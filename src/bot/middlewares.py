from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import select
from src.db.database import AsyncSessionLocal
from src.db.models import User, UserRole
from src.bot.config import BOT_STATE
from src.utils.texts import get_text

class QuotaMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        # Safely extract user_id and text/data depending on event type
        user_id = event.from_user.id
        text = ""
        if isinstance(event, Message):
            text = event.text or ""
        elif isinstance(event, CallbackQuery):
            text = event.data or ""

        # 1. Skip middleware completely for specific commands (Message only)
        if isinstance(event, Message) and (text.startswith("/start") or text.startswith("/language")):
            return await handler(event, data)

        async with AsyncSessionLocal() as session:
            # Fetch user without creating a new record
            result = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = result.scalar_one_or_none()

            # Ignore unregistered users entirely
            if not user:
                return

            # Inject variables for all handlers (Messages AND CallbackQueries)
            data["db_user"] = user
            data["db_session"] = session

            if BOT_STATE["is_paused"] and user.role != UserRole.OWNER:
                if isinstance(event, Message):
                    await event.answer("Bot is under maintenance. Please try again later.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("Bot is under maintenance.", show_alert=True)
                return

            # 2. Skip quota checks for buttons and commands
            if isinstance(event, CallbackQuery) or text.startswith("/"):
                return await handler(event, data)

            # --- Quota checks (Only for regular text messages) ---
            rules = {
                UserRole.REGULAR: {"req_limit": 5, "char_limit": 150},
                UserRole.ADMIN: {"req_limit": 15, "char_limit": 250},
                UserRole.OWNER: {"req_limit": 999999, "char_limit": 4096},
            }

            user_rules = rules.get(user.role, rules[UserRole.REGULAR])

            clean_text = text.strip()
            user_lang = user.preferred_language or "en"

            if len(clean_text) > user_rules["char_limit"]:
                warning_text = get_text(user_lang, "error_text_too_long").format(
                    current_len=len(clean_text),
                    char_limit=user_rules["char_limit"]
                )
                await event.answer(warning_text)
                return

            if user.daily_requests >= user_rules["req_limit"]:
                limit_text = get_text(user_lang, "error_daily_limit_reached").format(
                    req_limit=user_rules["req_limit"]
                )
                await event.answer(limit_text)
                return

            return await handler(event, data)