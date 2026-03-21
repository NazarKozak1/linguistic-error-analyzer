from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from src.db.database import AsyncSessionLocal
from src.db.crud import get_or_create_user
from src.db.models import UserRole
from src.bot.config import BOT_STATE



class QuotaMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:

        async with AsyncSessionLocal() as session:
            user, _ = await get_or_create_user(session, event.from_user.id)

            # передаємо завжди
            data["db_user"] = user
            data["db_session"] = session

            if BOT_STATE["is_paused"] and user.role != UserRole.OWNER:
                await event.answer("Bot is under maintenance. Please try again later.")
                return

            # Skip quota checks for commands
            if not event.text or event.text.startswith("/"):
                return await handler(event, data)

            rules = {
                UserRole.REGULAR: {"req_limit": 5, "char_limit": 250},
                UserRole.ADMIN: {"req_limit": 15, "char_limit": 500},
                UserRole.OWNER: {"req_limit": 999999, "char_limit": 4096},
            }

            user_rules = rules.get(user.role, rules[UserRole.REGULAR])

            text_length = len(event.text)
            if text_length > user_rules["char_limit"]:
                await event.answer(
                    f"Text is too long ({text_length}/{user_rules['char_limit']} characters). "
                    f"Please split it into smaller parts."
                )
                return

            if user.daily_requests >= user_rules["req_limit"]:
                await event.answer(
                    f"Daily request limit reached ({user_rules['req_limit']}/{user_rules['req_limit']}). "
                    f"Please try again tomorrow or ask me to get more daily requests: @Kozaknazar"
                )
                return

            return await handler(event, data)