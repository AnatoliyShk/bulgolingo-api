from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exists, select
from .models import Exercise, Lesson
from .schemas import LessonCreate


async def get_lessons(db: AsyncSession) -> list[Lesson]:
    result = await db.execute(select(Lesson))
    return result.scalars().all()


async def get_incomplete_lessons(db: AsyncSession) -> list[Lesson]:
    stmt = select(Lesson).where(
        exists().where(
            Exercise.lesson_id == Lesson.id,
            Exercise.is_completed.is_(False),
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_incomplete_lesson(db: AsyncSession) -> Lesson | None:
    stmt = (
        select(Lesson)
        .where(
            exists().where(
                Exercise.lesson_id == Lesson.id,
                Exercise.is_completed.is_(False),
            )
        )
        .order_by(Lesson.created_at.asc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_lesson(db: AsyncSession, lesson_id: int) -> Lesson | None:
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    return result.scalar_one_or_none()


async def get_exercise(db: AsyncSession, exercise_id: int) -> Exercise | None:
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    return result.scalar_one_or_none()


async def complete_exercise(db: AsyncSession, exercise: Exercise) -> Exercise:
    exercise.is_completed = True
    await db.commit()
    await db.refresh(exercise)
    return exercise


def get_fill_in_the_blank_exercises(lesson: Lesson) -> list[Exercise]:
    return [e for e in lesson.exercises if e.decision_type == "fill_in_the_blank"]


def get_uncompleted_fill_in_the_blank_exercises(lesson: Lesson) -> Exercise | None:
    exercises = [e for e in get_fill_in_the_blank_exercises(lesson) if not e.is_completed]
    if not exercises:
        return None
    return min(exercises, key=lambda e: e.created_at)


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
