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


def _coerce_to_str(value: object) -> object:
    """把异常信息里的 bytes / 嵌套结构统一转换为 JSON 安全的类型。
    否则 `bytes is not JSON serializable` 会让 500 退化成 500 的再 500。
    """
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return repr(value)
    if isinstance(value, dict):
        return {k: _coerce_to_str(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_coerce_to_str(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


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
        # exc.errors() 可能含 bytes（如 form-encoded body 失败时），必须 coerce
        safe_errors = _coerce_to_str(exc.errors())
        return JSONResponse(
            status_code=422,
            content=_wrap(42200, "参数校验失败", safe_errors),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        msg = str(exc)
        safe_msg = _coerce_to_str(msg)
        return JSONResponse(
            status_code=500,
            content=_wrap(50000, f"服务器内部错误: {safe_msg}"),
        )
