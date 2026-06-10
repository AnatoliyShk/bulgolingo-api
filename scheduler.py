# scheduler.py
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from google import genai
from google.genai import errors
from app.config import settings
from app.crud import get_lessons
from app.database import AsyncSessionLocal
from datetime import datetime


bot = Bot(token=settings.bot_token)
client = genai.Client(api_key=settings.gemini_api_key)
CHAT_ID = 304642547

async def send_hourly_report():

    async with AsyncSessionLocal() as session:
        lessons = await get_lessons(session)

    try:
        result = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents="give me random joke on Bulgarian language",
        )
        joke = result.text
    except errors.APIError as e:
        joke = f"(could not fetch a joke: {e})"

    if not lessons:
        await bot.send_message(CHAT_ID, f'No lessons found.\n\n{joke}', parse_mode="Markdown")
    else:
        await bot.send_message(CHAT_ID, f'Lessons count: {len(lessons)}\n\n{joke}', parse_mode="Markdown")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_hourly_report, "interval", hours=1, next_run_time=datetime.now())
    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())