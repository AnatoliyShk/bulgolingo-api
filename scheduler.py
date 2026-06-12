# scheduler.py
import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings
from app.learning_paths.crud import (
    complete_exercise,
    get_exercise,
    get_incomplete_lesson,
    get_uncompleted_fill_in_the_blank_exercises,
)
from app.database import AsyncSessionLocal


bot = Bot(token=settings.bot_token)
dp = Dispatcher()
CHAT_ID = 304642547


async def send_hourly_report():
    async with AsyncSessionLocal() as session:
        lesson = await get_incomplete_lesson(session)
        if not lesson:
            await bot.send_message(CHAT_ID, "No incomplete lessons found.")
            return

        exercise = get_uncompleted_fill_in_the_blank_exercises(lesson)
        if not exercise:
            await bot.send_message(CHAT_ID, "No uncompleted exercises found.")
            return

        clause = exercise.clause
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=option,
                        callback_data=f"quiz:{exercise.id}:{index}",
                    )
                ]
                for index, option in enumerate(clause["options"])
            ]
        )

        await bot.send_message(CHAT_ID, clause["sentence"], reply_markup=keyboard)


@dp.callback_query(F.data.startswith("quiz:"))
async def handle_quiz_answer(callback: CallbackQuery):
    _, exercise_id, option_index = callback.data.split(":")

    async with AsyncSessionLocal() as session:
        exercise = await get_exercise(session, int(exercise_id))
        clause = exercise.clause

        if int(option_index) == clause["correct_option"]:
            await complete_exercise(session, exercise)
            await callback.message.answer("Correct")
        else:
            await callback.message.answer(clause["explanation"])

    await callback.answer()


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_hourly_report, "interval", hours=1, next_run_time=datetime.now())
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
