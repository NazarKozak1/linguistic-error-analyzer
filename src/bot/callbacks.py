from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from src.bot.states import OnboardingSteps
from src.db.database import AsyncSessionLocal
from src.db.crud import update_user_language
from src.utils.logger import get_logger
from src.utils.texts import get_text
from src.db.models import User
from sqlalchemy.ext.asyncio import AsyncSession


from aiogram.types import BotCommand, BotCommandScopeChat

logger = get_logger(__name__)
router = Router()


@router.callback_query(OnboardingSteps.choose_language, F.data.startswith("lang_"))
async def process_language(callback: types.CallbackQuery, state: FSMContext):
    """save language and finish onboarding or standalone setting change."""
    selected_lang = callback.data.split("_")[1]

    async with AsyncSessionLocal() as session:
        await update_user_language(session, callback.from_user.id, selected_lang)

    # completely clear state as there are no more onboarding steps
    await state.clear()

    # get localized success message using the newly selected language
    success_text = get_text(selected_lang, "lang_saved")

    await callback.message.edit_text(success_text)
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: types.CallbackQuery, db_user: User, db_session: AsyncSession):
    # 1. Отримуємо короткий код мови з callback_data (наприклад, "uk" з "lang_uk")
    new_lang = callback.data.split("_")[1]

    # 2. Оновлюємо мову в базі даних
    db_user.preferred_language = new_lang
    await db_session.commit()

    # 3. Оновлюємо кнопку "Menu" персонально для цього користувача
    try:
        await callback.bot.set_my_commands(
            commands=[
                BotCommand(
                    command="change_output_language",
                    description=get_text(new_lang, "cmd_change_lang_desc")
                )
            ],
            scope=BotCommandScopeChat(chat_id=callback.from_user.id)
        )
    except Exception as e:
        # Логуємо помилку, якщо Telegram API тимчасово недоступне, але не ламаємо логіку
        print(f"Failed to update menu for user {callback.from_user.id}: {e}")

    # 4. Видаляємо повідомлення з клавіатурою (опціонально, щоб не засмічувати чат)
    await callback.message.delete()

    # 5. Надсилаємо локалізоване підтвердження
    success_text = get_text(new_lang, "lang_saved")
    await callback.message.answer(success_text)

    # 6. Закриваємо callback (щоб годинник на кнопці перестав крутитися)
    await callback.answer()