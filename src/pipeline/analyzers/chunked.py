"""
Architecture: Context-Aware Chunked Analyzer (Two-Step Parallel)
Description: Splits text into sentences. Runs parallel async requests for each sentence.
Step 1: Fast translation & correction.
Step 2: Detailed error extraction (only if errors exist).
Pros: Eliminates attention degradation on long texts, perfect UX with loading spinner.
"""
import os
import asyncio
import diff_match_patch as dmp_module
from dotenv import load_dotenv
from openai import AsyncOpenAI
import nltk
from nltk.tokenize import sent_tokenize

from src.pipeline.schemas import FastCorrection, DetailedErrors
from src.pipeline.taxonomy import TAG_TO_CATEGORY
from src.utils.enums import OutputLanguage

load_dotenv()

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)
    nltk.download('punkt', quiet=True)


class ChunkedAnalyzer:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("api key is missing")
        self.client = AsyncOpenAI(api_key=key)
        self.model = model
        self.temperature = 1.0 if "5" in model else 0.0

    @staticmethod
    def _highlight_changes(original: str, corrected: str) -> str:
        dmp = dmp_module.diff_match_patch()
        diffs = dmp.diff_main(original, corrected)
        dmp.diff_cleanupSemantic(diffs)

        char_mods = []
        for op, data in diffs:
            if op == dmp.DIFF_INSERT:
                char_mods.extend([(c, True) for c in data])
            elif op == dmp.DIFF_EQUAL:
                char_mods.extend([(c, False) for c in data])

        result = []
        current_word = ""
        word_modified = False

        for char, is_mod in char_mods:
            if char.isspace():
                if current_word:
                    result.append(f"<b>{current_word}</b>" if word_modified else current_word)
                    current_word = ""
                    word_modified = False
                result.append(char)
            else:
                current_word += char
                if is_mod:
                    word_modified = True

        if current_word:
            result.append(f"<b>{current_word}</b>" if word_modified else current_word)

        return "".join(result)

    @staticmethod
    def _preprocess_and_tokenize(text: str) -> tuple[str, list[str]]:
        text = text.strip()
        if not text:
            return "", []

        text = text[0].upper() + text[1:]
        if text[-1] not in ['.', '!', '?', '"', "'", '»', '“', '”']:
            text += '.'

        sentences = sent_tokenize(text, language='german')
        return text, sentences

    # step 1: fast correction
    async def _get_fast_correction_chunk(self, target_sentence: str, full_context: str, language: OutputLanguage) -> dict:
        """Translates and corrects a single sentence."""
        system_prompt = f"""
        You are a strict CEFR German examiner. 
        CONTEXT: "{full_context}" (Use for gender/timeline awareness).
        
        YOUR TASK: Fix the TARGET SENTENCE. 
        If there are grammar, spelling, or tense errors, fix them. 
        If it's gibberish, leave as is and set has_errors to False.
        Provide the corrected sentence and translation into {language.value}.
        """
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[ # type: ignore
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"TARGET SENTENCE: {target_sentence}"}
            ],
            response_format=FastCorrection,
            temperature=self.temperature
        )
        parsed = response.choices[0].message.parsed
        return {
            "corrected": parsed.corrected_text,
            "translation": parsed.translation,
            "has_errors": parsed.has_errors,
            "tokens": response.usage.total_tokens if response.usage else 0
        }

    async def get_fast_correction(self, user_input: str, language: OutputLanguage) -> dict:
        processed_input, sentences = self._preprocess_and_tokenize(user_input)

        if not sentences:
            return {
                "original": user_input, "corrected": user_input, "highlighted_text": user_input,
                "translation": "", "has_errors": False, "tokens": 0
            }

        tasks = [self._get_fast_correction_chunk(s, processed_input, language) for s in sentences]
        chunk_results = await asyncio.gather(*tasks)

        final_corrected = " ".join([r['corrected'].strip() for r in chunk_results])
        final_translation = " ".join([r['translation'].strip() for r in chunk_results])
        any_errors = any(r['has_errors'] for r in chunk_results)
        total_tokens = sum(r['tokens'] for r in chunk_results)

        highlighted = self._highlight_changes(processed_input, final_corrected)

        return {
            "original": processed_input,
            "corrected": final_corrected,
            "highlighted_text": highlighted,
            "translation": final_translation,
            "has_errors": any_errors,
            "tokens": total_tokens
        }

    # step 2: detailed errors
    async def _get_detailed_errors_chunk(self, target_sentence: str, full_original: str, full_corrected: str, language: OutputLanguage) -> dict:
        """Extracts errors for a single sentence by comparing it to the full corrected text."""
        system_prompt = f"""
        You are a strict CEFR German examiner.
        FULL ORIGINAL: "{full_original}"
        FULL CORRECTED: "{full_corrected}"
        
        YOUR TASK: Extract and explain the errors specifically found in this TARGET SENTENCE: "{target_sentence}".
        Provide short explanations in {language.value}.
        """
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[ # type: ignore
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Find errors for this sentence: {target_sentence}"}
            ],
            response_format=DetailedErrors,
            temperature=self.temperature
        )
        parsed = response.choices[0].message.parsed

        final_errors = []
        for err in parsed.errors:
            if err.error_fragment.strip() != err.correction.strip():
                err_dict = err.model_dump()
                err_dict['category'] = TAG_TO_CATEGORY.get(err.subcategory, "unknown")
                final_errors.append(err_dict)

        return {
            "errors": final_errors,
            "tokens": response.usage.total_tokens if response.usage else 0
        }

    async def get_detailed_errors(self, user_input: str, corrected_text: str, language: OutputLanguage) -> dict:
        processed_input, sentences = self._preprocess_and_tokenize(user_input)

        tasks = [self._get_detailed_errors_chunk(s, processed_input, corrected_text, language) for s in sentences]
        chunk_results = await asyncio.gather(*tasks)

        total_errors = []
        for r in chunk_results:
            total_errors.extend(r['errors'])

        total_tokens = sum(r['tokens'] for r in chunk_results)

        return {
            "errors": total_errors,
            "tokens": total_tokens
        }