from contextlib import asynccontextmanager
 
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
 
from app.config import settings
from app.database import engine, Base, get_db
from app.models import Lesson
from app.schemas import LessonCreate, LessonRead
from app import crud

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import errors
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # await init_db()

    # await bot.set_webhook(url=settings.WEBHOOK_URL, secret_token=settings.WEBHOOK_SECRET_TOKEN)
    # print(f"Webhook set: {settings.webhook_url}")
    # yield   
    # await bot.delete_webhook()
    # await bot.session.close()
    # print("Webhook removed, bot session closed.")
    yield

app = FastAPI(title="Bot API", lifespan=lifespan)

client = genai.Client(api_key=settings.gemini_api_key)

class Query(BaseModel):
    prompt: str
    model: str = "gemini-2.5-flash"

class Answer(BaseModel):
    response: str

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


@app.post("/ask", response_model=Answer)
def ask_gemini(query: Query):
    try:
        result = client.models.generate_content(
            model=query.model,
            contents="give me random joke on Bulgarian language",
        )
    except errors.APIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return Answer(response=result.text)