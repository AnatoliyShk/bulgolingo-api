
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
 
from .database import engine, Base, get_db
from .models import Item
from .schemas import ItemCreate, ItemRead
from .. import crud
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
 
app = FastAPI(title="FastAPI + Laravel Sail PostgreSQL", lifespan=lifespan)
 
 
@app.get("/")
async def root():
    return {"message": "FastAPI is connected to Sail PostgreSQL"}
 
 
@app.get("/items", response_model=list[ItemRead])
async def list_items(db: AsyncSession = Depends(get_db)):
    return await crud.get_items(db)
 
 
@app.get("/items/{item_id}", response_model=ItemRead)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
 
 
@app.post("/items", response_model=ItemRead, status_code=201)
async def create_item(payload: ItemCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_item(db, payload)
 
 
@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
