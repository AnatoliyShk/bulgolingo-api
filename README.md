# Bulgolingo API

Backend for a Bulgarian language-learning app, built with FastAPI: a REST API plus a
Telegram bot that sends AI-generated fill-in-the-blank exercises.

## Features
- JWT-based login and route protection
- Lesson, exercise, and learning-path REST endpoints backed by a shared PostgreSQL database
- AI-generated Bulgarian fill-in-the-blank exercises via Google Gemini
- Telegram bot that delivers exercises on an hourly schedule

## Stack
Python 3 · FastAPI · SQLAlchemy (async) · PostgreSQL · aiogram · APScheduler · JWT (PyJWT + bcrypt) · Docker

## Architecture
Two runtime processes:
1. **FastAPI server** (`main.py`) — REST API, connects to PostgreSQL via async SQLAlchemy (`app/database.py`)
2. **Telegram bot + scheduler** (`scheduler.py`) — sends exercises hourly, built on aiogram + APScheduler

Each resource is its own module under `app/`:
- `app/auth/` — `User` model, `POST /login` (JWT), `get_current_user` dependency used to protect routes
- `app/learning_paths/` — `LearningPath` model + routes
- `app/lessons/` — `Lesson` model + routes
- `app/exercises/` — `Exercise` model + routes
- `app/gemini/` — Gemini AI proxy route

Business logic lives in `services/` (`GeminiService` for calling Gemini, `ExerciseService` for
generating and persisting exercises), used by `scheduler.py`.

The connected PostgreSQL database is the same one used by the companion Laravel app (`bulgolingo`) —
this API reads/writes the shared production schema (`learning_paths`, `lessons`, `exercises`, `users`, etc.),
it does not own a separate database.

## Current endpoints
- `GET /` — health check
- `GET /docs` / `/redoc` — interactive API docs (Swagger / ReDoc)
- `POST /login` — exchange `{email, password}` for a JWT access token
- `GET /learning-paths/` — list learning paths
- `GET /learning-paths/{id}` — get one learning path (requires `Authorization: Bearer <token>`)
- `GET /lessons/`, `POST /lessons/`, `GET /lessons/{id}`, `PUT /lessons/{id}`, `PATCH /lessons/{id}`, `DELETE /lessons/{id}` — lesson CRUD (all require auth)
- `GET /exercises/`, `POST /exercises/`, `GET /exercises/{id}`, `PUT /exercises/{id}`, `PATCH /exercises/{id}`, `DELETE /exercises/{id}` — exercise CRUD (all require auth)
- `POST /ask` — proxy to Gemini AI

## Environment variables
Copy `.env.example` to `.env` and set:
- `BOT_TOKEN` — Telegram bot token
- `GEMINI_API_KEY` — Google Gemini API key
- `DATABASE_URL` — async SQLAlchemy PostgreSQL URL, e.g. `postgresql+asyncpg://user:pass@host:5432/dbname`
- `JWT_SECRET_KEY` — random secret used to sign/verify login tokens
- `JWT_ALGORITHM` — signing algorithm (default `HS256`)
- `JWT_EXPIRE_MINUTES` — token lifetime in minutes (default `60`)

## Running locally
```bash
uvicorn main:app --reload      # FastAPI server on :8000
python scheduler.py            # Telegram bot, separate process
```

## Docker
```bash
docker compose up --build      # runs fastapi + scheduler services
```
Requires an external Docker network named `sail` — create it first if it doesn't exist
(`docker network create sail`).

## Known issues
- `GeminiService.generate_exercise()` (in `services/gemini_service.py`) calls an OpenAI-style
  API (`client.chat.completions.create`), but the installed SDK is `google-genai`, which uses
  `client.models.generate_content` — this will fail at runtime.
- `services/exercise_service.py` references `Exercise.is_completed` and `Exercise.lesson_id`,
  and joins `Lesson`/`Exercise` via a relationship — none of these exist on the live schema
  (completion state lives in `user_exercise_completions`, the lesson/exercise link is the
  `exercise_lesson` pivot table). This breaks the scheduler's exercise-sending flow at runtime.
- `app/learning_paths/router.py`'s list endpoint has no auth dependency while its detail endpoint
  does — likely unfinished, worth confirming intent before relying on either behavior.
- `app/routes.py` is unused dead code.
