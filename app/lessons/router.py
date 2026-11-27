import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.auth.models import User
from app.database import Page, get_db, utcnow
from app.exercises.models import exercise_lesson
from app.lessons.models import Lesson, user_exercise_completions
from app.lessons.schemas import LessonCreate, LessonOut, LessonPatch, LessonUpdate

router = APIRouter(prefix="/lessons", tags=["lessons"])


async def _get_lesson_or_404(lesson_id: uuid.UUID, db: AsyncSession) -> Lesson:
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


@router.get("/", response_model=list[LessonOut])
async def list_lessons(
    is_completed: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: Page = Depends(),
):
    query = select(Lesson)
    if is_completed is not None:
        # Laravel's rule (ProgressService::isComplete): done when the lesson has exercises
        # and the current user has completed every one of them
        completed = (
            select(exercise_lesson.c.lesson_id)
            .outerjoin(
                user_exercise_completions,
                (user_exercise_completions.c.exercise_id == exercise_lesson.c.exercise_id)
                & (user_exercise_completions.c.user_id == current_user.pk),
            )
            .group_by(exercise_lesson.c.lesson_id)
            .having(func.count(exercise_lesson.c.exercise_id) > 0)
            .having(func.count(user_exercise_completions.c.exercise_id) == func.count(exercise_lesson.c.exercise_id))
        )
        query = query.where(Lesson.pk.in_(completed) if is_completed else Lesson.pk.not_in(completed))
    result = await db.execute(page.apply(query, Lesson.pk))
    return result.scalars().all()


@router.post("/", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    payload: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    lesson = Lesson(
        name=payload.name,
        description=payload.description,
        created_at=utcnow(),
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.get("/{lesson_id}", response_model=LessonOut)
async def get_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_lesson_or_404(lesson_id, db)


@router.put("/{lesson_id}", response_model=LessonOut)
async def replace_lesson(
    lesson_id: uuid.UUID,
    payload: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    lesson = await _get_lesson_or_404(lesson_id, db)
    lesson.name = payload.name
    lesson.description = payload.description
    lesson.updated_at = utcnow()
    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.patch("/{lesson_id}", response_model=LessonOut)
async def update_lesson(
    lesson_id: uuid.UUID,
    payload: LessonPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    lesson = await _get_lesson_or_404(lesson_id, db)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in changes.items():
        setattr(lesson, field, value)
    lesson.updated_at = utcnow()
    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    lesson = await _get_lesson_or_404(lesson_id, db)
    await db.delete(lesson)
    await db.commit()
