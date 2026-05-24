
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
 
from .database import engine, Base, get_db
from .models import Lesson
from .schemas import LessonCreate, LessonRead
from app import crud
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
 
app = FastAPI(title="FastAPI + Laravel Sail PostgreSQL", lifespan=lifespan)
 
 
@app.get("/")
async def root():
    return {"message": "FastAPI is connected to Sail PostgreSQL"}


@app.get("/lessons", response_model=list[LessonRead])
async def list_lessons(db: AsyncSession = Depends(get_db)):
    return await crud.get_lessons(db)


@app.get("/lessons/{lesson_id}", response_model=LessonRead)
async def get_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    lesson = await crud.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@app.post("/lessons", response_model=LessonRead, status_code=201)
async def create_lesson(payload: LessonCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_lesson(db, payload)


@app.delete("/lessons/{lesson_id}", status_code=204)
async def delete_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_lesson(db, lesson_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
