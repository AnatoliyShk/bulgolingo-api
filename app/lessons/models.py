from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    exercises: Mapped[list["Exercise"]] = relationship(back_populates="lesson")


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    lesson_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("lessons.id"))
    clause: Mapped[dict] = mapped_column(JSON)
    decision_type: Mapped[str] = mapped_column(String, default="fill_in_the_blank")
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    lesson: Mapped["Lesson"] = relationship(back_populates="exercises")
