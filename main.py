from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.learning_paths.router import router as learning_paths_router
from app.exercises.router import router as exercises_router
from app.lessons.router import router as lessons_router
from app.lexemas.router import router as lexemas_router
from app.scripted_dialogues.router import router as scripted_dialogues_router
from app.scripted_lines.router import router as scripted_lines_router
from app.gemini.router import router as gemini_router
from app.rag.router import router as rag_router


app = FastAPI(title="Bot API", version="0.7.27")

app.include_router(auth_router)
app.include_router(learning_paths_router)
app.include_router(lessons_router)
app.include_router(exercises_router)
app.include_router(lexemas_router)
app.include_router(scripted_dialogues_router)
app.include_router(scripted_lines_router)
app.include_router(gemini_router)
app.include_router(rag_router)


@app.get("/")
async def root():
    return {"message": "FastAPI is connected to Sail PostgreSQL"}
