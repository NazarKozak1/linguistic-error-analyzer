from aiogram import Router, F, types
from sqlalchemy.ext.asyncio import AsyncSession
from nltk.tokenize import sent_tokenize

from src.db.models import User, UserRole
from src.db.crud import save_sentence_with_errors
from src.utils.enums import OutputLanguage
from src.utils.logger import get_logger
from src.utils.validators import is_german
from src.utils.texts import get_text

from src.pipeline.analyzers.single_pass import SinglePassAnalyzer
from src.pipeline.analyzers.chunked import ChunkedAnalyzer

from html import escape

logger = get_logger(__name__)
router = Router()

single_pass_analyzer = SinglePassAnalyzer(model="gpt-5-mini")
chunked_analyzer = ChunkedAnalyzer(model="gpt-5-mini")

# map short language codes from DB to the Enum expected by OpenAI
LANG_MAPPING = {
    "uk": OutputLanguage.UKRAINIAN,
    "en": OutputLanguage.ENGLISH,
    "de": OutputLanguage.GERMAN,
    "ru": OutputLanguage.RUSSIAN
}


@router.message(F.text & ~F.text.startswith('/'))
async def process_sentence(message: types.Message, db_user: User, db_session: AsyncSession):
    user_lang = db_user.preferred_language or "en"

    if not is_german(message.text):
        await message.answer(get_text(user_lang, "not_german"))
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action='typing')
    logger.info(f"Received text from user_id={message.from_user.id}")

    try:
        lang_enum = LANG_MAPPING.get(user_lang, OutputLanguage.ENGLISH)
        logger.info(f"Starting analysis for user_id={db_user.id}, lang={lang_enum.name}")

        sentences = sent_tokenize(message.text.strip(), language='german')

        if len(sentences) <= 2 or db_user.role == UserRole.REGULAR:
            analyzer = single_pass_analyzer
        else:
            analyzer = chunked_analyzer

        result = await analyzer.analyze(
            user_input=message.text,
            language=lang_enum
        )

        db_user.daily_requests += 1
        db_user.daily_tokens += result.get("tokens", 0)

        await save_sentence_with_errors(
            session=db_session,
            user_id=db_user.id,
            telegram_message_id=message.message_id,
            original_text=result["original"],
            corrected_text=result["corrected"],
            translation=result["translation"],
            tokens_used=result.get("tokens", 0),
            errors_data=result["errors"]
        )
        logger.info(f"Saved analysis for user_id={db_user.id}")

        errors_list = result.get("errors", [])

        # fetch localized headers
        lbl_orig = get_text(user_lang, "original")
        lbl_corr = get_text(user_lang, "corrected")
        lbl_trans = get_text(user_lang, "translated")
        lbl_errs = get_text(user_lang, "errors_title")
        lbl_perfect = get_text(user_lang, "no_errors")

        # Build response with escaped user content
        # result['highlighted_text'] should NOT be escaped entirely because it contains OUR <b> tags,
        # but the original text and translations MUST be escaped.

        response = f"<b>{lbl_orig}</b> <pre>{escape(result['original'])}</pre>\n"

        if errors_list:
            # highlighted_text already contains <b> tags from our _highlight_changes method
            response += f"<b>{lbl_corr}</b> <pre>{result['highlighted_text']}</pre>\n"
            response += f"<b>{lbl_trans}</b> <pre>{escape(result['translation'])}</pre>\n\n"
            response += f"<b>{lbl_errs}</b>\n"

            for i, err in enumerate(errors_list, 1):
                # Escape fragments and explanations to be safe
                frag = escape(err.get('error_fragment', ''))
                corr = escape(err.get('correction', ''))
                expl = escape(err.get('explanation', ''))

                response += (
                    f"{i}. <s>{frag}</s> -> <b>{corr}</b>\n"
                    f"<i>{expl}</i>\n\n"
                )
        else:
            response += f"<b>{lbl_trans}</b> <pre>{escape(result['translation'])}</pre>\n\n"
            response += f"✅ {lbl_perfect}\n"

        await message.answer(response)
        logger.info(f"Response sent to user_id={db_user.id}")

    except Exception as e:
        logger.error(f"Analysis failed for user_id={db_user.id}: {e}", exc_info=True)
        await message.answer(get_text(user_lang, "analysis_error"))