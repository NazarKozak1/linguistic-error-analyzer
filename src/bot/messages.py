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
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest, TelegramAPIError

from html import escape
import asyncio
import contextlib

logger = get_logger(__name__)
router = Router()

single_pass_analyzer = SinglePassAnalyzer(model="gpt-5-mini")
chunked_analyzer = ChunkedAnalyzer(model="gpt-5-mini")

# Map short language codes from DB to the Enum expected by OpenAI
LANG_MAPPING = {
    "uk": OutputLanguage.UKRAINIAN,
    "en": OutputLanguage.ENGLISH,
    "de": OutputLanguage.GERMAN,
    "ru": OutputLanguage.RUSSIAN
}


async def run_loading_spinner(message: types.Message, base_text: str, loading_text: str):
    """Loading animation"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    while True:
        try:
            frame = frames[idx % len(frames)]
            animated_text = f"{base_text}\n\n{frame} {loading_text}..."
            await message.edit_text(animated_text, parse_mode="HTML")
            idx += 1
            await asyncio.sleep(1.0)  # Prevent Telegram API flood limits
        except asyncio.CancelledError:
            # Task was cancelled externally, exit loop cleanly
            break
        except TelegramRetryAfter as e:
            # Telegram asks us to wait before making more requests (Flood control)
            await asyncio.sleep(e.retry_after)
        except TelegramBadRequest:
            # Happens if we try to edit message with the exact same text
            # or if the message was deleted by the user
            await asyncio.sleep(1.0)
        except TelegramAPIError:
            # General network or Telegram server issues
            await asyncio.sleep(1.0)


@router.message(F.text & ~F.text.startswith('/'))
async def process_sentence(message: types.Message, db_user: User, db_session: AsyncSession):
    user_lang = db_user.preferred_language or "en"

    clean_text = message.text.strip()
    if clean_text:
        # Capitalize first letter
        clean_text = clean_text[0].upper() + clean_text[1:]
        # Add period at the end if needed
        if clean_text[-1] not in ['.', '!', '?', '"', "'", '»', '“', '”']:
            clean_text += '.'

    # Validate input language
    if not is_german(clean_text):
        await message.answer(get_text(user_lang, "not_german"))
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action='typing')
    logger.info(f"Received text from user_id={message.from_user.id}")

    spinner_task = None  # Prevent task leak on exception

    try:
        lang_enum = LANG_MAPPING.get(user_lang, OutputLanguage.ENGLISH)

        sentences = sent_tokenize(clean_text, language='german')

        if len(sentences) <= 2 or db_user.role == UserRole.REGULAR:
            analyzer = single_pass_analyzer
        else:
            analyzer = chunked_analyzer

        # Fetch localized UI texts
        lbl_orig = get_text(user_lang, "original")
        lbl_corr = get_text(user_lang, "corrected")
        lbl_trans = get_text(user_lang, "translated")
        lbl_errs = get_text(user_lang, "errors_title")
        lbl_perfect = get_text(user_lang, "no_errors")
        lbl_loading = get_text(user_lang, "loading_errors")
        lbl_analyzing = get_text(user_lang, "analyzing")

        # Step 1: Immediate response & First Spinner
        base_step_1 = f"<b>{lbl_orig}</b> <pre>{escape(message.text)}</pre>"
        sent_message = await message.answer(base_step_1, parse_mode="HTML")

        spinner_task = asyncio.create_task(
            run_loading_spinner(sent_message, base_step_1, lbl_analyzing)
        )

        # Fast API call for correction and translation
        fast_result = await analyzer.get_fast_correction(clean_text, lang_enum)

        # Stop first spinner cleanly
        spinner_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await spinner_task

        # Update user usage limits
        db_user.daily_requests += 1
        db_user.daily_tokens += fast_result.get("tokens", 0)

        # Handle case with no errors
        if not fast_result.get("has_errors"):
            final_no_errors = base_step_1 + f"\n\n<b>{lbl_trans}</b> <pre>{escape(fast_result['translation'])}</pre>\n\n✅ {lbl_perfect}\n"

            await sent_message.edit_text(final_no_errors, parse_mode="HTML")

            await save_sentence_with_errors(
                session=db_session,
                user_id=db_user.id,
                telegram_message_id=message.message_id,
                original_text=fast_result["original"],
                corrected_text=fast_result["corrected"],
                translation=fast_result["translation"],
                tokens_used=fast_result.get("tokens", 0),
                errors_data=[]
            )
            return

        # Step 2: Intermediate response & Second Spinner
        base_step_2 = base_step_1 + f"\n<b>{lbl_corr}</b> <pre>{fast_result['highlighted_text']}</pre>\n"
        base_step_2 += f"<b>{lbl_trans}</b> <pre>{escape(fast_result['translation'])}</pre>"

        spinner_task = asyncio.create_task(
            run_loading_spinner(sent_message, base_step_2, lbl_loading)
        )

        # Detailed API call for error explanations
        errors_result = await analyzer.get_detailed_errors(
            clean_text,
            fast_result["corrected"],
            lang_enum
        )

        # Stop second spinner cleanly
        spinner_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await spinner_task

        db_user.daily_tokens += errors_result.get("tokens", 0)

        # Step 3: Finalize response formatting
        final_response = base_step_2 + f"\n\n<b>{lbl_errs}</b>\n"
        errors_list = errors_result.get("errors", [])

        for i, err in enumerate(errors_list, 1):
            frag = escape(err.get('error_fragment', ''))
            corr = escape(err.get('correction', ''))
            expl = escape(err.get('explanation', ''))

            final_response += (
                f"{i}. <s>{frag}</s> -> <b>{corr}</b>\n"
                f"<i>{expl}</i>\n\n"
            )

        # Push final update to Telegram
        await sent_message.edit_text(final_response, parse_mode="HTML")

        # Save complete record to DB
        total_tokens = fast_result.get("tokens", 0) + errors_result.get("tokens", 0)
        await save_sentence_with_errors(
            session=db_session,
            user_id=db_user.id,
            telegram_message_id=message.message_id,
            original_text=fast_result["original"],
            corrected_text=fast_result["corrected"],
            translation=fast_result["translation"],
            tokens_used=total_tokens,
            errors_data=errors_list
        )
        logger.info(f"Analysis completed and saved for user_id={db_user.id}")

    except Exception as e:
        # Clean up the background task cleanly if something crashes
        if spinner_task and not spinner_task.done():
            spinner_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await spinner_task

        logger.error(f"Analysis failed for user_id={db_user.id}: {e}", exc_info=True)
        await message.answer(get_text(user_lang, "analysis_error"))