from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.services.activity_log_service import log_activity
from app.services.auth_service import authenticate_user, get_current_user, issue_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        log_activity(db, "LOGIN_FAILED", status="FAILED", message=f"username={payload.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = issue_token(user)
    log_activity(db, "LOGIN", user=user, status="SUCCESS")
    role_name = user.role.RoleName if user.role else "USER"
    return TokenResponse(access_token=token, role=role_name, username=user.Username)


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return UserOut(
        UserID=current_user.UserID,
        Username=current_user.Username,
        Email=current_user.Email,
        RoleName=current_user.role.RoleName if current_user.role else "USER",
        IsActive=current_user.IsActive,
    )
