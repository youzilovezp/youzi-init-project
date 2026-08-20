"""登录/登出/当前用户信息。"""

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.schemas.common import ResponseModel
from app.schemas.user import LoginRequest, LoginResponse, UserOut
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/login", response_model=ResponseModel[LoginResponse], summary="登录")
async def login(db: SessionDep, payload: LoginRequest):
    data = await auth_service.login(db, payload)
    return ResponseModel(data=data)


@router.get("/me", response_model=ResponseModel[UserOut], summary="当前用户信息")
async def me(user: CurrentUser):
    return ResponseModel(data=UserOut.model_validate(user))


@router.post("/logout", response_model=ResponseModel, summary="登出")
async def logout():
    # JWT 无状态，前端清除 token 即可；如需黑名单可在此向 Redis 写入
    return ResponseModel(message="已退出")
