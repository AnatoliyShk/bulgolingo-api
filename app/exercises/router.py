import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.exercises.models import Exercise
from app.exercises.schemas import ExerciseCreate, ExerciseOut, ExercisePatch, ExerciseUpdate

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


@router.post("/", response_model=ExerciseOut, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    payload: ExerciseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = Exercise(
        name=payload.name,
        clause=payload.clause,
        decision_type=payload.decision_type,
        created_at=datetime.now(timezone.utc),
    )
    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    return exercise


@router.get("/{exercise_id}", response_model=ExerciseOut)
async def get_exercise(
    exercise_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_exercise_or_404(exercise_id, db)


@router.put("/{exercise_id}", response_model=ExerciseOut)
async def replace_exercise(
    exercise_id: uuid.UUID,
    payload: ExerciseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = await _get_exercise_or_404(exercise_id, db)
    exercise.name = payload.name
    exercise.clause = payload.clause
    exercise.decision_type = payload.decision_type
    exercise.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(exercise)
    return exercise


@router.patch("/{exercise_id}", response_model=ExerciseOut)
async def update_exercise(
    exercise_id: uuid.UUID,
    payload: ExercisePatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = await _get_exercise_or_404(exercise_id, db)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(exercise, field, value)
    exercise.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = await _get_exercise_or_404(exercise_id, db)
    await db.delete(exercise)
    await db.commit()
