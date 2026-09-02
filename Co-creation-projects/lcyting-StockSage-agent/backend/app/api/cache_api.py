"""
API кэша стандартных файлов — поиск grep, управление кэшем, статистика данных
"""

from fastapi import APIRouter, Query
from app.services.stock_file_cache import get_stock_file_cache
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/cache", tags=["Кэш файлов"])


@router.get("/search")
async def grep_search(
    keyword: str = Query(..., description="搜索关键词"),
data_type: str = Query(None,description="Квалифицированный тип данных: цитата/финансовый/профиль/держатели/настроения"),
):
"""Содержимое файла кэша поиска в стиле Grep

Ищите ключевые слова во всех кэшированных файлах данных акций и возвращайте соответствующие результаты.
    """
    fc = get_stock_file_cache()
    results = fc.grep_search(keyword, data_type)
    return success_response(data={
        "keyword": keyword,
        "total_matches": len(results),
        "results": results,
    })


@router.get("/stock/{stock_code}")
async def get_stock_cache_info(stock_code: str):
"""Запрос состояния кэша акции"""
    fc = get_stock_file_cache()
    data_types = fc.get_stock_data_types(stock_code)
    return success_response(data={
        "stock_code": stock_code,
        "cached_types": data_types,
        "has_quote": "quote" in data_types,
        "has_financial": "financial" in data_types,
        "has_profile": "profile" in data_types,
        "has_holders": "holders" in data_types,
        "has_sentiment": "sentiment" in data_types,
    })


@router.get("/stats")
async def cache_stats():
"""Получить статистику кэша"""
    fc = get_stock_file_cache()
    return success_response(data=fc.get_stats())


@router.delete("/clear")
async def clear_cache(
    stock_code: str = Query(None, description="指定股票代码，不传则清空全部"),
):
"""Очистить кэш файлов"""
    fc = get_stock_file_cache()
    fc.clear_stock_cache(stock_code)
return Success_response(message=f"Кэш очищен{'(' + stock_code + ')' if stock_code else ''}")


@router.get("/list")
async def list_cached_stocks():
"""Перечислить все кэшированные биржевые символы"""
    fc = get_stock_file_cache()
    codes = fc.get_stock_codes()
    result = []
    for code in codes:
        types = fc.get_stock_data_types(code)
        result.append({"code": code, "data_types": types})
    return success_response(data={"stocks": result, "total": len(result)})
