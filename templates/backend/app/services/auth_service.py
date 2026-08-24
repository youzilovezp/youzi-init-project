"""
认证相关业务逻辑。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthError
from app.core.security import create_access_token, verify_password
from app.crud.user import user_crud
from app.schemas.user import LoginRequest, LoginResponse, UserOut


class AuthService:
    async def login(self, db: AsyncSession, payload: LoginRequest) -> LoginResponse:
        # OAuth2PasswordRequestForm 提交时 username/password 是 bytes，统一解码
        username = (
            payload.username.decode("utf-8")
            if isinstance(payload.username, bytes)
            else payload.username
        )
        password = (
            payload.password.decode("utf-8")
            if isinstance(payload.password, bytes)
            else payload.password
        )

        user = await user_crud.get_by_username(db, username)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthError("用户名或密码错误")
        if not user.is_active:
            raise AuthError("账号已被禁用")

        token = create_access_token(
            subject=user.id,
            extra={"username": user.username, "is_superuser": user.is_superuser},
        )
        return LoginResponse(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
            user=UserOut.model_validate(user),
        )


auth_service = AuthService()
