"""
Интеллектуальный помощник по анализу запасов — маршрутизация через API управления запасами по собственному выбору

Предоставляет интерфейсы для запроса, добавления и удаления самостоятельно выбранных акций.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from app.services import watchlist_service
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/watchlist", tags=["自选股管理"])


class WatchlistAddRequest(BaseModel):
"""Добавить дискреционный запрос на акции"""
stock: str = Field(...,description="Название или код акции, например, 'Kweichow Moutai' или '600519'", min_length=1)


class WatchlistDeleteRequest(BaseModel):
"""Удалить запрос на выбор акций"""
stock: str = Field(...,description="Название или код акции, например, 'Kweichow Moutai' или '600519'", min_length=1)


@router.get("/")
async def get_watchlist():
"""Запросить список самостоятельно выбранных акций

Возвращает все дополнительные акции текущего счета и их рыночные данные.
    """
    result = watchlist_service.get_watchlist()
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "查询自选股失败"))

    return success_response(
        data={
            "stocks": result["stocks"],
            "total": result["total"],
        },
message=f"Всего {result['total']} только акции, выбранные вами самостоятельно",
    )


@router.post("/")
async def add_watchlist(body: WatchlistAddRequest):
"""Добавить дополнительные акции

Добавьте указанную акцию в список акций, выбранный вами самостоятельно.

- **stock**: название акции или 6-значный код, например «Kweichow Moutai», «600519».
    """
    if not body.stock or not body.stock.strip():
        return error_response(code=400, message="请输入股票名称或代码")

    result = watchlist_service.add_to_watchlist(body.stock.strip())
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "添加自选股失败"))

    return success_response(data=result, message=result["message"])


@router.delete("/{stock}")
async def delete_watchlist(stock: str):
"""Удалить выбранные акции

Удалите указанную акцию из списка дискреционных акций.

- **stock**: название акции или 6-значный код, например «Kweichow Moutai», «600519».
    """
    if not stock or not stock.strip():
        return error_response(code=400, message="请输入股票名称或代码")

    result = watchlist_service.delete_from_watchlist(stock.strip())
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "删除自选股失败"))

    return success_response(data=result, message=result["message"])
