# scheduler.py
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
# from app.config import settings
from app.crud import get_lessons
from app.database import AsyncSessionLocal
from datetime import datetime


bot = Bot(token='8765817228:AAHdW5T3kIozIK4ZuMVRZL-lb2DB0vqrmsc')
CHAT_ID = 304642547 

async def send_hourly_report():
    
    await bot.send_message(CHAT_ID, 'test', parse_mode="Markdown")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_hourly_report, "interval", hours=1, next_run_time=datetime.now())
    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())