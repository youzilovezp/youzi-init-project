"""
FastAPI 依赖注入。
"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, PermissionDeniedError
from app.core.security import decode_token
from app.crud.user import user_crud
from app.db.session import get_session
from app.models.user import User

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    db: SessionDep,
    authorization: str | None = Header(default=None),
) -> User:
    """从 Authorization 头提取 Bearer token 并解析当前用户。"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("缺少 Authorization 头")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise AuthError(str(exc)) from exc

    user_id = int(payload.get("sub", 0))
    user = await user_crud.get(db, user_id)
    if user is None or not user.is_active:
        raise AuthError("用户不存在或已被禁用")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_superuser(user: CurrentUser) -> User:
    if not user.is_superuser:
        raise PermissionDeniedError("需要超级管理员权限")
    return user


SuperUser = Annotated[User, Depends(get_current_superuser)]
