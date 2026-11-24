import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

# checked against when the email is unknown, so a miss costs as long as a wrong password
# (cost 12 matches Laravel's default BCRYPT_ROUNDS)
DUMMY_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt(12)).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt 5 raises past 72 bytes; PHP (Laravel) silently truncates there, so match it
    return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))


def create_access_token(user_id: uuid.UUID) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return uuid.UUID(payload["sub"])
