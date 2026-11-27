import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.auth.models import User
from app.database import get_db
from app.exercises.models import Exercise
from app.exercises.schemas import ExerciseOut

# Read and delete only: Laravel owns exercise content (prompt, explanation, option and word-pair rows)
# and validates it on save, so writes go through the Laravel app.
router = APIRouter(prefix="/exercises", tags=["exercises"])


async def _get_exercise_or_404(exercise_id: uuid.UUID, db: AsyncSession) -> Exercise:
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    return exercise


@router.get("/", response_model=list[ExerciseOut])
async def list_exercises(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Exercise))
    return result.scalars().all()


@router.get("/{exercise_id}", response_model=ExerciseOut)
async def get_exercise(
    exercise_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_exercise_or_404(exercise_id, db)


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    exercise = await _get_exercise_or_404(exercise_id, db)
    await db.delete(exercise)
    await db.commit()
