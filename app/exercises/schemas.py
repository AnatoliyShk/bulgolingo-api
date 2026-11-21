from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator


class FillInTheBlankClause(BaseModel):
    """Laravel's FillInTheBlankExercise clause rules; the Telegram quiz reads every field."""

    sentence: str = Field(min_length=1)
    options: list[str] = Field(min_length=1)
    correct_option: StrictInt  # the bot compares it to an int, so "2" would never be correct
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def _answer_is_an_option(self) -> "FillInTheBlankClause":
        if not 0 <= self.correct_option < len(self.options):
            raise ValueError(f"correct_option {self.correct_option} is not an index into options")
        return self


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
