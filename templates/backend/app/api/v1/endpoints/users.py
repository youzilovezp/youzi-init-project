"""用户管理接口。"""

from fastapi import APIRouter, Query

from app.api.deps import SessionDep, SuperUser
from app.core.exceptions import BusinessError, NotFoundError
from app.crud.user import user_crud
from app.schemas.common import PageResponse, ResponseModel
from app.schemas.user import UserCreate, UserOut, UserPasswordUpdate, UserUpdate

router = APIRouter()


@router.get("", response_model=ResponseModel[PageResponse[UserOut]], summary="用户列表")
async def list_users(
    db: SessionDep,
    _user: SuperUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    username: str | None = None,
    is_active: bool | None = None,
):
    items, total = await user_crud.list_paginated(
        db, page=page, page_size=page_size, username=username, is_active=is_active
    )
    return ResponseModel(
        data=PageResponse[UserOut](
            items=[UserOut.model_validate(u) for u in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("", response_model=ResponseModel[UserOut], summary="创建用户")
async def create_user(db: SessionDep, _user: SuperUser, payload: UserCreate):
    if await user_crud.get_by_username(db, payload.username):
        raise BusinessError(code=40001, message="用户名已存在")
    user = await user_crud.create(db, payload)
    return ResponseModel(data=UserOut.model_validate(user))


@router.get("/{user_id}", response_model=ResponseModel[UserOut], summary="用户详情")
async def get_user(db: SessionDep, _user: SuperUser, user_id: int):
    user = await user_crud.get(db, user_id)
    if user is None:
        raise NotFoundError("用户不存在")
    return ResponseModel(data=UserOut.model_validate(user))


@router.put("/{user_id}", response_model=ResponseModel[UserOut], summary="更新用户")
async def update_user(
    db: SessionDep,
    user: SuperUser,
    user_id: int,
    payload: UserUpdate,
):
    target = await user_crud.get(db, user_id)
    if target is None:
        raise NotFoundError("用户不存在")
    if target.id == user.id and not user.is_superuser:
        raise BusinessError(message="不能修改自己的账号")
    updated = await user_crud.update(db, target, payload)
    return ResponseModel(data=UserOut.model_validate(updated))


@router.delete("/{user_id}", response_model=ResponseModel, summary="删除用户")
async def delete_user(db: SessionDep, user: SuperUser, user_id: int):
    if user_id == user.id:
        raise BusinessError(message="不能删除自己")
    if not await user_crud.delete(db, user_id):
        raise NotFoundError("用户不存在")
    return ResponseModel(message="已删除")


@router.post(
    "/{user_id}/password",
    response_model=ResponseModel,
    summary="修改密码（管理员）",
)
async def admin_change_password(
    db: SessionDep,
    _user: SuperUser,
    user_id: int,
    payload: UserPasswordUpdate,
):
    target = await user_crud.get(db, user_id)
    if target is None:
        raise NotFoundError("用户不存在")
    try:
        await user_crud.update_password(db, target, payload)
    except ValueError as exc:
        raise BusinessError(message=str(exc)) from exc
    return ResponseModel(message="密码已更新")
