from pydantic import BaseModel, Field
from typing import List, Literal
from src.pipeline.taxonomy import ERRORS_DESCRIPTION

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
    errors: List[ErrorDetail] = Field(description="List of detected errors. MUST be generated BEFORE the corrected texts.")
    corrected_text: str = Field(description="The clean corrected German sentence. ABSOLUTELY NO HTML TAGS HERE.")
    translation: str = Field(description="Translation of the corrected sentence into the requested language.")