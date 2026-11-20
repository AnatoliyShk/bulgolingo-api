from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LexemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    word: str
    created_at: datetime | None
    updated_at: datetime | None


class LexemaCreate(BaseModel):
    word: str


class LexemaUpdate(BaseModel):
    word: str


class LexemaPatch(BaseModel):
    word: str | None = None
