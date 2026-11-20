import uuid

from sqlalchemy import BigInteger, Column, Integer, Table, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, utcnow
from app.exercises.models import Exercise
from app.gemini.service import GeminiService

exercise_lesson = Table(
    "exercise_lesson",
    Base.metadata,
    Column("lesson_id", BigInteger),
    Column("exercise_id", BigInteger),
    Column("order", Integer),
)


class ExerciseService:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

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

    async def create_exercise(self, db: AsyncSession, lesson_pk: int, decision_type: str) -> Exercise:
        exercise_data = self.gemini_service.generate_exercise()
        exercise = Exercise(
            name=f"Exercise for clause '{exercise_data['sentence']}'",
            clause=exercise_data,
            decision_type=decision_type,
            created_at=utcnow(),
        )
        db.add(exercise)
        await db.commit()
        await db.refresh(exercise)

        await db.execute(insert(exercise_lesson).values(lesson_id=lesson_pk, exercise_id=exercise.pk))
        await db.commit()

        return exercise
