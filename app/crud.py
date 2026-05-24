from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Lesson
from .schemas import LessonCreate


async def get_lessons(db: AsyncSession) -> list[Lesson]:
    result = await db.execute(select(Lesson))
    return result.scalars().all()


async def get_lesson(db: AsyncSession, lesson_id: int) -> Lesson | None:
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    return result.scalar_one_or_none()


async def create_lesson(db: AsyncSession, payload: LessonCreate) -> Lesson:
    lesson = Lesson(**payload.model_dump())
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def delete_lesson(db: AsyncSession, lesson_id: int) -> bool:
    lesson = await get_lesson(db, lesson_id)
    if not lesson:
        return False
    await db.delete(lesson)
    await db.commit()
    return True