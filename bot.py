import asyncio
import logging
import logging.handlers
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database.repository import init_db
from handlers import start, meme, favorites, payments, referral, admin
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.user_check import UserCheckMiddleware


def setup_logging():
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))

    file_handler = logging.handlers.RotatingFileHandler(
        "bot.log", maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(fmt))

    logging.basicConfig(level=logging.INFO, handlers=[handler, file_handler])
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Initialising database…")
    await init_db()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares (order matters: user_check first, then rate_limit for messages)
    dp.update.middleware(UserCheckMiddleware())
    dp.message.middleware(RateLimitMiddleware())

    # Routers
    dp.include_router(admin.router)      # admin first — higher priority
    dp.include_router(start.router)
    dp.include_router(payments.router)
    dp.include_router(referral.router)
    dp.include_router(favorites.router)
    dp.include_router(meme.router)       # catch-all text last

    logger.info("Starting bot…")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
