import uuid

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.exercises.models import Exercise


class Lexema(Base):
    __tablename__ = "lexemas"

    pk: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column("uuid", UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    word: Mapped[str] = mapped_column(String)
    exercise_pk: Mapped[int | None] = mapped_column(
        "exercise_id", BigInteger, ForeignKey("exercises.id"), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    exercise: Mapped[Exercise | None] = relationship(lazy="selectin")

    @property
    def exercise_id(self) -> uuid.UUID | None:
        """Public id of the linked exercise (the `uuid` column, not the bigint FK)."""
        return self.exercise.id if self.exercise is not None else None
