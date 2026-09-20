from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScriptedLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dialogue_id: UUID
    clause: dict
    created_at: datetime | None
    updated_at: datetime | None


class ScriptedLineCreate(BaseModel):
    dialogue_id: UUID
    clause: dict


class ScriptedLineUpdate(BaseModel):
    dialogue_id: UUID
    clause: dict


class ScriptedLinePatch(BaseModel):
    dialogue_id: UUID | None = None
    clause: dict | None = None
