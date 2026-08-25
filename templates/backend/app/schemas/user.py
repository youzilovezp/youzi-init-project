"""用户相关 schema。"""

import unicodedata

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _sanitize_text(v: str | None) -> str | None:
    """NFKC 规范化 + 拦截 ASCII 控制字符 / BiDi 覆盖符。

    防：① admin\x00 绕过相等比较 ② 全角字符撑爆 bcrypt（1 字符 = 1 长度，但字节 4B，bcrypt O(n²)）
    ③ BiDi 控制字符（U+202E 等）混淆 UI 显示
    """
    if v is None:
        return v
    v = unicodedata.normalize("NFKC", v).strip()
    for ch in v:
        code = ord(ch)
        if (
            code < 0x20
            or code == 0x7F
            or code
            in (
                0x202A,
                0x202B,
                0x202C,
                0x202D,
                0x202E,
                0x2066,
                0x2067,
                0x2068,
                0x2069,
            )
        ):
            raise ValueError(f"包含非法控制字符 (U+{code:04X})")
    return v


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("username", "nickname", "email", "phone")
    @classmethod
    def _norm(cls, v):
        return _sanitize_text(v)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    role_id: int | None = None
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def _norm_pwd(cls, v: str) -> str:
        # 密码原样过 bcrypt，所以不规范化（保留用户原始密码）；只做控制字符拦截
        for ch in v:
            code = ord(ch)
            if code < 0x20 or code == 0x7F:
                raise ValueError("密码不能包含控制字符")
        return v


class UserUpdate(BaseModel):
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    avatar: str | None = None
    role_id: int | None = None
    is_active: bool | None = None

    @field_validator("nickname", "email", "phone")
    @classmethod
    def _norm(cls, v):
        return _sanitize_text(v)


class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _norm_pwd(cls, v: str) -> str:
        for ch in v:
            if ord(ch) < 0x20 or ord(ch) == 0x7F:
                raise ValueError("新密码不能包含控制字符")
        return v


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
    username: str = Field(min_length=3, max_length=50)
    password: str

    @field_validator("username")
    @classmethod
    def _norm(cls, v):
        return _sanitize_text(v)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
