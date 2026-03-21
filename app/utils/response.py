# app/utils/response.py
from typing import Any, Optional, Union
from fastapi.responses import JSONResponse


class APIResponse:
    """统一 API 响应格式"""

    @staticmethod
    def success(data: Any = None, msg: str = "success", code: int = 200) -> JSONResponse:
        """成功响应"""
        return JSONResponse(
            status_code=code,
            content={
                "code": code,
                "msg": msg,
                "data": data
            }
        )

    @staticmethod
    def error(msg: str = "error", code: int = 400, data: Any = None) -> JSONResponse:
        """错误响应"""
        return JSONResponse(
            status_code=code,
            content={
                "code": code,
                "msg": msg,
                "data": data
            }
        )

    @staticmethod
    def unauthorized(msg: str = "未授权", code: int = 401) -> JSONResponse:
        """未授权响应"""
        return JSONResponse(
            status_code=code,
            content={
                "code": code,
                "msg": msg,
                "data": None
            }
        )

    @staticmethod
    def not_found(msg: str = "资源不存在", code: int = 404) -> JSONResponse:
        """资源不存在"""
        return JSONResponse(
            status_code=code,
            content={
                "code": code,
                "msg": msg,
                "data": None
            }
        )