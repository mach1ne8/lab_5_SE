import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import *
from handlers import basement
from db import create_db_pool
from middlewares import DatabaseMiddleware

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN_BOT)

dp = Dispatcher()


async def create_pool():
    try:
        pool = await create_db_pool()
        if pool:
            logging.info("Пул базы данных успешно создан.")
        else:
            logging.error("Не удалось создать пул базы данных.")
        return pool
    except Exception as e:
        logging.error(f"Ошибка при создании пула базы данных: {e}")
        return None


async def main():
    pool = await create_pool()
    if pool is None:
        logging.error("Не удалось инициализировать пул базы данных. Бот не может продолжить работу.")
        return

    dp.update.middleware(DatabaseMiddleware(pool))

    try:
        dp.include_router(basement.router)
        await dp.start_polling(bot)
    finally:
        await pool.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен вручную.")
