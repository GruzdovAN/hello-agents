"""
Интеллектуальный помощник по анализу запасов — самостоятельно выбираемый уровень службы управления запасами

Инкапсулирует логику запроса данных для запроса, добавления и удаления самостоятельно выбранных акций для вызовов уровня маршрутизации API.
"""

import sys
from pathlib import Path
# Убедитесь, что путь навыков можно импортировать
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # backend/app/services -> project root
_AGENTS_DIR = _PROJECT_ROOT / "agents"
_SKILLS_ZIXUAN = _PROJECT_ROOT / "skills" / "自选股管理" / "mx-zixuan"

for p in [_AGENTS_DIR, _SKILLS_ZIXUAN, str(_PROJECT_ROOT)]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.config import settings
from app.services.mx_timed_cache import get_mx_timed_cache, mx_cache_ttl_seconds

# 与 mx_data / mx_search 共用 TTL（默认 600s）：逾时才再打妙想侧自选接口
_WATCHLIST_CACHE_QUERY = "mx_zixuan_self_select_list"


def _watchlist_cache_key() -> str:
    return get_mx_timed_cache().make_key("mx_zixuan", _WATCHLIST_CACHE_QUERY)


def _invalidate_watchlist_cache() -> None:
    get_mx_timed_cache().delete(_watchlist_cache_key())


def _get_mx_zixuan_instance():
"""Создать экземпляр вызова API mx_zixuan"""
    import mx_zixuan as _mx
    return _mx


def get_watchlist() -> dict:
"""Запросить список самостоятельно выбранных акций

    Returns:
        {
            "success": True/False,
            "stocks": [{"code": str, "name": str, "price": float, ...}, ...],
            "total": int,
            "error": str or None
        }
    """
    import mx_zixuan as _mx

    ttl = mx_cache_ttl_seconds()
    if ttl > 0:
        cached = get_mx_timed_cache().get_fresh(_watchlist_cache_key(), ttl)
        if cached is not None:
            return cached

    result = {
        "success": False,
        "stocks": [],
        "total": 0,
        "error": None,
    }

    if not settings.MX_APIKEY or settings.MX_APIKEY == "your-mx-apikey-here":
        result["error"] = "MX_APIKEY 未配置"
        return result

    try:
        raw_result = _mx.query_self_select(settings.MX_APIKEY)

# Проверьте статус API
        status = raw_result.get("status", -1)
        code = raw_result.get("code", -1)
        if status != 0 and code != 0:
            result["error"] = raw_result.get("message", "查询自选股失败")
            return result

# Анализ результатов запроса
        data = raw_result.get("data", {})
        all_results = data.get("allResults", {})
        result_data = all_results.get("result", {})
        data_list = result_data.get("dataList", [])

        stocks = []
        for stock in (data_list or []):
            stocks.append({
                "code": stock.get("SECURITY_CODE", ""),
                "name": stock.get("SECURITY_SHORT_NAME", ""),
                "price": stock.get("NEWEST_PRICE", ""),
                "change_pct": stock.get("CHG", ""),
                "change_amount": stock.get("PCHG", ""),
                "turnover_rate": stock.get("010000_TURNOVER_RATE", ""),
                "volume_ratio": stock.get("010000_LIANGBI", ""),
            })

        result["success"] = True
        result["stocks"] = stocks
        result["total"] = len(stocks)
        if ttl > 0:
            get_mx_timed_cache().set(_watchlist_cache_key(), result)
        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def add_to_watchlist(stock_input: str) -> dict:
"""Добавить акции в дополнительные акции

    Args:
stock_input: название или код акции, например «Kweichow Moutai» или «600519».

    Returns:
        {
            "success": True/False,
            "message": str,
            "error": str or None
        }
    """
    import mx_zixuan as _mx

    result = {
        "success": False,
        "message": "",
        "error": None,
    }

    if not settings.MX_APIKEY or settings.MX_APIKEY == "your-mx-apikey-here":
        result["error"] = "MX_APIKEY 未配置"
        return result

    try:
#Construct добавление инструкций на естественном языке
query = f"Добавить {stock_input} в мой список выбора акций"
        raw_result = _mx.manage_self_select(settings.MX_APIKEY, query)

        status = raw_result.get("status", -1)
        code = raw_result.get("code", -1)
        if status != 0 and code != 0:
            result["error"] = raw_result.get("message", "添加自选股失败")
            return result

        result["success"] = True
result["message"] = raw_result.get("message", f"{stock_input} добавлен в ваш выбор")
        _invalidate_watchlist_cache()
        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def delete_from_watchlist(stock_input: str) -> dict:
"""Удалить акции из дискреционных акций

    Args:
stock_input: название или код акции, например «Kweichow Moutai» или «600519».

    Returns:
        {
            "success": True/False,
            "message": str,
            "error": str or None
        }
    """
    import mx_zixuan as _mx

    result = {
        "success": False,
        "message": "",
        "error": None,
    }

    if not settings.MX_APIKEY or settings.MX_APIKEY == "your-mx-apikey-here":
        result["error"] = "MX_APIKEY 未配置"
        return result

    try:
# Создание инструкций удаления на естественном языке
query = f"Удалить {stock_input} из моего списка выбора акций"
        raw_result = _mx.manage_self_select(settings.MX_APIKEY, query)

        status = raw_result.get("status", -1)
        code = raw_result.get("code", -1)
        if status != 0 and code != 0:
            result["error"] = raw_result.get("message", "删除自选股失败")
            return result

        result["success"] = True
result["message"] = raw_result.get("message", f"{stock_input} удален из выбора")
        _invalidate_watchlist_cache()
        return result

    except Exception as e:
        result["error"] = str(e)
        return result
