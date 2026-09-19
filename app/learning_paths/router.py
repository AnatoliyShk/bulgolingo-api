import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.learning_paths.models import LearningPath
from app.learning_paths.schemas import LearningPathOut

router = APIRouter(prefix="/learning-paths", tags=["learning-paths"])


@router.get("/", response_model=list[LearningPathOut])
async def list_learning_paths(
    level: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(LearningPath)
    if level is not None:
        query = query.where(LearningPath.level == level)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{learning_path_id}", response_model=LearningPathOut)
async def get_learning_path(
    learning_path_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(LearningPath).where(LearningPath.id == learning_path_id))
    learning_path = result.scalar_one_or_none()
    if learning_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found")
    return learning_path
