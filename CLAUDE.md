# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Bulgarian language learning app, built entirely on FastAPI, with two runtime processes:
1. **FastAPI server** (`main.py`) — REST API (auth, learning paths, lessons, Gemini AI)
2. **Telegram bot** (`scheduler.py`) — sends hourly fill-in-the-blank exercises via aiogram + APScheduler

## Running the project

```bash
uvicorn main:app --reload           # FastAPI server on :8000
python scheduler.py                 # Telegram bot + scheduler (separate process)
```

### Docker
```bash
docker compose up --build           # Runs fastapi + scheduler services
```
The compose setup connects to an external Docker network named `sail` (Laravel Sail convention). Start that network first if it doesn't exist.

## Environment variables

Copy `.env.example` to `.env`. Required variables:
- `BOT_TOKEN` — Telegram bot token
- `GEMINI_API_KEY` — Google Gemini API key
- `DATABASE_URL` — async SQLAlchemy URL (e.g. `postgresql+asyncpg://...`)
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` — auth token settings

## Architecture (`main.py` + `app/`)

| Layer | Entry point |
|---|---|
| Settings | `app/config.py` — `Settings` (pydantic-settings, reads `.env`) |
| DB engine/session | `app/database.py` — async SQLAlchemy engine + session factory; `get_db()` dependency, `Base` declarative base |
| Auth | `app/auth/` — `User` model, JWT login (`POST /login`), `get_current_user` dependency used to protect routes |
| Learning paths | `app/learning_paths/` — `LearningPath` model + REST routes |
| Lessons | `app/lessons/` — `Lesson` and `Exercise` models + REST routes for lessons (`GET/POST /lessons/`, `GET/PUT/PATCH/DELETE /lessons/{id}`) |
| Gemini AI | `app/gemini/router.py` — `POST /ask` endpoint proxying to Gemini |
| Business logic | `services/` — `GeminiService`, `ExerciseService` |

All persistence goes through SQLAlchemy async models under `app/`; there is no other ORM or data layer in this project.

### Services (`services/`)
- `GeminiService` — wraps `google.genai.Client`, calls Gemini to generate Bulgarian fill-in-the-blank exercises
- `ExerciseService` — queries `app.lessons.models.Lesson`/`Exercise` via an `AsyncSession` for incomplete lessons/exercises, calls `GeminiService.generate_exercise()`, creates `Exercise` records
- Used by `scheduler.py` (not by the FastAPI routes directly)

### Scheduler (`scheduler.py`)
- Opens its own `AsyncSession` (via `app.database.AsyncSessionLocal`) per job/callback to query lessons and exercises
- Sends an exercise to Telegram chat ID `304642547` every hour
- Handles `quiz:<exercise_id>:<option_index>` callback queries to mark exercises complete

## Key inconsistencies to be aware of

- `app/routes.py` is unused dead code (imports modules that don't exist: `.learning_paths.crud`, `.schemas`)
- `GeminiService.generate_exercise()` uses the OpenAI-style `client.chat.completions.create` API, but the installed SDK is `google-genai` which uses `client.models.generate_content` — this method will fail at runtime
- `app/learning_paths/router.py`'s list endpoint has no auth dependency while its detail endpoint does — likely unfinished, worth confirming with the user before relying on either behavior
