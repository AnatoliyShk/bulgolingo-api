import uuid

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.models import User
from app.database import Base


class ScriptedDialogue(Base):
    __tablename__ = "scripted_dialogues"

    pk: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column("uuid", UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    bot_id: Mapped[int] = mapped_column(BigInteger)
    user_pk: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(lazy="selectin")

    @property
    def user_id(self) -> uuid.UUID:
        """Public id of the owning user (the `uuid` column, not the bigint FK)."""
        return self.user.id
