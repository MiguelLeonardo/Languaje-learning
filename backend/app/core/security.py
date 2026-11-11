"""JWT auth + a tiny per-user rate limiter (replace with gateway/Cloud Armor limits in production)."""

import time
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import User
from app.db.session import get_db

bearer = HTTPBearer(auto_error=False)


def create_token(user_id: str, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {"sub": user_id, "iss": settings.jwt_issuer, "iat": now,
               "exp": now + timedelta(minutes=settings.jwt_ttl_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"],
                             issuer=settings.jwt_issuer, options={"require": ["sub", "exp"]})
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from exc
    user = db.get(User, payload["sub"])
    if not user:
        user = User(id=payload["sub"])
        db.add(user)
        db.commit()
    return user


class RateLimiter:
    def __init__(self, max_calls: int, per_seconds: float):
        self.max_calls, self.per = max_calls, per_seconds
        self._hits: dict[str, deque] = defaultdict(deque)

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        now = time.monotonic()
        q = self._hits[user.id]
        while q and now - q[0] > self.per:
            q.popleft()
        if len(q) >= self.max_calls:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too many attempts, slow down")
        q.append(now)
        return user


speech_rate_limit = RateLimiter(max_calls=60, per_seconds=60)
