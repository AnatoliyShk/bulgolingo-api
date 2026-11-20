import uuid

from sqlalchemy import BigInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

ADMIN_ROLE_ID = 2  # `roles` row seeded by the Laravel app: 1 student, 2 admin, 3 admin_visitor


class User(Base):
    __tablename__ = "users"

    pk: Mapped[int] = mapped_column("id", BigInteger, primary_key=True)
    id: Mapped[uuid.UUID] = mapped_column("uuid", UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)
    role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    @property
    def is_admin(self) -> bool:
        return self.role_id == ADMIN_ROLE_ID
