from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.lessons.models import Lesson
from app.lessons.schemas import LessonCreate, LessonOut, LessonPatch, LessonUpdate

router = APIRouter(prefix="/lessons", tags=["lessons"])


async def _get_lesson_or_404(lesson_id: int, db: AsyncSession) -> Lesson:
    lesson = await db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


@router.get("/", response_model=list[LessonOut])
async def list_lessons(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Lesson))
    return result.scalars().all()


@router.post("/", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    payload: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = Lesson(
        name=payload.name,
        description=payload.description,
        created_at=datetime.now(timezone.utc),
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.get("/{lesson_id}", response_model=LessonOut)
async def get_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_lesson_or_404(lesson_id, db)


@router.put("/{lesson_id}", response_model=LessonOut)
async def replace_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = await _get_lesson_or_404(lesson_id, db)
    lesson.name = payload.name
    lesson.description = payload.description
    lesson.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.patch("/{lesson_id}", response_model=LessonOut)
async def update_lesson(
    lesson_id: int,
    payload: LessonPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = await _get_lesson_or_404(lesson_id, db)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(lesson, field, value)
    lesson.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = await _get_lesson_or_404(lesson_id, db)
    await db.delete(lesson)
    await db.commit()
