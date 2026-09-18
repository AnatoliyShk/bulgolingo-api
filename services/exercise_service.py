from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lessons.models import Exercise, Lesson
from services.gemini_service import GeminiService


class ExerciseService:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

    @staticmethod
    async def get_incomplete_lesson(db: AsyncSession) -> Lesson | None:
        result = await db.execute(
            select(Lesson)
            .join(Exercise)
            .where(Exercise.is_completed.is_(False))
            .order_by(Lesson.created_at)
            .limit(1)
        )
        return result.scalars().first()

    @staticmethod
    async def get_exercise(db: AsyncSession, exercise_id: int) -> Exercise | None:
        return await db.get(Exercise, exercise_id)

    @staticmethod
    async def complete_exercise(db: AsyncSession, exercise: Exercise) -> Exercise:
        exercise.is_completed = True
        await db.commit()
        await db.refresh(exercise)
        return exercise

    @staticmethod
    async def get_uncompleted_fill_in_the_blank(db: AsyncSession, lesson: Lesson) -> Exercise | None:
        result = await db.execute(
            select(Exercise)
            .where(
                Exercise.lesson_id == lesson.id,
                Exercise.decision_type == "fill_in_the_blank",
                Exercise.is_completed.is_(False),
            )
            .order_by(Exercise.created_at)
            .limit(1)
        )
        return result.scalars().first()

    async def create_exercise(self, db: AsyncSession, lesson_id: int, decision_type: str) -> Exercise:
        exercise_data = self.gemini_service.generate_exercise()
        exercise = Exercise(
            name=f"Exercise for clause '{exercise_data['clause']['sentence']}'",
            lesson_id=lesson_id,
            clause=exercise_data,
            decision_type=decision_type,
            created_at=datetime.now(timezone.utc),
        )
        db.add(exercise)
        await db.commit()
        await db.refresh(exercise)
        return exercise
