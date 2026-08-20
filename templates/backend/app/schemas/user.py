"""用户相关 schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    nickname: str | None = None
    email: EmailStr | None = None
    phone: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    role_id: int | None = None
    is_active: bool = True


class UserUpdate(BaseModel):
    nickname: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    avatar: str | None = None
    role_id: int | None = None
    is_active: bool | None = None


class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)


class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    avatar: str | None
    role_id: int | None
    role_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
