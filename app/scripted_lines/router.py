import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db, utcnow
from app.scripted_dialogues.models import ScriptedDialogue
from app.scripted_lines.models import ScriptedLine
from app.scripted_lines.schemas import (
    ScriptedLineCreate,
    ScriptedLineOut,
    ScriptedLinePatch,
    ScriptedLineUpdate,
)

router = APIRouter(prefix="/scripted-lines", tags=["scripted-lines"])


def _visible_lines(user: User):
    return select(ScriptedLine).join(ScriptedLine.dialogue).where(ScriptedDialogue.visible_to(user))


async def _get_line_or_404(line_id: uuid.UUID, db: AsyncSession, user: User) -> ScriptedLine:
    result = await db.execute(_visible_lines(user).where(ScriptedLine.id == line_id))
    line = result.scalar_one_or_none()
    if line is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scripted line not found")
    return line


async def _dialogue_pk_or_404(dialogue_id: uuid.UUID, db: AsyncSession, user: User) -> int:
    result = await db.execute(
        select(ScriptedDialogue.pk).where(ScriptedDialogue.id == dialogue_id, ScriptedDialogue.visible_to(user))
    )
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
    query = _visible_lines(current_user)
    if dialogue_id is not None:
        query = query.where(ScriptedLine.dialogue_pk == await _dialogue_pk_or_404(dialogue_id, db, current_user))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ScriptedLineOut, status_code=status.HTTP_201_CREATED)
async def create_scripted_line(
    payload: ScriptedLineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = ScriptedLine(
        dialogue_pk=await _dialogue_pk_or_404(payload.dialogue_id, db, current_user),
        clause=payload.clause,
        created_at=utcnow(),
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
    return await _get_line_or_404(line_id, db, current_user)


@router.put("/{line_id}", response_model=ScriptedLineOut)
async def replace_scripted_line(
    line_id: uuid.UUID,
    payload: ScriptedLineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = await _get_line_or_404(line_id, db, current_user)
    line.dialogue_pk = await _dialogue_pk_or_404(payload.dialogue_id, db, current_user)
    line.clause = payload.clause
    line.updated_at = utcnow()
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
    line = await _get_line_or_404(line_id, db, current_user)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "dialogue_id" in changes:
        line.dialogue_pk = await _dialogue_pk_or_404(changes["dialogue_id"], db, current_user)
    if "clause" in changes:
        line.clause = changes["clause"]
    line.updated_at = utcnow()
    await db.commit()
    await db.refresh(line)
    return line


@router.delete("/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scripted_line(
    line_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = await _get_line_or_404(line_id, db, current_user)
    await db.delete(line)
    await db.commit()
