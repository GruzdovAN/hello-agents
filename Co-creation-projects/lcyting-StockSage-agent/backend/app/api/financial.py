"""
Интеллектуальный помощник по анализу акций — маршрутизация API финансовых данных

Предоставляет финансовые показатели, профиль компании и интерфейсы запроса информации об акционерах.
"""

from fastapi import APIRouter, Query
from app.services import market_service
from app.utils.mx_http import mx_result_to_http
from app.utils.response import error_response

router = APIRouter(prefix="/financial", tags=["财务数据"])


@router.get("/indicators/{code}")
async def get_financial_indicators(
    code: str,
индикаторы: str = Query(default="Чистая прибыль, операционная прибыль, рентабельность капитала, прибыль на акцию",description="Необходимые финансовые показатели"),
):
"""Получить финансовые показатели отдельных акций

- **код**: 6-значный код акций.
- **индикаторы**: описание финансового показателя (естественный язык), например «ROE по чистой прибыли от операционной деятельности».
    """
    if not code or len(code) < 4:
        return error_response(code=400, message="请输入有效的股票代码")

    result = market_service.get_stock_financial(code, indicators)
    return mx_result_to_http(result)


@router.get("/profile/{code}")
async def get_company_profile(code: str):
"""Получить профиль компании

- **код**: 6-значный код акций.
    """
    if not code or len(code) < 4:
        return error_response(code=400, message="请输入有效的股票代码")

    result = market_service.get_stock_profile(code)
    return mx_result_to_http(result)


@router.get("/holders/{code}")
async def get_top_holders(code: str):
"""Получите информацию о десяти крупнейших акционерах

- **код**: 6-значный код акций.
    """
    if not code or len(code) < 4:
        return error_response(code=400, message="请输入有效的股票代码")

    result = market_service.get_stock_holders(code)
    return mx_result_to_http(result)
