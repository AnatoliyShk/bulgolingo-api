from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.learning_paths.router import router as learning_paths_router
from app.exercises.router import router as exercises_router
from app.lessons.router import router as lessons_router
from app.lexemas.router import router as lexemas_router
from app.scripted_dialogues.router import router as scripted_dialogues_router
from app.scripted_lines.router import router as scripted_lines_router
from app.gemini.router import router as gemini_router


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

app = FastAPI(title="Bot API", version="0.5.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(learning_paths_router)
app.include_router(lessons_router)
app.include_router(exercises_router)
app.include_router(lexemas_router)
app.include_router(scripted_dialogues_router)
app.include_router(scripted_lines_router)
app.include_router(gemini_router)


@app.get("/")
async def root():
    return {"message": "FastAPI is connected to Sail PostgreSQL"}
