from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=True)
 
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
 

def utcnow() -> datetime:
    """Current UTC time without tzinfo: Laravel's timestamp columns have no time zone,
    and asyncpg rejects aware datetimes for them."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
