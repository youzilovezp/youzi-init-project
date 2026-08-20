"""角色管理接口。"""

from fastapi import APIRouter

from app.api.deps import SessionDep, SuperUser
from app.core.exceptions import NotFoundError
from app.crud.role import role_crud
from app.schemas.common import ResponseModel
from app.schemas.role import RoleCreate, RoleOut, RoleUpdate

router = APIRouter()


@router.get("", response_model=ResponseModel[list[RoleOut]], summary="角色列表")
async def list_roles(db: SessionDep, _user: SuperUser):
    items = await role_crud.list_all(db)
    return ResponseModel(data=[RoleOut.model_validate(r) for r in items])


@router.post("", response_model=ResponseModel[RoleOut], summary="创建角色")
async def create_role(db: SessionDep, _user: SuperUser, payload: RoleCreate):
    role = await role_crud.create(db, payload)
    return ResponseModel(data=RoleOut.model_validate(role))


@router.get("/{role_id}", response_model=ResponseModel[RoleOut], summary="角色详情")
async def get_role(db: SessionDep, _user: SuperUser, role_id: int):
    role = await role_crud.get(db, role_id)
    if role is None:
        raise NotFoundError("角色不存在")
    return ResponseModel(data=RoleOut.model_validate(role))


@router.put("/{role_id}", response_model=ResponseModel[RoleOut], summary="更新角色")
async def update_role(
    db: SessionDep, _user: SuperUser, role_id: int, payload: RoleUpdate
):
    role = await role_crud.get(db, role_id)
    if role is None:
        raise NotFoundError("角色不存在")
    updated = await role_crud.update(db, role, payload)
    return ResponseModel(data=RoleOut.model_validate(updated))


@router.delete("/{role_id}", response_model=ResponseModel, summary="删除角色")
async def delete_role(db: SessionDep, _user: SuperUser, role_id: int):
    if not await role_crud.delete(db, role_id):
        raise NotFoundError("角色不存在")
    return ResponseModel(message="已删除")
