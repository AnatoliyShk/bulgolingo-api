from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.learning_paths.models import LearningPath
from app.learning_paths.schemas import LearningPathOut

router = APIRouter(prefix="/learning-paths", tags=["learning-paths"])


@router.get("/", response_model=list[LearningPathOut])
async def list_learning_paths(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LearningPath))
    return result.scalars().all()
