import uuid

from sqlalchemy import BigInteger, Column, DateTime, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Lexema(Base):
    __tablename__ = "lexemas"

    pk: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column("uuid", UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    word: Mapped[str] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)


# Laravel's many-to-many link between lexemas and exercises (both columns hold the parents' bigint pk).
exercise_lexema = Table(
    "exercise_lexema",
    Base.metadata,
    Column("exercise_id", BigInteger),
    Column("lexema_id", BigInteger),
)
