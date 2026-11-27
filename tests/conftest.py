import os

# Settings() runs at import time; these let the tests run without a .env. Nothing here reaches the DB or Gemini.
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("JWT_SECRET_KEY", "x" * 32)
