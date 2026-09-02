"""
API истории анализа — управление историей различных аналитических отчетов.
"""

from fastapi import APIRouter, Query
from app.services import history_service
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/history", tags=["分析历史"])


@router.get("/list")
async def list_history(
type: str = Query(None,description="类型: Sentiment/data_anaанализ/buffett/chat"),
    limit: int = Query(20, ge=1, le=100),
):
"""Получить список истории"""
    result = await history_service.get_history_list(analysis_type=type, limit=limit)
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "查询失败"))
    return success_response(data={"items": result["items"], "total": result["total"]})


@router.get("/{record_id}")
async def get_history(record_id: int):
"""Получить подробности истории"""
    result = await history_service.get_history_detail(record_id)
    if not result["success"]:
        return error_response(code=404, message=result.get("error", "记录不存在"))
    return success_response(data=result["record"])


@router.delete("/{record_id}")
async def delete_history(record_id: int):
"""Удалить одну запись истории"""
    result = await history_service.delete_history(record_id)
    if not result["success"]:
        return error_response(code=404, message=result.get("error", "删除失败"))
    return success_response(message=result["message"])


@router.post("/clear")
async def clear_history(
    type: str = Query(None, description="仅清除指定类型"),
):
"""Очистить сегодняшнюю историю"""
    result = await history_service.clear_today_history(analysis_type=type)
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "清除失败"))
    return success_response(message=f"已清除 {result['count']} 条记录")
