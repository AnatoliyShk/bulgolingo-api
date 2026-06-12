from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from . import crud
from .schemas import LessonCreate, LessonRead

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=list[LessonRead])
async def list_lessons(db: AsyncSession = Depends(get_db)):
    return await crud.get_lessons(db)


@router.get("/{lesson_id}", response_model=LessonRead)
async def get_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    lesson = await crud.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.post("", response_model=LessonRead, status_code=201)
async def create_lesson(payload: LessonCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_lesson(db, payload)


@router.delete("/{lesson_id}", status_code=204)
async def delete_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_lesson(db, lesson_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
