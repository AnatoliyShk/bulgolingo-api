import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.scripted_dialogues.models import ScriptedDialogue
from app.scripted_dialogues.schemas import (
    ScriptedDialogueCreate,
    ScriptedDialogueOut,
    ScriptedDialoguePatch,
    ScriptedDialogueUpdate,
)

router = APIRouter(prefix="/scripted-dialogues", tags=["scripted-dialogues"])


async def _get_dialogue_or_404(dialogue_id: uuid.UUID, db: AsyncSession) -> ScriptedDialogue:
    result = await db.execute(select(ScriptedDialogue).where(ScriptedDialogue.id == dialogue_id))
    dialogue = result.scalar_one_or_none()
    if dialogue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scripted dialogue not found")
    return dialogue


async def _user_pk_or_404(user_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(select(User.pk).where(User.id == user_id))
    user_pk = result.scalar_one_or_none()
    if user_pk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_pk


@router.get("/", response_model=list[ScriptedDialogueOut])
async def list_scripted_dialogues(
    bot_id: int | None = Query(None),
    user_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ScriptedDialogue)
    if bot_id is not None:
        query = query.where(ScriptedDialogue.bot_id == bot_id)
    if user_id is not None:
        query = query.where(ScriptedDialogue.user_pk == await _user_pk_or_404(user_id, db))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ScriptedDialogueOut, status_code=status.HTTP_201_CREATED)
async def create_scripted_dialogue(
    payload: ScriptedDialogueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dialogue = ScriptedDialogue(
        bot_id=payload.bot_id,
        user_pk=await _user_pk_or_404(payload.user_id, db),
        created_at=datetime.now(timezone.utc),
    )
    db.add(dialogue)
    await db.commit()
    await db.refresh(dialogue)
    return dialogue


@router.get("/{dialogue_id}", response_model=ScriptedDialogueOut)
async def get_scripted_dialogue(
    dialogue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_dialogue_or_404(dialogue_id, db)


@router.put("/{dialogue_id}", response_model=ScriptedDialogueOut)
async def replace_scripted_dialogue(
    dialogue_id: uuid.UUID,
    payload: ScriptedDialogueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dialogue = await _get_dialogue_or_404(dialogue_id, db)
    dialogue.bot_id = payload.bot_id
    dialogue.user_pk = await _user_pk_or_404(payload.user_id, db)
    dialogue.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(dialogue)
    return dialogue


@router.patch("/{dialogue_id}", response_model=ScriptedDialogueOut)
async def update_scripted_dialogue(
    dialogue_id: uuid.UUID,
    payload: ScriptedDialoguePatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dialogue = await _get_dialogue_or_404(dialogue_id, db)
    changes = payload.model_dump(exclude_unset=True)
    if "bot_id" in changes:
        dialogue.bot_id = changes["bot_id"]
    if "user_id" in changes:
        dialogue.user_pk = await _user_pk_or_404(changes["user_id"], db)
    dialogue.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(dialogue)
    return dialogue


@router.delete("/{dialogue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scripted_dialogue(
    dialogue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dialogue = await _get_dialogue_or_404(dialogue_id, db)
    await db.delete(dialogue)
    await db.commit()
