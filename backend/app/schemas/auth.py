from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    UserID: int
    Username: str
    Email: EmailStr
    RoleName: str
    IsActive: bool

    model_config = {"from_attributes": True}


class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role_name: str = "USER"


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    role_name: str | None = None
    is_active: bool | None = None
    password: str | None = None
