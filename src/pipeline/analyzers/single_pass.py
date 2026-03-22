"""
Architecture: Single-Pass Analyzer
Description: Analyzes the entire text in one API call.
Pros: Cheaper, faster.
Cons: Prone to LLM attention degradation (hallucinations, missed commas, duplicate errors) on longer texts using mini-models.
"""
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
import diff_match_patch as dmp_module

from src.utils.enums import OutputLanguage
from src.pipeline.taxonomy import TAG_TO_CATEGORY
from src.pipeline.schemas import FastCorrection, DetailedErrors

load_dotenv()

class SinglePassAnalyzer:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        """Init async analyzer."""
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("api key is missing")

        self.temperature = 1
        if model == "gpt-4o-mini":
            self.temperature = 0.

        self.client = AsyncOpenAI(api_key=key)
        self.model = model

    @staticmethod
    def _highlight_changes(original: str, corrected: str) -> str:
        """Uses diff-match-patch to highlight character changes grouped by whole words."""
        dmp = dmp_module.diff_match_patch()
        diffs = dmp.diff_main(original, corrected)
        dmp.diff_cleanupSemantic(diffs)

        # Track inserted/modified characters
        char_mods = []
        for op, data in diffs:
            if op == dmp.DIFF_INSERT:
                char_mods.extend([(c, True) for c in data])
            elif op == dmp.DIFF_EQUAL:
                char_mods.extend([(c, False) for c in data])

        # Group characters into words; bold the entire word if modified
        result = []
        current_word = ""
        word_modified = False

        for char, is_mod in char_mods:
            if char.isspace():
                if current_word:
                    if word_modified:
                        result.append(f"<b>{current_word}</b>")
                    else:
                        result.append(current_word)
                    current_word = ""
                    word_modified = False
                result.append(char)  # Preserve original spaces
            else:
                current_word += char
                if is_mod:
                    word_modified = True

        # Append the final word
        if current_word:
            if word_modified:
                result.append(f"<b>{current_word}</b>")
            else:
                result.append(current_word)

        return "".join(result)

    async def get_fast_correction(self, user_input: str, language: OutputLanguage) -> dict:
        """Step 1: Fast correction and translation."""
        system_prompt = f"""
        You are a strict CEFR German examiner.
        Analyze the user's text. If there are grammar, spelling, or tense errors, fix them. 
        If the text is gibberish or random punctuation, leave it as is and set has_errors to False.
        Provide the corrected text and its translation into {language.value}.
        Do NOT explain the errors yet.
        """
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[ # type: ignore
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            response_format=FastCorrection,
            temperature=self.temperature
        )

        parsed = response.choices[0].message.parsed
        tokens = response.usage.total_tokens if response.usage else 0
        highlighted = self._highlight_changes(user_input, parsed.corrected_text)

        return {
            "original": user_input,
            "corrected": parsed.corrected_text,
            "highlighted_text": highlighted,
            "translation": parsed.translation,
            "has_errors": parsed.has_errors,
            "tokens": tokens
        }

    async def get_detailed_errors(self, user_input: str, corrected_text: str, language: OutputLanguage) -> dict:
        """Step 2: Detailed error extraction (called only if errors exist)."""
        system_prompt = f"""
        You are a strict CEFR German examiner.
        The user wrote: "{user_input}"
        The corrected version is: "{corrected_text}"

        Compare them and extract the errors. 
        Provide short, clear explanations for each error in {language.value}.
        """
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[ # type: ignore
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Find errors between: '{user_input}' -> '{corrected_text}'"}
            ],
            response_format=DetailedErrors,
            temperature=self.temperature
        )

        parsed = response.choices[0].message.parsed
        tokens = response.usage.total_tokens if response.usage else 0

        final_errors = []
        for err in parsed.errors:
            if err.error_fragment.strip() == err.correction.strip():
                continue
            err_dict = err.model_dump()
            err_dict['category'] = TAG_TO_CATEGORY.get(err.subcategory, "unknown")
            final_errors.append(err_dict)

        return {
            "errors": final_errors,
            "tokens": tokens
        }