import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.commands import router as commands_router, set_bot_commands
from src.bot.callbacks import router as callbacks_router
from src.utils.logger import get_logger
from src.bot.messages import router as messages_router
from src.bot.middlewares import QuotaMiddleware


logger = get_logger(__name__)
load_dotenv()

async def main():
    """bot entry point."""
    token = os.getenv("TELEGRAM_BOT_API_KEY")
    if not token:
        logger.error("telegram token missing in .env")
        raise ValueError("telegram token missing in .env")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.message.middleware(QuotaMiddleware())

    dp.include_router(commands_router)
    dp.include_router(callbacks_router)
    dp.include_router(messages_router)

    await set_bot_commands(bot)

    logger.info("bot is starting...")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("bot stopped by user.")