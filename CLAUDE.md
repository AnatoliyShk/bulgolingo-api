# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Bulgarian language learning app, built entirely on FastAPI, with two runtime processes:
1. **FastAPI server** (`main.py`) — REST API (auth, learning paths, lessons, Gemini AI)
2. **Telegram bot** (`scheduler.py`) — sends hourly fill-in-the-blank exercises via aiogram + APScheduler

## Running the project

```bash
uv run uvicorn main:app --reload    # FastAPI server on :8000
uv run python scheduler.py          # Telegram bot + scheduler (separate process)
uv run pytest                       # tests: pure rule checks, no DB or Gemini needed
```

### Docker
```bash
docker compose up --build           # Runs fastapi + scheduler services
```
The compose setup connects to an external Docker network named `sail` (Laravel Sail convention). Start that network first if it doesn't exist.

## Environment variables

Copy `.env.example` to `.env`. Required variables:
- `BOT_TOKEN` — Telegram bot token (optional; when empty, `scheduler.py` exits cleanly and the bot is off)
- `TELEGRAM_CHAT_ID` — chat the scheduler sends exercises to (required by `scheduler.py` only)
- `GEMINI_API_KEY` — Google Gemini API key
- `DATABASE_URL` — async SQLAlchemy URL (e.g. `postgresql+asyncpg://...`)
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` — auth token settings

## Architecture (`main.py` + `app/`)

| Layer | Entry point |
|---|---|
| Settings | `app/config.py` — `Settings` (pydantic-settings, reads `.env`) |
| DB engine/session | `app/database.py` — async SQLAlchemy engine + session factory; `get_db()` dependency, `Base` declarative base |
| Auth | `app/auth/` — `User` model, JWT login (`POST /login`), `get_current_user` dependency used to protect routes; `require_admin` (role `admin`, `users.role_id = 2`) guards writes to lessons/lexemas, exercise deletes and `POST /rag/index`; scripted dialogues/lines are scoped to their owner via `ScriptedDialogue.visible_to(user)` unless admin |
| Learning paths | `app/learning_paths/` — `LearningPath` model + REST routes (`GET /learning-paths/`, `GET /learning-paths/{id}`) |
| Lessons | `app/lessons/` — `Lesson` model + REST routes (`GET/POST /lessons/`, `GET/PUT/PATCH/DELETE /lessons/{id}`) |
| Exercises | `app/exercises/` — read-only `Exercise` model (plus `ExerciseOption`/`ExerciseWordPair`) + REST routes (`GET /exercises/`, `GET/DELETE /exercises/{id}`); no create/edit, Laravel owns exercise content |
| Lexemas | `app/lexemas/` — `Lexema` model + REST routes (`GET/POST /lexemas/`, `GET/PUT/PATCH/DELETE /lexemas/{id}`) |
| Scripted dialogues | `app/scripted_dialogues/` — `ScriptedDialogue` model + REST routes (`GET/POST /scripted-dialogues/`, `GET/PUT/PATCH/DELETE /scripted-dialogues/{id}`) |
| Scripted lines | `app/scripted_lines/` — `ScriptedLine` model + REST routes (`GET/POST /scripted-lines/`, `GET/PUT/PATCH/DELETE /scripted-lines/{id}`) |
| Gemini AI | `app/gemini/router.py` — `POST /ask` endpoint proxying to Gemini |
| RAG / dialogue trees | `app/rag/` — `POST /rag/dialogue-trees`, `GET /rag/lexemas`, `POST /rag/index`; embedding layer in `app/gemini/rag.py` |
| Business logic | service modules inside the feature packages — `app/exercises/service.py` (`ExerciseService`), `app/lexemas/service.py` (`LexemaRagService`), `app/scripted_dialogues/service.py` (`DialogueTreeService`) |

All persistence goes through SQLAlchemy async models under `app/`; there is no other ORM or data layer in this project.

The Postgres database is owned by a separate Laravel/Sail app (see `DATABASE_URL` — a `laravel` user), not by this repo, and this repo has no migrations of its own. `User`, `LearningPath`, `Lesson`, `Exercise`, `Lexema`, `ScriptedDialogue`, and `ScriptedLine` each have a real bigint `id` primary key (Laravel-managed) plus a separate unique `uuid` column (UUIDv7, also Laravel-managed). The SQLAlchemy models expose this as two attributes: `pk` (`Mapped[int]`, mapped to the DB's `id` column — internal only, used for joins against the legacy bigint association tables such as `exercise_lesson`/`exercise_lexema`) and `id` (`Mapped[uuid.UUID]`, mapped to the DB's `uuid` column — this is the public identifier used in every route path param, every response schema, and the JWT `sub` claim). Never use `db.get(Model, ...)` for these models since the primary key (`pk`) is not the public id — look up by `select(Model).where(Model.id == given_uuid)` instead.

### Services
- `ExerciseService` — static helpers over `app.exercises.models.Exercise`: looks one up by uuid and picks a random `fill_in_the_blank` exercise for the scheduler
- Used by `scheduler.py` (not by the FastAPI routes directly)
- `LexemaRagService` (`app/lexemas/service.py`) — in-memory vector index over `lexemas`. There is nowhere to persist embeddings (no migrations in this repo), so it embeds every lexema on first use; after that each search compares (row count, newest `pk`, newest `coalesce(updated_at, created_at)`) and, when any changed, re-embeds only the words stamped since the last build plus any the index lacks, and prunes deleted ones — so adds, edits (here or in Laravel) and deletes are picked up without re-embedding the table. `POST /rag/index` forces a full rebuild (needed only when a linked exercise's sentence changes, which does not touch the word's stamp), and `?since=<date>` re-embeds only the lexemas stamped at or after that moment, merging them into the existing index (it falls back to a full rebuild when the index is still cold, since a partial refresh would otherwise leave a half-populated index that looks complete). Module-level singleton `lexema_rag_service`.
- `DialogueTreeService` (`app/scripted_dialogues/service.py`) — retrieves lexemas for a topic, asks Gemini for a *flat* node list (structured output, `temperature=0` + fixed `seed`), validates that the result is a complete tree of the requested depth/branching, retries once with the fault fed back, then assembles the nested tree. Optionally persists it as a `ScriptedDialogue` + one `ScriptedLine` per node.
- Gemini's SDK is synchronous; async routes call it through `run_in_threadpool` rather than blocking the event loop.

### Scheduler (`scheduler.py`)
- Opens its own `AsyncSession` (via `app.database.AsyncSessionLocal`) per job/callback to query lessons and exercises
- Sends a random fill-in-the-blank exercise to Telegram chat `TELEGRAM_CHAT_ID` every hour (the chat is not a user, so nothing is recorded in `user_exercise_completions`)
- Handles `quiz:<exercise_id>:<option_index>` callback queries by replying "Correct" or the explanation; nothing is stored

## Key inconsistencies to be aware of

- Exercise content lives in Laravel's columns and rows: `exercises.prompt`/`explanation`/`statement_is_true`, `exercise_options` (fill-in-the-blank, image matching) and `exercise_word_pairs` (multiple choice). The legacy `exercises.clause` JSON column is stale — Laravel stopped reading and writing it in its 2026-10-02 migration — so it is deliberately not mapped; `Exercise.clause` is a property that assembles the same per-type shape as Laravel's `ExerciseDefinition::storedClause()`. Keep the two in step when Laravel changes a type.
- The dialogue tree generated by `DialogueTreeService` is *determined*: the whole tree is materialised up front and every node carries a fixed set of replies, so playing it back needs no further model calls. Node ids encode the path (`n1`, `n1.2`, `n1.2.1`), and the model returns empty strings — never nulls — for the root's `parent_id`/`option_*`, which keeps the response schema free of nullable fields.
- `scripted_lines` has no ordering column, so a persisted tree is reconstructed from the `id`/`parent_id` inside each line's `clause`, not from row order.
- `scripted_dialogues.user_id` and `scripted_lines.scripted_dialogue_id` are real bigint foreign keys to the parent `pk`, so the models map them as `user_pk` / `dialogue_pk` and expose the parent's public uuid through the `user_id` / `dialogue_id` properties (backed by a `selectin` relationship). Routes take and return those uuids and resolve them to a `pk` before writing.
- `lexemas.language_id` is required and words are unique per `(language_id, word)` (Laravel's `lexemas_language_id_word_unique`). New words take Laravel's default content language (`bg`, its `learning.default_language` config) via a column default; a duplicate word on create/PUT/PATCH returns 409.
- `lexemas` has no exercise column: words link to exercises many-to-many through `exercise_lexema` (bigint `exercise_id`/`lexema_id`, defined in `app/lexemas/models.py`). `GET /lexemas/?exercise_id=` filters through it; the API does not create or remove those links. The RAG index uses the oldest linked exercise's `prompt` and `explanation` as context for each word.
- The `exercise_lesson` association table (in `app/exercises/models.py`) stores plain bigint columns for `lesson_id`/`exercise_id` (referencing the internal `pk`, not the public `uuid`) and declares no `ForeignKey` constraint to the parent tables
