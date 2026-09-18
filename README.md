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
generating and persisting exercises), used by `scheduler.py`. `ExerciseService` has no notion of
"completed" exercises — it picks the earliest lesson with exercises and its earliest
fill-in-the-blank exercise every run, so the scheduler currently resends the same exercise on
every hourly tick rather than progressing through a lesson.

The connected PostgreSQL database is the same one used by the companion Laravel app (`bulgolingo`) —
this API reads/writes the shared production schema (`learning_paths`, `lessons`, `exercises`, `users`, etc.),
it does not own a separate database.

## Current endpoints
Every endpoint requires `Authorization: Bearer <token>` except `GET /`, `GET /docs`/`/redoc`, and `POST /login` itself.

### General
| Method | Route | Auth | Notes |
|---|---|---|---|
| GET | `/` | No | Health check |
| GET | `/docs`, `/redoc` | No | Interactive API docs (Swagger / ReDoc) |

### `app/auth`
| Method | Route | Auth | Notes |
|---|---|---|---|
| POST | `/login` | No | Exchange `{email, password}` for a JWT access token |

### `app/learning_paths`
| Method | Route | Auth | Notes |
|---|---|---|---|
| GET | `/learning-paths/` | Yes | List learning paths |
| GET | `/learning-paths/{id}` | Yes | Get one learning path |

### `app/lessons`
| Method | Route | Auth | Notes |
|---|---|---|---|
| GET | `/lessons/` | Yes | List lessons |
| POST | `/lessons/` | Yes | Create a lesson |
| GET | `/lessons/{id}` | Yes | Get one lesson |
| PUT | `/lessons/{id}` | Yes | Replace a lesson |
| PATCH | `/lessons/{id}` | Yes | Partially update a lesson |
| DELETE | `/lessons/{id}` | Yes | Delete a lesson |

### `app/exercises`
| Method | Route | Auth | Notes |
|---|---|---|---|
| GET | `/exercises/` | Yes | List exercises |
| POST | `/exercises/` | Yes | Create an exercise |
| GET | `/exercises/{id}` | Yes | Get one exercise |
| PUT | `/exercises/{id}` | Yes | Replace an exercise |
| PATCH | `/exercises/{id}` | Yes | Partially update an exercise |
| DELETE | `/exercises/{id}` | Yes | Delete an exercise |

### `app/gemini`
| Method | Route | Auth | Notes |
|---|---|---|---|
| POST | `/ask` | Yes | Proxy to Gemini AI |

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
None currently known.
