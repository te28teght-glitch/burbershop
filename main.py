import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database.db import db
from handlers import start, booking, admin

logging.basicConfig(level=logging.INFO)

async def main():
    await db.create_tables()
    
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(admin.router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())