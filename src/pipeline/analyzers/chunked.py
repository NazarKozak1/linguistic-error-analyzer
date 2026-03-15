"""
Architecture: Context-Aware Chunked Analyzer (Sentence-by-Sentence)
Description: Splits text into sentences. Runs parallel async requests for each sentence.
Passes the full original text as passive context to retain gender/timeline awareness.
Pros: Eliminates attention degradation, zero duplicates, high precision on mini-models.
Cons: Consumes more tokens (O(N^2) scaling for context).
"""
import os
import asyncio
import diff_match_patch as dmp_module
from dotenv import load_dotenv
from openai import AsyncOpenAI

from src.pipeline.schemas import SinglePassAnalysis
from src.pipeline.taxonomy import TAG_TO_CATEGORY

import nltk
from nltk.tokenize import sent_tokenize

load_dotenv()

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)
    nltk.download('punkt', quiet=True)


class ChunkedAnalyzer:
    def __init__(self, api_key: str | None = None, model: str = "gpt-5-mini"):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("api key is missing")
        self.client = AsyncOpenAI(api_key=key)
        self.model = model

    @staticmethod
    def _highlight_changes(original: str, corrected: str) -> str:
        # Highlight word-level diffs using Google's diff-match-patch
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
        """Silently capitalizes the first letter of the text and ensures end punctuation before tokenizing."""
        text = text.strip()
        if not text:
            return "", []

        # 1. Capitalize the very first letter of the entire text
        text = text[0].upper() + text[1:]

        # 2. Add a period at the end if punctuation is missing
        if text[-1] not in ['.', '!', '?', '"', "'", '»', '“', '”']:
            text += '.'

        # 3. Tokenize into sentences ONLY AFTER the full text is fixed
        sentences = sent_tokenize(text, language='german')

        return text, sentences


    async def _analyze_single_sentence(self, target_sentence: str, full_context: str, language) -> dict:
        """Analyzes a single sentence while using the full text as passive context."""

        system_prompt = f"""
        You are a strict CEFR German examiner. 
        
        CONTEXT: The user wrote a full text: "{full_context}". 
        Use this context ONLY to understand the user's gender (e.g., male names like Nazar), timeline (past/present), and pronouns.
        
        YOUR TASK: Analyze ONLY the TARGET SENTENCE. Ignore errors in the rest of the text.

        Strict Workflow for TARGET SENTENCE:
        1. Find ALL grammar, spelling, punctuation, AND TENSE errors.
        2. Document them in the `errors` array. Explanations in {language.value}.
        3. Generate the `corrected_text` for the target sentence.
        4. Generate `translation` for the target sentence STRICTLY in {language.value}. Do NOT output English unless English is explicitly requested.

        CRITICAL PRIORITIES:
        1. GRAMMAR & TENSE OVERRIDE EVERYTHING. Look at the CONTEXT timeline.
        2. ORTHOGRAPHY: Fix typos, capitalization, and punctuation.
        3. PRESERVE VALID STYLE: Do NOT change correct sentences to sound more formal.
        4. GIBBERISH RULE: If the target sentence is meaningless gibberish, just random punctuation (e.g. "? !"), or random letters (e.g. "aaaaa"), DO NOT invent meaning or add new words. Leave it exactly as it is and return empty errors array.
        - STRICT GENDER RULE: If context implies male, do NOT suggest female endings.
        """

        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[ # type: ignore
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"TARGET SENTENCE TO ANALYZE: {target_sentence}"}
            ],
            response_format=SinglePassAnalysis,
        )

        parsed = response.choices[0].message.parsed
        tokens = response.usage.total_tokens if response.usage else 0

        # Filter out hallucinations (duplicates are rare in single-sentence chunks)
        final_errors = []
        for err in parsed.errors:
            if err.error_fragment.strip() == err.correction.strip():
                continue
            err_dict = err.model_dump()
            err_dict['category'] = TAG_TO_CATEGORY.get(err.subcategory, "unknown")
            final_errors.append(err_dict)

        return {
            "corrected": parsed.corrected_text,
            "translation": parsed.translation,
            "errors": final_errors,
            "tokens": tokens
        }

    async def analyze(self, user_input: str, language) -> dict:
        """Main pipeline: splits text, runs async requests, and merges results."""

        # 1. Preprocess text (silent fixes: capital letter, trailing period) and split
        processed_input, sentences = self._preprocess_and_tokenize(user_input)

        # Return early if the input is empty or invalid
        if not sentences:
            return {
                "original": user_input,
                "corrected": user_input,
                "highlighted_text": user_input,
                "translation": "",
                "errors": [],
                "tokens": 0
            }

        # 2. Dispatch parallel async requests for each sentence
        # Pass 'processed_input' instead of 'user_input' so the LLM sees the clean context
        tasks = [self._analyze_single_sentence(sentence, processed_input, language) for sentence in sentences]
        chunk_results = await asyncio.gather(*tasks)

        # 3. Merge results
        final_corrected = " ".join([r['corrected'].strip() for r in chunk_results])
        final_translation = " ".join([r['translation'].strip() for r in chunk_results])

        total_errors = []
        for r in chunk_results:
            total_errors.extend(r['errors'])

        total_tokens = sum(r['tokens'] for r in chunk_results)

        # 4. Generate word-level diff highlight on the fully merged text
        # Compare against processed_input so our silent fixes aren't highlighted as AI corrections
        highlighted = self._highlight_changes(processed_input, final_corrected)

        return {
            "original": processed_input,  # Return the cleaned version
            "corrected": final_corrected,
            "highlighted_text": highlighted,
            "translation": final_translation,
            "errors": total_errors,
            "tokens": total_tokens
        }