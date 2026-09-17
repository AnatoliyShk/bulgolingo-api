from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    language: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    level: Mapped[str | None] = mapped_column(String(2), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
