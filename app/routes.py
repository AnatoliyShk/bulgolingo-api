from app.config import settings
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .crud import get_lessons
from .schemas import Report
from aiogram import Bot


bot = Bot(token=settings.bot_token)

async def send_report(db: AsyncSession, report: Report):
    lessons = await get_lessons(db)

    if not lessons:
        return {"message": "No lessons found."}