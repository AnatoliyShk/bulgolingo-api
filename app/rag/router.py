import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.rag.schemas import (
    DialogueTreeOut,
    DialogueTreeRequest,
    LexemaIndexOut,
    RetrievedLexemaOut,
)
from services.dialogue_tree_service import DialogueTreeService, TreeGenerationError
from services.rag_service import lexema_rag_service

router = APIRouter(prefix="/rag", tags=["rag"])

dialogue_tree_service = DialogueTreeService()


@router.get("/lexemas", response_model=list[RetrievedLexemaOut])
async def search_lexemas(
    q: str = Query(min_length=1, description="Free text; Bulgarian or English both work"),
    k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The retrieval half of the pipeline on its own, for inspecting what a topic pulls in."""
    lexemas = await lexema_rag_service.retrieve(db, q, k)
    return [
        RetrievedLexemaOut(id=lexema.id, word=lexema.word, score=lexema.score)
        for lexema in lexemas
    ]


@router.post("/index", response_model=LexemaIndexOut)
async def rebuild_index(
    since: datetime | None = Query(
        None,
        description=(
            "Re-embed only lexemas created or updated at or after this moment "
            "(date or timestamp, e.g. 2026-09-01 or 2026-09-01T12:30:00Z). "
            "Omit to re-embed everything."
        ),
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-embed lexemas. Only needed when existing words are edited in place —
    added and removed ones are picked up automatically."""
    result = await lexema_rag_service.build_index(db, since)
    return LexemaIndexOut(
        embedded=result.embedded,
        total=result.total,
        partial=result.partial,
        since=since,
    )


@router.post("/dialogue-trees", response_model=DialogueTreeOut)
async def generate_dialogue_tree(
    request: DialogueTreeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a fully scripted Bulgarian dialogue tree grounded in stored lexemas."""
    try:
        return await dialogue_tree_service.generate(db, request, current_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown bot_id {request.bot_id}",
        )
    except TreeGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
