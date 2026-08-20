"""
统一异常体系与全局异常处理。
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class BusinessError(Exception):
    """业务异常基类。

    使用方式：
        raise BusinessError(code=40001, message="用户名已存在")
    """

    def __init__(self, code: int = 40000, message: str = "业务异常", data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class NotFoundError(BusinessError):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=40400, message=message)


class AuthError(BusinessError):
    def __init__(self, message: str = "认证失败"):
        super().__init__(code=40100, message=message)


class PermissionDeniedError(BusinessError):
    def __init__(self, message: str = "权限不足"):
        super().__init__(code=40300, message=message)


def _wrap(code: int, message: str, data=None) -> dict:
    return {"code": code, "message": message, "data": data}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessError)
    async def business_handler(_: Request, exc: BusinessError) -> JSONResponse:
        return JSONResponse(
            status_code=200, content=_wrap(exc.code, exc.message, exc.data)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_wrap(42200, "参数校验失败", exc.errors()),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        # 生产环境不要回显堆栈
        return JSONResponse(
            status_code=500,
            content=_wrap(50000, f"服务器内部错误: {exc!s}"),
        )
