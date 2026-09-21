"""
Password hashing and JWT session tokens. Passwords are never stored or
logged in plaintext (sections 44, 46, 60).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

ALGORITHM = "HS256"

# bcrypt's underlying algorithm only uses the first 72 bytes of the input;
# passwords are truncated explicitly (rather than left to fail unpredictably
# on very long input) to keep behaviour deterministic. Using the `bcrypt`
# package directly -- instead of `passlib` -- avoids passlib's unmaintained
# bcrypt-backend self-test, which is incompatible with bcrypt >= 4.1.
_MAX_PASSWORD_BYTES = 72


def _truncate(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_PASSWORD_BYTES]


def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(_truncate(plain_password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate(plain_password), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: str, extra_claims: Optional[dict[str, Any]] = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
