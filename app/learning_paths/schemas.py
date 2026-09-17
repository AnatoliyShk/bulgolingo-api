from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LearningPathOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    language: str
    type: str
    level: str | None
    created_at: datetime | None
    updated_at: datetime | None
