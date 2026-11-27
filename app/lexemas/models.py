import uuid

from sqlalchemy import BigInteger, Column, DateTime, String, Table, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# Laravel's languages table; only what the lexema default below needs.
languages = Table("languages", Base.metadata, Column("id", BigInteger), Column("code", String))

# Laravel's config('learning.default_language'): new words are created in this language when none is named.
DEFAULT_LANGUAGE_CODE = "bg"

# Name of Laravel's unique index on (language_id, word).
WORD_UNIQUE_CONSTRAINT = "lexemas_language_id_word_unique"


class Lexema(Base):
    __tablename__ = "lexemas"

    pk: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column("uuid", UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    word: Mapped[str] = mapped_column(String)
    # resolved inside the INSERT, as Laravel's Lexema `creating` hook does with Language::defaultId()
    language_id: Mapped[int] = mapped_column(
        BigInteger,
        default=select(languages.c.id).where(languages.c.code == DEFAULT_LANGUAGE_CODE).scalar_subquery(),
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)


# Laravel's many-to-many link between lexemas and exercises (both columns hold the parents' bigint pk).
exercise_lexema = Table(
    "exercise_lexema",
    Base.metadata,
    Column("exercise_id", BigInteger),
    Column("lexema_id", BigInteger),
)
