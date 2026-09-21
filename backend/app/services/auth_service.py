"""
Authentication / authorization (section 44). Three roles: USER, ADMIN,
SUPER_ADMIN, each a strict superset of the previous one's permissions.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import Role, User
from app.utils.security import create_access_token, decode_access_token, verify_password

ROLE_HIERARCHY = {"USER": 0, "ADMIN": 1, "SUPER_ADMIN": 2}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.execute(select(User).where(User.Username == username)).scalar_one_or_none()
    if not user or not user.IsActive:
        return None
    if not verify_password(password, user.PasswordHash):
        return None
    user.LastLoginAt = datetime.now(timezone.utc)
    db.commit()
    return user


def issue_token(user: User) -> str:
    role = user.role.RoleName if user.role else "USER"
    return create_access_token(subject=user.Username, extra_claims={"role": role, "user_id": user.UserID})


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    username = payload.get("sub")
    user = db.execute(select(User).where(User.Username == username)).scalar_one_or_none()
    if not user or not user.IsActive:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_role(minimum_role: str):
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        role_name = current_user.role.RoleName if current_user.role else "USER"
        if ROLE_HIERARCHY.get(role_name, 0) < ROLE_HIERARCHY.get(minimum_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires the '{minimum_role}' role or higher.",
            )
        return current_user

    return _dependency


require_user = require_role("USER")
require_admin = require_role("ADMIN")
require_super_admin = require_role("SUPER_ADMIN")


def get_or_create_role(db: Session, role_name: str) -> Role:
    role = db.execute(select(Role).where(Role.RoleName == role_name)).scalar_one_or_none()
    if role:
        return role
    role = Role(RoleName=role_name, Description=role_name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role
