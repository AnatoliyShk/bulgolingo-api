from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScriptedDialogueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bot_id: int
    user_id: UUID
    created_at: datetime | None
    updated_at: datetime | None


class ScriptedDialogueCreate(BaseModel):
    bot_id: int
    user_id: UUID


class ScriptedDialogueUpdate(BaseModel):
    bot_id: int
    user_id: UUID


class ScriptedDialoguePatch(BaseModel):
    bot_id: int | None = None
    user_id: UUID | None = None
