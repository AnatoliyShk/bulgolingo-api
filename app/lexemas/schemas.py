from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

# stored without surrounding spaces, so `?word=` lookups and Laravel's unique (language_id, word) index see the same text
Word = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class LexemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    word: str
    created_at: datetime | None
    updated_at: datetime | None


class LexemaCreate(BaseModel):
    word: Word


class LexemaUpdate(BaseModel):
    word: Word


class LexemaPatch(BaseModel):
    word: Word | None = None
