from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
 
 
class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
 