import uuid

from sqlalchemy import BigInteger, Column, Integer, Table, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base
from app.exercises.models import Exercise

exercise_lesson = Table(
    "exercise_lesson",
    Base.metadata,
    Column("lesson_id", BigInteger),
    Column("exercise_id", BigInteger),
    Column("order", Integer),
)


class ExerciseService:
    @staticmethod
    async def get_exercise(db: AsyncSession, exercise_id: uuid.UUID) -> Exercise | None:
        result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_random_fill_in_the_blank_exercise(db: AsyncSession) -> Exercise | None:
        result = await db.execute(
            select(Exercise)
            .where(Exercise.decision_type == "fill_in_the_blank")
            .order_by(func.random())
            .limit(1)
        )
        return result.scalars().first()
