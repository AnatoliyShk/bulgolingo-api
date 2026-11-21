import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.auth.models import User
from app.database import get_db, utcnow
from app.exercises.models import Exercise
from app.lexemas.models import Lexema, exercise_lexema
from app.lexemas.schemas import LexemaCreate, LexemaOut, LexemaPatch, LexemaUpdate

router = APIRouter(prefix="/lexemas", tags=["lexemas"])


async def _get_lexema_or_404(lexema_id: uuid.UUID, db: AsyncSession) -> Lexema:
    result = await db.execute(select(Lexema).where(Lexema.id == lexema_id))
    lexema = result.scalar_one_or_none()
    if lexema is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lexema not found")
    return lexema


async def _exercise_pk_or_404(exercise_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(select(Exercise.pk).where(Exercise.id == exercise_id))
    exercise_pk = result.scalar_one_or_none()
    if exercise_pk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    return exercise_pk


@router.get("/", response_model=list[LexemaOut])
async def list_lexemas(
    word: str | None = Query(None),
    exercise_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Lexema)
    if word is not None:
        query = query.where(Lexema.word == word)
    if exercise_id is not None:
        query = query.join(exercise_lexema, exercise_lexema.c.lexema_id == Lexema.pk).where(
            exercise_lexema.c.exercise_id == await _exercise_pk_or_404(exercise_id, db)
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=LexemaOut, status_code=status.HTTP_201_CREATED)
async def create_lexema(
    payload: LexemaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    lexema = Lexema(
        word=payload.word,
        created_at=utcnow(),
    )
    db.add(lexema)
    await db.commit()
    await db.refresh(lexema)
    return lexema


@router.get("/{lexema_id}", response_model=LexemaOut)
async def get_lexema(
    lexema_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_lexema_or_404(lexema_id, db)


@router.put("/{lexema_id}", response_model=LexemaOut)
async def replace_lexema(
    lexema_id: uuid.UUID,
    payload: LexemaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    lexema = await _get_lexema_or_404(lexema_id, db)
    lexema.word = payload.word
    lexema.updated_at = utcnow()
    await db.commit()
    await db.refresh(lexema)
    return lexema


@router.patch("/{lexema_id}", response_model=LexemaOut)
async def update_lexema(
    lexema_id: uuid.UUID,
    payload: LexemaPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    lexema = await _get_lexema_or_404(lexema_id, db)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "word" in changes:
        lexema.word = changes["word"]
    lexema.updated_at = utcnow()
    await db.commit()
    await db.refresh(lexema)
    return lexema


@router.delete("/{lexema_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lexema(
    lexema_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    lexema = await _get_lexema_or_404(lexema_id, db)
    await db.delete(lexema)
    await db.commit()
