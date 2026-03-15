# src/pipeline/taxonomy.py
"""
German errors mapping
"""
TAG_TO_CATEGORY = {
    # orthography
    "caps": "1_orthography", "umlauts": "1_orthography", "vowel_length": "1_orthography",
    "punctuation": "1_orthography", "spacing": "1_orthography", "spelling": "1_orthography", "comma_usage": "1_orthography",
    # morphology
    "case_nominative": "2_morphology", "case_akkusativ": "2_morphology", "case_dativ": "2_morphology",
    "case_genitive": "2_morphology", "gender_mismatch": "2_morphology", "plural_formation": "2_morphology",
    "adj_declension_weak": "2_morphology", "adj_declension_strong": "2_morphology", "verb_conjugation_regular": "2_morphology",
    "verb_conjugation_irregular": "2_morphology", "tense_praesens": "2_morphology", "tense_perfekt": "2_morphology",
    "tense_praeteritum": "2_morphology", "tense_futur": "2_morphology", "pronoun_personal": "2_morphology",
    "pronoun_possessive": "2_morphology", "pronoun_reflexive": "2_morphology", "article_error": "2_morphology",
    # syntax
    "v2_position": "3_syntax", "subordinate_pos": "3_syntax", "agreement": "3_syntax",
    "prep_constructions": "3_syntax", "modal_infinitives": "3_syntax", "sentence_fragments": "3_syntax",
    "question_order": "3_syntax", "negation": "3_syntax", "separable_prefix": "3_syntax", "word_order_general": "3_syntax",
    # lexicon
    "word_choice": "4_lexicon", "overgeneralization": "4_lexicon", "basic_vocab": "4_lexicon",
    "false_friends": "4_lexicon", "collocations": "4_lexicon",
    # pragmatics
    "politeness": "5_pragmatics", "literal_translation": "5_pragmatics", "register": "5_pragmatics", "contextual_inference": "5_pragmatics"
}


ERRORS_DESCRIPTION = """
    Error category tag.

    caps – capitalization
    umlauts – ä/ö/ü error
    vowel_length – long/short vowel spelling
    punctuation – punctuation mark
    spacing – missing/extra space
    spelling – word spelling
    comma_usage – comma rule

    case_nominative – nominative case
    case_akkusativ – accusative case
    case_dativ – dative case
    case_genitive – genitive case
    gender_mismatch – wrong noun gender
    plural_formation – plural form

    adj_declension_weak – weak adjective ending
    adj_declension_strong – strong adjective ending

    verb_conjugation_regular – regular verb form
    verb_conjugation_irregular – irregular verb form

    tense_praesens – present tense
    tense_perfekt – Perfekt tense
    tense_praeteritum – Präteritum tense
    tense_futur – future tense

    pronoun_personal – personal pronoun
    pronoun_possessive – possessive pronoun
    pronoun_reflexive – reflexive pronoun

    article_error – wrong article

    v2_position – verb second rule
    subordinate_pos – verb final clause
    agreement – subject–verb agreement
    prep_constructions – preposition usage
    modal_infinitives – modal + infinitive

    sentence_fragments – incomplete sentence
    question_order – question word order
    negation – nicht/kein usage
    separable_prefix – separable verb

    word_order_general – general word order

    word_choice – wrong word choice
    overgeneralization – grammar overgeneralized
    basic_vocab – basic vocabulary error
    false_friends – misleading translation
    collocations – unnatural word combination

    politeness – politeness form
    literal_translation – direct translation
    register – formal/informal mismatch
    contextual_inference – context meaning error
    """