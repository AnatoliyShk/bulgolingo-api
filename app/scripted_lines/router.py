import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.scripted_dialogues.models import ScriptedDialogue
from app.scripted_lines.models import ScriptedLine
from app.scripted_lines.schemas import (
    ScriptedLineCreate,
    ScriptedLineOut,
    ScriptedLinePatch,
    ScriptedLineUpdate,
)

router = APIRouter(prefix="/scripted-lines", tags=["scripted-lines"])


async def _get_line_or_404(line_id: uuid.UUID, db: AsyncSession) -> ScriptedLine:
    result = await db.execute(select(ScriptedLine).where(ScriptedLine.id == line_id))
    line = result.scalar_one_or_none()
    if line is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scripted line not found")
    return line


async def _dialogue_pk_or_404(dialogue_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(select(ScriptedDialogue.pk).where(ScriptedDialogue.id == dialogue_id))
    dialogue_pk = result.scalar_one_or_none()
    if dialogue_pk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scripted dialogue not found")
    return dialogue_pk


@router.get("/", response_model=list[ScriptedLineOut])
async def list_scripted_lines(
    dialogue_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ScriptedLine)
    if dialogue_id is not None:
        query = query.where(ScriptedLine.dialogue_pk == await _dialogue_pk_or_404(dialogue_id, db))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ScriptedLineOut, status_code=status.HTTP_201_CREATED)
async def create_scripted_line(
    payload: ScriptedLineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = ScriptedLine(
        dialogue_pk=await _dialogue_pk_or_404(payload.dialogue_id, db),
        clause=payload.clause,
        created_at=datetime.now(timezone.utc),
    )
    db.add(line)
    await db.commit()
    await db.refresh(line)
    return line


@router.get("/{line_id}", response_model=ScriptedLineOut)
async def get_scripted_line(
    line_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_line_or_404(line_id, db)


@router.put("/{line_id}", response_model=ScriptedLineOut)
async def replace_scripted_line(
    line_id: uuid.UUID,
    payload: ScriptedLineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = await _get_line_or_404(line_id, db)
    line.dialogue_pk = await _dialogue_pk_or_404(payload.dialogue_id, db)
    line.clause = payload.clause
    line.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(line)
    return line


@router.patch("/{line_id}", response_model=ScriptedLineOut)
async def update_scripted_line(
    line_id: uuid.UUID,
    payload: ScriptedLinePatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = await _get_line_or_404(line_id, db)
    changes = payload.model_dump(exclude_unset=True)
    if "dialogue_id" in changes:
        line.dialogue_pk = await _dialogue_pk_or_404(changes["dialogue_id"], db)
    if "clause" in changes:
        line.clause = changes["clause"]
    line.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(line)
    return line


@router.delete("/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scripted_line(
    line_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = await _get_line_or_404(line_id, db)
    await db.delete(line)
    await db.commit()
