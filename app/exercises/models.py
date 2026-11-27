import uuid

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, SmallInteger, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExerciseOption(Base):
    __tablename__ = "exercise_options"

    pk: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    exercise_pk: Mapped[int] = mapped_column("exercise_id", BigInteger, ForeignKey("exercises.id"))
    position: Mapped[int] = mapped_column(SmallInteger)
    text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)


class ExerciseWordPair(Base):
    __tablename__ = "exercise_word_pairs"

    pk: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    exercise_pk: Mapped[int] = mapped_column("exercise_id", BigInteger, ForeignKey("exercises.id"))
    position: Mapped[int] = mapped_column(SmallInteger)
    term: Mapped[str] = mapped_column(Text)
    translation: Mapped[str] = mapped_column(Text)
    left_position: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    right_position: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)


class Exercise(Base):
    """Read-only: Laravel owns exercise content. The legacy `clause` JSON column is deliberately
    not mapped, since Laravel stopped reading and writing it; `clause` is assembled instead."""

    __tablename__ = "exercises"

    pk: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column("uuid", UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    decision_type: Mapped[str] = mapped_column(String)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text)
    statement_is_true: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    options: Mapped[list[ExerciseOption]] = relationship(order_by=ExerciseOption.position, lazy="selectin", viewonly=True)
    word_pairs: Mapped[list[ExerciseWordPair]] = relationship(order_by=ExerciseWordPair.position, lazy="selectin", viewonly=True)

    @property
    def clause(self) -> dict:
        """The clause as Laravel's ExerciseDefinition::storedClause() assembles it for each type."""
        if self.decision_type == "true_false":
            return {
                "sentence": self.prompt or "",
                "correct_option": bool(self.statement_is_true),
                "explanation": self.explanation,
            }
        if self.decision_type == "multiple_choice":
            pairs = self.word_pairs
            clause: dict = {"pairs": [[pair.translation, pair.term] for pair in pairs]}
            if pairs and all(p.left_position is not None and p.right_position is not None for p in pairs):
                clause["order"] = {
                    "left": [p.position for p in sorted(pairs, key=lambda p: p.left_position)],
                    "right": [p.position for p in sorted(pairs, key=lambda p: p.right_position)],
                }
            clause["explanation"] = self.explanation
            return clause
        # fill_in_the_blank and image_matching: answers are option rows, one flagged correct
        clause = {
            "options": [option.text for option in self.options],
            "correct_option": next((o.position for o in self.options if o.is_correct), None),
            "explanation": self.explanation,
        }
        if self.decision_type == "fill_in_the_blank":
            clause = {"sentence": self.prompt or "", **clause}
        return clause


# Laravel's ordered many-to-many link between lessons and exercises (bigint pks).
exercise_lesson = Table(
    "exercise_lesson",
    Base.metadata,
    Column("lesson_id", BigInteger),
    Column("exercise_id", BigInteger),
    Column("order", Integer),
)
