"""
认证相关业务逻辑。
"""

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthError
from app.core.security import create_access_token, verify_password
from app.crud.user import user_crud
from app.schemas.user import LoginRequest, LoginResponse, UserOut


class AuthService:
    async def login(self, db: AsyncSession, payload: LoginRequest) -> LoginResponse:
        user = await user_crud.get_by_username(db, payload.username)
        if user is None or not verify_password(payload.password, user.password_hash):
            logger.warning("auth.login.fail username={}", payload.username)
            raise AuthError("用户名或密码错误")
        if not user.is_active:
            raise AuthError("账号已被禁用")

        token = create_access_token(
            subject=user.id,
            extra={"username": user.username, "is_superuser": user.is_superuser},
        )
        logger.info("auth.login.ok user_id={} username={}", user.id, user.username)
        return LoginResponse(
            access_token=token,
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            user=UserOut.model_validate(user),
        )


auth_service = AuthService()
