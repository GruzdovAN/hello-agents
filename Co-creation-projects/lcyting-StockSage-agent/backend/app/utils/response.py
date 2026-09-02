"""
Интеллектуальный помощник по анализу запасов — модуль единого формата ответов

Определите стандартную структуру ответа API, чтобы обеспечить согласованность форматов данных внешнего и внутреннего интерфейса.
"""

from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
"""Единый формат ответа API"""

    code: int = 0  # 状态码：0=成功，非0=错误
    message: str = "success"  # 提示信息
data: Необязательный[Любой] = Нет # Данные ответа

    class Config:
        json_schema_extra = {
            "example": {
                "code": 0,
                "message": "success",
                "data": {"stock_code": "600519", "price": 1700.00},
            }
        }


class PageResponse(BaseModel):
"""Формат ответа API разбиения на страницы"""

    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
нумерация страниц: Необязательно[dict] = Нет # Информация о нумерации страниц {page, page_size, total, total_pages}

    class Config:
        json_schema_extra = {
            "example": {
                "code": 0,
                "message": "success",
                "data": [],
                "pagination": {"page": 1, "page_size": 20, "total": 100, "total_pages": 5},
            }
        }


def success_response(data: Any = None, message: str = "success", meta: Any = None) -> dict:
    """快速构建成功响应；meta 用于妙想缓存/额度提示等扩展字段"""
    out: dict = {"code": 0, "message": message, "data": data}
    if meta is not None:
        out["meta"] = meta
    return out


def error_response(code: int, message: str, data: Any = None) -> dict:
    """快速构建错误响应"""
    return APIResponse(code=code, message=message, data=data).model_dump()


def page_response(data: Any, page: int, page_size: int, total: int) -> dict:
"""Быстро создавайте ответы с разбивкой на страницы"""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PageResponse(
        code=0,
        data=data,
        pagination={"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
    ).model_dump()
