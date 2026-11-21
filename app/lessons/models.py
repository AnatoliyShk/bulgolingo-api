import uuid

from sqlalchemy import BigInteger, Column, DateTime, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Lesson(Base):
    __tablename__ = "lessons"

    pk: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column("uuid", UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)


learning_path_lesson = Table(
    "learning_path_lesson",
    Base.metadata,
    Column("learning_path_id", BigInteger),
    Column("lesson_id", BigInteger),
)

# One row per exercise a user has finished (bigint pks). Lesson completion is derived from it, as in Laravel.
user_exercise_completions = Table(
    "user_exercise_completions",
    Base.metadata,
    Column("user_id", BigInteger),
    Column("exercise_id", BigInteger),
)
