"""
Интеллектуальный помощник по анализу запасов — маршрутизация API поиска информации

Обеспечивает поиск финансовой информации, анализ общественного мнения по отдельным акциям и популярные интерфейсы запроса информации.
"""

from fastapi import APIRouter, Query
from app.services import news_service
from app.utils.mx_http import mx_result_to_http
from app.utils.response import error_response

router = APIRouter(prefix="/news", tags=["поиск информации"])


@router.get("/search")
async def search_news(
    query: str = Query(..., description="自然语言搜索问句"),
):
"""Поиск финансовой информации

    - **query**: 自然语言搜索问句，如 "人工智能板块近期新闻"、"贵州茅台最新研报"
    """
    if not query or not query.strip():
        return error_response(code=400, message="请输入搜索内容")

    result = news_service.search_news(query.strip())
    return mx_result_to_http(result)


@router.get("/sentiment/{code}")
async def get_stock_sentiment(code: str):
"""Получить анализ общественного мнения по отдельным акциям

Ищите новости, отчеты об исследованиях и объявления, связанные с акциями, по коду акции и сортируйте их по категориям.

    - **code**: 6位股票代码，如 600519（贵州茅台）、000001（平安银行）
    """
    if not code or len(code) < 4:
        return error_response(code=400, message="请输入有效的股票代码")

    result = news_service.analyze_sentiment(code)
    return mx_result_to_http(result)


@router.get("/hot")
async def get_hot_news():
"""Получите актуальную рыночную информацию

Вернитесь к обзору сегодняшних горячих тем рынка акций А, потоков капитала на север и другой информации.
    """
    result = news_service.search_market_news()
    return mx_result_to_http(result)
