from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Query
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url)
 
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
 
 
class Base(DeclarativeBase):
    pass
 
 
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@dataclass
class Page:
    """`?limit=&offset=` for list routes; use as `page: Page = Depends()`."""

    limit: int = Query(100, ge=1, le=500)
    offset: int = Query(0, ge=0)

    def apply(self, query: Select, order_by) -> Select:
        # without a fixed order Postgres may return rows differently per page, skipping or repeating some
        return query.order_by(order_by).limit(self.limit).offset(self.offset)
 

def utcnow() -> datetime:
    """Current UTC time without tzinfo: Laravel's timestamp columns have no time zone,
    and asyncpg rejects aware datetimes for them."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
