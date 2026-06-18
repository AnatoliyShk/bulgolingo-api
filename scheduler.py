import asyncio
import os
from datetime import datetime

import django
from asgiref.sync import sync_to_async
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services import ExerciseService

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from learning_paths.models import Exercise, Lesson  # noqa: E402
from app.config import settings

bot = Bot(token=settings.bot_token)
dp = Dispatcher()
CHAT_ID = 304642547


async def send_hourly_report():
    lesson = await ExerciseService.get_incomplete_lesson()
    if not lesson:
        await bot.send_message(CHAT_ID, "No incomplete lessons found.")
        return

    exercise = await ExerciseService.get_uncompleted_fill_in_the_blank(lesson)
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
    exercise = await ExerciseService.get_exercise(int(exercise_id))
    clause = exercise.clause

    if int(option_index) == clause["correct_option"]:
        await ExerciseService.complete_exercise(exercise)
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
