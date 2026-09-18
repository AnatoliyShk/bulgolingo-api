from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    is_completed: bool
    created_at: datetime | None
    updated_at: datetime | None


class LessonCreate(BaseModel):
    name: str
    description: str = ""


class LessonUpdate(BaseModel):
    name: str
    description: str = ""


class LessonPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    is_completed: bool | None = None
