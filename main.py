# main.py - Запуск 
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode  
from aiogram.client.default import DefaultBotProperties  
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.chat_action import ChatActionMiddleware
from datetime import datetime, timezone

from config import load_config
from database.db import Database
from utils.cache import Cache
from handlers import setup_handlers
from middlewares import CacheMiddleware


async def send_reminders_loop(bot: Bot, db: Database):
    """Фоновий процес для перевірки та відправки нагадувань."""
    while True:
        try:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


            reminders = db.execute(
                "SELECT * FROM reminders WHERE remind_at <= ?", 
                (now,), 
                fetchall=True
            )

            for reminder in reminders:
                user_id = reminder["user_id"]
                text = reminder["text"]

                try:
                    await bot.send_message(user_id, f"🔔 Нагадування: {text}")
                except Exception as e:
                    logging.error(f"Не вдалося надіслати нагадування користувачу {user_id}: {e}")

   
                db.delete_reminder(reminder["id"])

        except Exception as e:
            logging.error(f"Помилка у фоновому процесі нагадувань: {e}")

        await asyncio.sleep(60) 


async def register_middleware(dp, config):
    """Реєстрація middleware."""
    cache = Cache(ttl=config.cache.ttl)
    dp.message.middleware(CacheMiddleware(cache))
    dp.callback_query.middleware(CacheMiddleware(cache))
    dp.message.middleware(ChatActionMiddleware())


async def main():
    """Головна функція запуску бота."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    config = load_config()
    db = Database(config.db.path)
    db.connect()
    db.create_tables()

    cache = Cache(ttl=config.cache.ttl)

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp["config"] = config
    dp["db"] = db
    dp["cache"] = cache

    setup_handlers(dp)
    await register_middleware(dp, config)


    asyncio.create_task(send_reminders_loop(bot, db))

    try:
        logging.info("Бот запущено")
        await dp.start_polling(bot)
    finally:
        logging.info("Бот зупинено")
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот зупинено")
