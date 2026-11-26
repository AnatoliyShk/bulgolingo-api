from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.auth.models import User
from app.auth.schemas import LoginRequest, TokenResponse
from app.auth.security import DUMMY_HASH, create_access_token, verify_password
from app.database import get_db

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    # bcrypt takes ~0.25s of CPU; run it off the event loop so other requests keep moving
    password_ok = await run_in_threadpool(verify_password, payload.password, user.password if user else DUMMY_HASH)
    if user is None or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(access_token=create_access_token(user.id))
