from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LexemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    word: str
    exercise_id: UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class LexemaCreate(BaseModel):
    word: str
    exercise_id: UUID | None = None


class LexemaUpdate(BaseModel):
    word: str
    exercise_id: UUID | None = None


class LexemaPatch(BaseModel):
    word: str | None = None
    exercise_id: UUID | None = None
