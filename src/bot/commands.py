from aiogram import Router, types, Bot
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.bot.states import OnboardingSteps
from src.bot.keyboards import get_language_kb
from src.db.database import AsyncSessionLocal
from src.db.crud import get_or_create_user

from src.utils.texts import get_text, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User, UserRole

import asyncio
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats
from src.utils.logger import get_logger
from src.bot.config import BOT_STATE


logger = get_logger(__name__)
router = Router()


@router.message(StateFilter(OnboardingSteps.choose_language))
async def require_language_choice(message: types.Message):
    """Catch ANY input (commands, text, media) while in choose_language state."""

    tg_lang = message.from_user.language_code
    fallback_lang = tg_lang if tg_lang in SUPPORTED_LANGUAGES else "en"

    warning_text = get_text(fallback_lang, "require_language_selection")

    await message.answer(
        warning_text,
        reply_markup=get_language_kb()
    )


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """handle /start, check if user exists, route to onboarding or welcome back."""

    # extract telegram language code to use for the very first interaction
    tg_lang = message.from_user.language_code
    fallback_lang = tg_lang if tg_lang in SUPPORTED_LANGUAGES else "en"

    async with AsyncSessionLocal() as session:
        user, is_new = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            language_code=tg_lang
        )

    if not is_new:
        # existing user: fetch their saved preferred language
        user_lang = user.preferred_language if user.preferred_language in SUPPORTED_LANGUAGES else "en"

        # get localized text and format it with user's name
        welcome_back_text = get_text(user_lang, "welcome_back").format(name=user.first_name)

        await message.answer(welcome_back_text)
        return

    # new user: start fsm onboarding
    await state.set_state(OnboardingSteps.choose_language)

    # get localized onboarding text based on their telegram client language
    welcome_new_text = get_text(fallback_lang, "welcome_new")

    await message.answer(
        welcome_new_text,
        reply_markup=get_language_kb()
    )


@router.message(Command("language"))
async def cmd_change_language(message: types.Message, state: FSMContext):
    # Fetch user without creating a new record
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        # Ignore command if user is not found in the database
        if not user:
            return

        user_lang = user.preferred_language if user.preferred_language in SUPPORTED_LANGUAGES else "en"

    await state.set_state(OnboardingSteps.choose_language)
    await state.update_data(standalone=True)

    prompt_text = get_text(user_lang, "choose_new_language")

    await message.answer(
        prompt_text,
        reply_markup=get_language_kb()
    )




@router.message(Command("set_role"))
async def cmd_set_role(message: types.Message, db_user: User, db_session: AsyncSession, bot: Bot):
    # Only users with OWNER role can execute this command
    if db_user.role != UserRole.OWNER:
        return

    # Expected format: /set_role <id/@username> <ROLE>
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Usage: /set_role <telegram_id/@username> <REGULAR/ADMIN/OWNER>")
        return

    target_id_raw = args[1]
    role_name = args[2].upper()

    # Validate the existence of the requested role
    try:
        new_role = UserRole[role_name]
    except KeyError:
        return await message.answer(f"Invalid role. Use: REGULAR, ADMIN, or OWNER")

    # Locate the target user in the database
    if target_id_raw.startswith("@"):
        stmt = select(User).where(User.username == target_id_raw[1:])
    elif target_id_raw.isdigit():
        stmt = select(User).where(User.telegram_id == int(target_id_raw))
    else:
        stmt = select(User).where(User.username == target_id_raw)

    result = await db_session.execute(stmt)
    target_user = result.scalar_one_or_none()

    if not target_user:
        return await message.answer(f"User {target_id_raw} not found in database.")

    # Update role and persist changes
    target_user.role = new_role
    await db_session.commit()

    # Prepare localized notification for the target user
    lang = target_user.preferred_language or "en"
    notification = get_text(lang, "role_changed").format(role=new_role.name)

    # Append role-specific description from texts.py
    if new_role == UserRole.REGULAR:
        notification += "\n\n" + get_text(lang, "role_desc_regular")
    elif new_role == UserRole.ADMIN:
        notification += "\n\n" + get_text(lang, "role_desc_admin")
    elif new_role == UserRole.OWNER:
        notification += "\n\n" + get_text(lang, "role_desc_owner")

    # Send notification to the target user and confirmation to the owner
    try:
        await bot.send_message(chat_id=target_user.telegram_id, text=notification)
        await message.answer(f"✅ Role for {target_id_raw} updated to {new_role.name}")
    except Exception as e:
        await message.answer(f"✅ Role updated, but notification failed: {e}")




async def set_bot_commands(bot: Bot):
    """Set up localized bot command menus concurrently."""
    scope = BotCommandScopeAllPrivateChats()
    tasks = []

    # 1. Base menu (fallback without language_code)
    default_commands = [
        BotCommand(
            command="language",
            description=get_text(DEFAULT_LANGUAGE, "cmd_change_lang_desc")
        )
    ]
    tasks.append(bot.set_my_commands(commands=default_commands, scope=scope))

    # 2. Localized menus for specific languages
    for lang in SUPPORTED_LANGUAGES:
        localized_commands = [
            BotCommand(
                command="language",
                description=get_text(lang, "cmd_change_lang_desc")
            )
        ]
        tasks.append(
            bot.set_my_commands(
                commands=localized_commands,
                scope=scope,
                language_code=lang
            )
        )

    # 3. Execute all API requests concurrently
    try:
        await asyncio.gather(*tasks)
        logger.info("Bot commands successfully set for all languages.")
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}", exc_info=True)


@router.message(Command("maintenance"))
async def cmd_toggle_maintenance(message: types.Message, db_user: User):
    # Restrict to OWNER only
    if db_user.role != UserRole.OWNER:
        return

    # Toggle the state
    BOT_STATE["is_paused"] = not BOT_STATE["is_paused"]

    status = "<b>Maintenance Mode</b>" if BOT_STATE["is_paused"] else "<b>Active</b>"
    await message.answer(f"Current status: {status}\nRegular and Admin users are now blocked." if BOT_STATE[
        "is_paused"] else f"Current status: {status}\nBot is open to everyone.")





# Command for reseting menu

"""from aiogram.types import BotCommandScopeChat

@router.message(Command("reset_menu"))
async def cmd_reset_menu(message: types.Message, bot: Bot):
    try:
        await bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=message.from_user.id))
        await message.answer("✅")
    except Exception as e:
        await message.answer(f"❌ {e}")"""