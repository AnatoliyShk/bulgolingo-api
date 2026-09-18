from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    clause: dict
    decision_type: str
    created_at: datetime | None
    updated_at: datetime | None


class ExerciseCreate(BaseModel):
    name: str
    clause: dict
    decision_type: str = "fill_in_the_blank"


class ExerciseUpdate(BaseModel):
    name: str
    clause: dict
    decision_type: str = "fill_in_the_blank"


class ExercisePatch(BaseModel):
    name: str | None = None
    clause: dict | None = None
    decision_type: str | None = None
