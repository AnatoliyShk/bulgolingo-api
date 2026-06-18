# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Bulgarian language learning app with two runtime processes:
1. **FastAPI server** (`main.py`) — REST API with Gemini AI integration
2. **Telegram bot** (`scheduler.py`) — sends hourly fill-in-the-blank exercises via aiogram + APScheduler

## Running the project

### Local development (Django side)
```bash
python manage.py runserver          # Django dev server (models, admin, migrations)
python manage.py migrate            # Apply Django migrations
python manage.py makemigrations     # Create new migrations
```

### Local development (FastAPI side)
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
- `DATABASE_URL` — async SQLAlchemy URL (e.g. `postgresql+asyncpg://...`) used by FastAPI/SQLAlchemy

Django uses SQLite (`db.sqlite3`) configured directly in `config/settings.py` and does not read `DATABASE_URL`.

## Architecture: dual-framework design

This project runs **two frameworks simultaneously** — Django and FastAPI — with distinct responsibilities:

| Layer | Framework | Entry point |
|---|---|---|
| Data models & migrations | Django | `learning_paths/models.py`, `config/settings.py` |
| Admin interface | Django | `/admin/` |
| Lesson CRUD REST API | Django views | `learning_paths/views.py` → `config/urls.py` |
| Gemini AI REST endpoint | FastAPI | `app/gemini/router.py` → `main.py` |
| Telegram bot + scheduler | aiogram + APScheduler | `scheduler.py` |
| Business logic | Plain Python services | `services/` |

### Django app (`config/` + `learning_paths/`)
- Standard Django project layout; `config/` is the project package (settings, urls, wsgi, asgi)
- `learning_paths/` is the only Django app; models: `LearningPath`, `Lesson`, `Exercise`
- `Exercise.clause` is a JSONField storing the AI-generated quiz structure: `{sentence, options, correct_option, explanation}`
- Django routes under `/api/` (e.g. `GET /api/lessons/`, `POST /api/lessons/`)

### FastAPI app (`main.py` + `app/`)
- `app/config.py` — `Settings` (pydantic-settings, reads `.env`)
- `app/database.py` — async SQLAlchemy engine + session factory; `get_db()` dependency
- `app/gemini/router.py` — `POST /ask` endpoint proxying to Gemini
- FastAPI currently does not have its own ORM models; the Django ORM models are the source of truth for data

### Services (`services/`)
- `GeminiService` — wraps `google.genai.Client`, calls Gemini to generate Bulgarian fill-in-the-blank exercises
- `ExerciseService` — queries Django ORM for incomplete lessons/exercises, calls `GeminiService.generate_exercise()`, creates `Exercise` records
- Used by `scheduler.py` (not by the FastAPI routes directly)

### Scheduler (`scheduler.py`)
- Bootstraps Django (`django.setup()`) before importing models, so it can use the Django ORM
- Sends an exercise to Telegram chat ID `304642547` every hour
- Handles `quiz:<exercise_id>:<option_index>` callback queries to mark exercises complete

## Key inconsistencies to be aware of

- `services/gemini_service.py` imports from both `django.conf.settings` (unused) and `app.config.settings` — the Django import is vestigial
- `app/routes.py` is unused; `main.py` imports from `app.learning_paths.router` which does not exist yet (import is commented out in `main.py`)
- `GeminiService.generate_exercise()` uses the OpenAI-style `client.chat.completions.create` API, but the installed SDK is `google-genai` which uses `client.models.generate_content` — this method will fail at runtime
