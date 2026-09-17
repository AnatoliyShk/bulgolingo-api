# Bulgolingo API

Backend for a Bulgarian language-learning app, built with FastAPI: a REST API plus a
Telegram bot that sends AI-generated fill-in-the-blank exercises.

## Features
- Learning path listing backed by a shared PostgreSQL database
- AI-generated Bulgarian fill-in-the-blank exercises via Google Gemini
- Telegram bot that delivers exercises on an hourly schedule

## Stack
Python 3 · FastAPI · SQLAlchemy (async) · PostgreSQL · aiogram · APScheduler · Docker

## Architecture
Two runtime processes:
1. **FastAPI server** (`main.py`) — REST API, connects to PostgreSQL via async SQLAlchemy (`app/database.py`)
2. **Telegram bot + scheduler** (`scheduler.py`) — sends exercises hourly, built on aiogram + APScheduler

Business logic lives in `services/` (`GeminiService` for calling Gemini, `ExerciseService` for
generating and persisting exercises).

## Current endpoints
- `GET /` — health check
- `GET /docs` / `/redoc` — interactive API docs (Swagger / ReDoc)
- `GET /learning-paths/` — list learning paths from the database
- `POST /ask` — proxy to Gemini AI

## Environment variables
Copy `.env.example` to `.env` and set:
- `BOT_TOKEN` — Telegram bot token
- `GEMINI_API_KEY` — Google Gemini API key
- `DATABASE_URL` — async SQLAlchemy PostgreSQL URL, e.g. `postgresql+asyncpg://user:pass@host:5432/dbname`

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
- `app/routes.py` is unused dead code.
