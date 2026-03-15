"""
Architecture: Single-Pass Analyzer
Description: Analyzes the entire text in one API call.
Pros: Cheaper, faster.
Cons: Prone to LLM attention degradation (hallucinations, missed commas, duplicate errors) on longer texts using mini-models.
"""
import os
import pprint
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
import diff_match_patch as dmp_module

from src.utils.enums import OutputLanguage
from src.pipeline.schemas import SinglePassAnalysis
from src.pipeline.taxonomy import TAG_TO_CATEGORY

load_dotenv()

class SinglePassAnalyzer:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        """init async analyzer."""
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
        """Uses diff-match-patch but groups character changes into whole words."""
        dmp = dmp_module.diff_match_patch()
        diffs = dmp.diff_main(original, corrected)
        dmp.diff_cleanupSemantic(diffs)

        # 1. Розбираємо текст на літери і фіксуємо, чи була літера додана/змінена
        char_mods = []
        for op, data in diffs:
            if op == dmp.DIFF_INSERT:
                char_mods.extend([(c, True) for c in data])
            elif op == dmp.DIFF_EQUAL:
                char_mods.extend([(c, False) for c in data])

        # 2. Збираємо літери у слова. Якщо хоч одна літера змінилася — робимо все слово жирним
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
                result.append(char)  # зберігаємо оригінальні пробіли
            else:
                current_word += char
                if is_mod:
                    word_modified = True

        # Додаємо останнє слово
        if current_word:
            if word_modified:
                result.append(f"<b>{current_word}</b>")
            else:
                result.append(current_word)

        return "".join(result)

    async def analyze(self, user_input: str, language: OutputLanguage = OutputLanguage.UKRAINIAN) -> dict:
        """run analysis pipeline in a single pass."""
        system_prompt = f"""
                You are a strict CEFR German examiner. Analyze the user's German text in ONE SINGLE PASS.

                Strict Workflow:
                1. Find ALL grammar, spelling, punctuation, AND TENSE errors.
                2. Document them in the `errors` array. Explanations in {language.value}.
                3. Generate the `corrected_text` based exactly on the errors array.
                4. Generate `translation`.

                CRITICAL PRIORITIES (IN ORDER):
                1. GRAMMAR & TENSE OVERRIDE EVERYTHING: You MUST correct verbs that contradict time markers. "Ich kaufe ... gestern" is a FATAL ERROR. You MUST change it to Perfekt ("Ich habe ... gekauft"). 
                2. ORTHOGRAPHY: Fix typos, capitalization, and punctuation.
                3. PRESERVE VALID STYLE: If the sentence is grammatically correct (e.g., "war ich mit der Schule fertig"), DO NOT change it to sound more formal. Only fix actual errors.
                4. GIBBERISH RULE: If the target sentence is meaningless gibberish, just random punctuation (e.g. "? !"), or random letters (e.g. "aaaaa"), DO NOT invent meaning or add new words. Leave it exactly as it is and return empty errors array.
                
                - STRICT GENDER RULE: Always check the user's name or previous context for gender. If the user is male (Nazar), NEVER suggest female endings like 'Data Scientistin'.
                - NO PEDANTRY: If a sentence is natural and correct German (A1-B1 level), do not change it just to sound "more professional" unless the user specifically asks for a formal style.
                - NO DUPLICATES: Each error should be documented only once. Do not include the same error as both a single word and part of a sentence fragment.
                
                
                Example:
                User: "Ich bin fertig."
                Correct: Keep as is. Do NOT change to "Ich bin fertig geworden".
                Reason: It's grammatically correct and natural.
                """
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[  # type: ignore
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            response_format=SinglePassAnalysis,
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

        highlighted = self._highlight_changes(user_input, parsed.corrected_text)

        return {
            "original": user_input,
            "corrected": parsed.corrected_text,
            "highlighted_text": highlighted,
            "translation": parsed.translation,
            "errors": final_errors,
            "tokens": tokens
        }


async def main():
    """run test execution."""
    analyzer = SinglePassAnalyzer()
    test_sentence = "Ich kaufe ein Äpfel getern"

    try:
        result = await analyzer.analyze(test_sentence, language=OutputLanguage.UKRAINIAN)
        pprint.pprint(result)
    except Exception as e:
        print(f"error: {e}")


if __name__ == "__main__":
    asyncio.run(main())