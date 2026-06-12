from pydantic import BaseModel


class LessonCreate(BaseModel):
    name: str
    description: str | None = None


class LessonRead(LessonCreate):
    id: int

    model_config = {"from_attributes": True}
