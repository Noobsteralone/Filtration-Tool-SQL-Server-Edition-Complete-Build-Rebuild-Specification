"""User / role management -- Super Admin only (section 44)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreateRequest, UserOut, UserUpdateRequest
from app.services.activity_log_service import log_activity
from app.services.auth_service import get_or_create_role, require_super_admin
from app.utils.security import hash_password

router = APIRouter(prefix="/api/users", tags=["users"])


def _to_out(user: User) -> UserOut:
    return UserOut(
        UserID=user.UserID,
        Username=user.Username,
        Email=user.Email,
        RoleName=user.role.RoleName if user.role else "USER",
        IsActive=user.IsActive,
    )


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_super_admin)):
    users = db.execute(select(User)).scalars().all()
    return [_to_out(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db), current=Depends(require_super_admin)):
    existing = db.execute(select(User).where(User.Username == payload.username)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    role = get_or_create_role(db, payload.role_name)
    from datetime import datetime, timezone

    user = User(
        Username=payload.username,
        Email=payload.email,
        PasswordHash=hash_password(payload.password),
        RoleID=role.RoleID,
        IsActive=True,
        CreatedAt=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_activity(db, "USER_CREATED", user=current, entity_type="USER", entity_id=user.UserID)
    return _to_out(user)


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdateRequest, db: Session = Depends(get_db), current=Depends(require_super_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.email is not None:
        user.Email = payload.email
    if payload.is_active is not None:
        user.IsActive = payload.is_active
    if payload.role_name is not None:
        role = get_or_create_role(db, payload.role_name)
        user.RoleID = role.RoleID
    if payload.password:
        user.PasswordHash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    log_activity(db, "USER_UPDATED", user=current, entity_type="USER", entity_id=user.UserID)
    return _to_out(user)
