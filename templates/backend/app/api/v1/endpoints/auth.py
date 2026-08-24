"""登录/登出/当前用户信息。

端点接受两种 content-type：
- application/json          —— 前端 axios 默认走这个
- application/x-www-form-urlencoded —— Swagger UI Authorize 用

通过 Request.headers['content-type'] 显式分支。
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.core.exceptions import AuthError
from app.schemas.common import ResponseModel
from app.schemas.user import LoginRequest, LoginResponse, UserOut
from app.services.auth_service import auth_service

router = APIRouter()


class LoginJSON(BaseModel):
    """JSON 登录（前端 axios 默认走这个）。"""

    username: str
    password: str


async def _read_form(request: Request):
    """读 form-encoded body；bytes 字段转 str。"""
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    if username is None or password is None:
        raise AuthError("缺少 username 或 password")
    return LoginRequest(
        username=username.decode("utf-8") if isinstance(username, bytes) else username,
        password=password.decode("utf-8") if isinstance(password, bytes) else password,
    )


@router.post("/login", response_model=ResponseModel[LoginResponse], summary="登录")
async def login(db: SessionDep, request: Request):
    """根据 Content-Type 分发：JSON → LoginJSON；form-urlencoded → form。"""
    content_type = (request.headers.get("content-type") or "").lower()

    if "application/json" in content_type:
        body = await request.json()
        json_body = LoginJSON(**body)
        payload = LoginRequest(username=json_body.username, password=json_body.password)
    elif (
        "application/x-www-form-urlencoded" in content_type
        or "multipart/form-data" in content_type
    ):
        payload = await _read_form(request)
    else:
        raise AuthError("不支持的 Content-Type")

    data = await auth_service.login(db, payload)
    return ResponseModel(data=data)


@router.get("/me", response_model=ResponseModel[UserOut], summary="当前用户信息")
async def me(user: CurrentUser):
    return ResponseModel(data=UserOut.model_validate(user))


@router.post("/logout", response_model=ResponseModel, summary="登出")
async def logout():
    # JWT 无状态，前端清除 token 即可；如需黑名单可在此向 Redis 写入
    return ResponseModel(message="已退出")
