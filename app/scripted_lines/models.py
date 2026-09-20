import uuid

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.scripted_dialogues.models import ScriptedDialogue


class ScriptedLine(Base):
    __tablename__ = "scripted_lines"

    pk: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column("uuid", UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    dialogue_pk: Mapped[int] = mapped_column(
        "scripted_dialogue_id", BigInteger, ForeignKey("scripted_dialogues.id")
    )
    clause: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    dialogue: Mapped[ScriptedDialogue] = relationship(lazy="selectin")

    @property
    def dialogue_id(self) -> uuid.UUID:
        """Public id of the parent dialogue (the `uuid` column, not the bigint FK)."""
        return self.dialogue.id
