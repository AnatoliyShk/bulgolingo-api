from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import jwt

from app.auth.models import User
from app.auth.security import decode_access_token
from app.database import get_db

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise unauthorized

    user = await db.get(User, user_id)
    if user is None:
        raise unauthorized

    return user
