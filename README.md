# Bulgolingo API

Backend for a Bulgarian language-learning app, built with FastAPI: a REST API plus a
Telegram bot that sends AI-generated fill-in-the-blank exercises.

## Features
- JWT-based login and route protection
- Lesson, exercise, and learning-path REST endpoints backed by a shared PostgreSQL database
- AI-generated Bulgarian fill-in-the-blank exercises via Google Gemini
- Telegram bot that delivers exercises on an hourly schedule
- Retrieval-augmented (RAG) generation of scripted Bulgarian dialogue trees with English translations, grounded in the lexemas stored in the database

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
- `app/lexemas/` — `Lexema` model + routes
- `app/scripted_dialogues/`, `app/scripted_lines/` — scripted dialogue models + routes
- `app/gemini/` — Gemini AI proxy route and the embedding layer (`rag.py`)
- `app/rag/` — retrieval and dialogue-tree generation routes

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

### `app/lexemas`
| Method | Route | Auth | Notes |
|---|---|---|---|
| GET | `/lexemas/` | Yes | List lexemas; filter by `word` or `exercise_id` |
| POST | `/lexemas/` | Yes | Create a lexema |
| GET | `/lexemas/{id}` | Yes | Get one lexema |
| PUT | `/lexemas/{id}` | Yes | Replace a lexema |
| PATCH | `/lexemas/{id}` | Yes | Partially update a lexema |
| DELETE | `/lexemas/{id}` | Yes | Delete a lexema |

### `app/scripted_dialogues`
| Method | Route | Auth | Notes |
|---|---|---|---|
| GET | `/scripted-dialogues/` | Yes | List dialogues; filter by `bot_id` or `user_id` |
| POST | `/scripted-dialogues/` | Yes | Create a dialogue |
| GET | `/scripted-dialogues/{id}` | Yes | Get one dialogue |
| PUT | `/scripted-dialogues/{id}` | Yes | Replace a dialogue |
| PATCH | `/scripted-dialogues/{id}` | Yes | Partially update a dialogue |
| DELETE | `/scripted-dialogues/{id}` | Yes | Delete a dialogue |

### `app/scripted_lines`
| Method | Route | Auth | Notes |
|---|---|---|---|
| GET | `/scripted-lines/` | Yes | List lines; filter by `dialogue_id` |
| POST | `/scripted-lines/` | Yes | Create a line |
| GET | `/scripted-lines/{id}` | Yes | Get one line |
| PUT | `/scripted-lines/{id}` | Yes | Replace a line |
| PATCH | `/scripted-lines/{id}` | Yes | Partially update a line |
| DELETE | `/scripted-lines/{id}` | Yes | Delete a line |

### `app/gemini`
| Method | Route | Auth | Notes |
|---|---|---|---|
| POST | `/ask` | Yes | Proxy to Gemini AI |

### `app/rag`
| Method | Route | Auth | Notes |
|---|---|---|---|
| POST | `/rag/dialogue-trees` | Yes | Generate a scripted Bulgarian dialogue tree grounded in stored lexemas |
| GET | `/rag/lexemas` | Yes | Inspect retrieval: nearest lexemas for a query `q`, top `k` |
| POST | `/rag/index` | Yes | Re-embed lexemas; `since=<date>` re-embeds only those changed at or after it |

## RAG dialogue trees
`POST /rag/dialogue-trees` embeds the topic, pulls the nearest lexemas out of the database, and asks
Gemini for a **determined** dialogue tree: the whole tree is generated up front, so every node has a
fixed set of learner replies and playing it back needs no further model calls. Each node carries the
partner's line in Bulgarian with its English translation; each reply carries the learner's line in
both languages.

```jsonc
// request
{ "topic": "ordering coffee", "level": "A2", "depth": 3, "branching": 2, "lexemas": 12 }
```

```jsonc
// response (abridged)
{
  "title_bg": "В кафенето", "title_en": "At the cafe",
  "topic": "ordering coffee", "level": "A2", "depth": 3, "branching": 2,
  "lexemas": [{ "id": "...", "word": "кафе", "score": 0.81 }],
  "root": {
    "id": "n1",
    "line_bg": "Добър ден! Какво желаете?",
    "line_en": "Good day! What would you like?",
    "lexemas": ["кафе"],
    "replies": [{ "option_bg": "...", "option_en": "...", "next": { "id": "n1.1", "...": "..." } }]
  },
  "dialogue_id": null
}
```

- `depth` (1–5) and `branching` (1–4) describe a complete tree; the two together may not exceed 40 nodes.
- `level` is CEFR (`A1`–`C2`).
- Pass `bot_id` to also store the tree as a scripted dialogue — one `scripted_lines` row per node, with
  the node's `id`/`parent_id` inside `clause` — and `dialogue_id` comes back populated.
- Generation runs at `temperature=0` with a fixed seed, and the result is validated to be a complete
  tree of the requested shape (one retry with the fault fed back to the model, then `502`).
- The vector index lives in memory and is rebuilt automatically when lexemas are added or removed;
  call `POST /rag/index` after editing existing words in place. `POST /rag/index?since=2026-09-01`
  re-embeds only the lexemas created or updated at or after that moment and merges them into the
  existing index, leaving every other vector untouched — `since` also accepts a full timestamp
  (`2026-09-01T12:30:00Z`). The response reports `embedded`, `total` and `partial`; a dated call on a
  cold index has nothing to merge into, so it falls back to a full rebuild and reports `partial: false`.
  Lexemas with no `created_at`/`updated_at` cannot be placed in time and stay out of a dated refresh.

## Environment variables
Copy `.env.example` to `.env` and set:
- `BOT_TOKEN` — Telegram bot token
- `GEMINI_API_KEY` — Google Gemini API key
- `DATABASE_URL` — async SQLAlchemy PostgreSQL URL, e.g. `postgresql+asyncpg://user:pass@host:5432/dbname`
- `JWT_SECRET_KEY` — random secret used to sign/verify login tokens
- `JWT_ALGORITHM` — signing algorithm (default `HS256`)
- `JWT_EXPIRE_MINUTES` — token lifetime in minutes (default `60`)
- `GEMINI_MODEL` — generation model (default `gemini-2.5-flash`)
- `GEMINI_EMBED_MODEL` — embedding model for retrieval (default `gemini-embedding-001`)
- `GEMINI_EMBED_DIM` — embedding dimensions (default `768`)

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
- The RAG vector index is per-process and in memory: it is rebuilt on the first request after each restart, which costs one embedding call per lexema.
