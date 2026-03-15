import os
import pprint
import asyncio
from enum import Enum
from typing import List, Literal
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
import diff_match_patch as dmp_module

# --- 1. TAXONOMY ---
TAG_TO_CATEGORY = {
    "caps": "1_orthography", "umlauts": "1_orthography", "vowel_length": "1_orthography",
    "punctuation": "1_orthography", "spacing": "1_orthography", "spelling": "1_orthography",
    "comma_usage": "1_orthography",
    "case_nominative": "2_morphology", "case_akkusativ": "2_morphology", "case_dativ": "2_morphology",
    "case_genitive": "2_morphology", "gender_mismatch": "2_morphology", "plural_formation": "2_morphology",
    "adj_declension_weak": "2_morphology", "adj_declension_strong": "2_morphology",
    "verb_conjugation_regular": "2_morphology",
    "verb_conjugation_irregular": "2_morphology", "tense_praesens": "2_morphology", "tense_perfekt": "2_morphology",
    "tense_praeteritum": "2_morphology", "tense_futur": "2_morphology", "pronoun_personal": "2_morphology",
    "pronoun_possessive": "2_morphology", "pronoun_reflexive": "2_morphology", "article_error": "2_morphology",
    "v2_position": "3_syntax", "subordinate_pos": "3_syntax", "agreement": "3_syntax",
    "prep_constructions": "3_syntax", "modal_infinitives": "3_syntax", "sentence_fragments": "3_syntax",
    "question_order": "3_syntax", "negation": "3_syntax", "separable_prefix": "3_syntax",
    "word_order_general": "3_syntax",
    "word_choice": "4_lexicon", "overgeneralization": "4_lexicon", "basic_vocab": "4_lexicon",
    "false_friends": "4_lexicon", "collocations": "4_lexicon",
    "politeness": "5_pragmatics", "literal_translation": "5_pragmatics", "register": "5_pragmatics",
    "contextual_inference": "5_pragmatics"
}

ERRORS_DESCRIPTION = "Error category tag (e.g. spelling, comma_usage, word_choice, word_order_general, etc.)"


# --- 2. SCHEMAS (БЕЗ HTML-тегів) ---
class ErrorDetail(BaseModel):
    error_fragment: str = Field(description="The fragment from the original sentence containing the error.")
    correction: str = Field(description="The corrected version of the fragment.")
    subcategory: Literal[
        "caps", "umlauts", "vowel_length", "punctuation", "spacing", "spelling", "comma_usage",
        "case_nominative", "case_akkusativ", "case_dativ", "case_genitive", "gender_mismatch",
        "plural_formation", "adj_declension_weak", "adj_declension_strong", "verb_conjugation_regular",
        "verb_conjugation_irregular", "tense_praesens", "tense_perfekt", "tense_praeteritum",
        "tense_futur", "pronoun_personal", "pronoun_possessive", "pronoun_reflexive", "article_error",
        "v2_position", "subordinate_pos", "agreement", "prep_constructions", "modal_infinitives",
        "sentence_fragments", "question_order", "negation", "separable_prefix", "word_order_general",
        "word_choice", "overgeneralization", "basic_vocab", "false_friends", "collocations",
        "politeness", "literal_translation", "register", "contextual_inference"
    ] = Field(description=ERRORS_DESCRIPTION)
    cefr_level: Literal["A1.1", "A1.2", "A2.1", "A2.2", "B1.1", "B1.2", "B2.1", "B2.2", "C1.1", "C1.2", "C2.1", "C2.2"]
    explanation: str = Field(description="Short explanation why this is an error.")


class SinglePassAnalysis(BaseModel):
    has_errors: bool = Field(description="True if errors are found.")
    errors: List[ErrorDetail] = Field(
        description="List of detected errors. MUST be generated BEFORE the corrected texts.")
    corrected_text: str = Field(description="The clean corrected German sentence. ABSOLUTELY NO HTML TAGS HERE.")
    translation: str = Field(description="Translation of the corrected sentence into the requested language.")


# --- 3. HELPER: ALGORITHMIC DIFFING ---
def highlight_changes(original: str, corrected: str) -> str:
    """Uses Google's diff-match-patch to highlight insertions and replacements."""
    dmp = dmp_module.diff_match_patch()
    diffs = dmp.diff_main(original, corrected)
    dmp.diff_cleanupSemantic(diffs)

    result_html = ""
    for op, data in diffs:
        if op == dmp.DIFF_INSERT:
            result_html += f"<b>{data}</b>"
        elif op == dmp.DIFF_EQUAL:
            result_html += data
        # DIFF_DELETE ігноруємо, бо нам треба тільки фінальний вигляд
    return result_html


# --- 4. ANALYZER CLASS ---
class OutputLanguage(Enum):
    UKRAINIAN = "Ukrainian"
    GERMAN = "German"
    ENGLISH = "English"
    RUSSIAN = "Russian"


class TestSinglePassAnalyzer:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        load_dotenv()
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("api key is missing")
        self.client = AsyncOpenAI(api_key=key)
        self.model = model

    async def analyze(self, user_input: str, language: OutputLanguage = OutputLanguage.UKRAINIAN) -> dict:
        system_prompt = f"""
        You are an expert CEFR German examiner and teacher. 
        Analyze the user's German text in ONE SINGLE PASS.

        Strict Workflow:
        1. FIRST, find all actual grammar, spelling, punctuation or serious lexical errors.
        2. Document them in the `errors` array. Write explanations in {language.value}.
        3. ONLY AFTER creating the errors array, generate the `corrected_text`. 
        4. Every change in `corrected_text` MUST have a corresponding entry in the `errors` array.
        5. Generate `translation`.

        Critical Rules:
        - Focus ONLY on true errors. DO NOT alter conversational but grammatically correct phrasing (e.g., 'war ich mit der Schule fertig' is correct, DO NOT change it to 'habe ich die Schule abgeschlossen').
        - Never hallucinate extra auxiliary verbs.
        - If the sentence is perfect, `has_errors` is false, `errors` is empty, and `corrected_text` matches original.
        """

        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            response_format=SinglePassAnalysis,
            temperature=0.0
        )

        parsed = response.choices[0].message.parsed
        tokens = response.usage.total_tokens if response.usage else 0

        # Збагачуємо категоріями та фільтруємо галюцинації "самовиправлення"
        final_errors = []
        for err in parsed.errors:
            if err.error_fragment.strip() == err.correction.strip():
                continue
            err_dict = err.model_dump()
            err_dict['category'] = TAG_TO_CATEGORY.get(err.subcategory, "unknown")
            final_errors.append(err_dict)

        # Генеруємо HTML-підсвітку локально, без LLM
        highlighted = highlight_changes(user_input, parsed.corrected_text)

        return {
            "original": user_input,
            "corrected": parsed.corrected_text,
            "highlighted_text": highlighted,
            "translation": parsed.translation,
            "errors": final_errors,
            "tokens": tokens
        }


# --- 5. TEST EXECUTION ---
async def main():
    analyzer = TestSinglePassAnalyzer()

    test_text = "Ich heiße Nazar Kozak und bin 2003 in der Ukraine geboren. 2020 war ich mit der Schule fertig. Von 2020 bis 2024 habe ich meinen Bachelor gemacht. Von 2024 bis 2025 habe ich meinen Master gemacht. Also, ich habe von 2023 bis 2025 als Python Entwikler gearbeitet. Und ich habe von April 2025 bis Oktober 2025 als Datenwissenschaftler gearbeitet. Aber, jetzt habe ich keine Arbeit. Später will ich eine Stelle als Datenwissenschaftler finden."

    print("🚀 Запускаємо тест...\n")

    for i in range(1, 4):
        print(f"--- Ітерація {i} ---")
        try:
            result = await analyzer.analyze(test_text, language=OutputLanguage.UKRAINIAN)

            print(f"Corrected: {result['corrected']}")
            print(f"Highlighted: {result['highlighted_text']}")
            print("Errors list length:", len(result['errors']))
            for idx, err in enumerate(result['errors'], 1):
                print(f"  {idx}. {err['error_fragment']} -> {err['correction']} ({err['subcategory']})")
            print("-" * 40 + "\n")

        except Exception as e:
            print(f"Помилка: {e}")


if __name__ == "__main__":
    asyncio.run(main())