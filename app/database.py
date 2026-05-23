from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os
 
# Reads from environment — see .env file
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://sail:password@pgsql:5432/laravel"
    #                                      ^^^^ 
    #  "pgsql" is the Sail service name — works because
    #  FastAPI joins the same Docker network as Sail
)
 
engine = create_async_engine(DATABASE_URL, echo=True)
 
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
 