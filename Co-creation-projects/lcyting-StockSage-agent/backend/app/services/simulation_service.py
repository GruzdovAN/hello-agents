"""
Интеллектуальный помощник по анализу акций — уровень имитации торгового сервиса

Инкапсулируйте моделируемые торговые операции (запрос позиции, запрос фонда, доверенное размещение заказа, отмену заказа и т. д.) для вызовов уровня маршрутизации API.
"""

import sys
from pathlib import Path
from typing import Optional

# Убедитесь, что путь навыков можно импортировать
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # backend/app/services -> project root
_AGENTS_DIR = _PROJECT_ROOT / "agents"
_SKILLS_MONI = _PROJECT_ROOT / "skills" / "模拟组合管理" / "mx-moni"

for p in [_AGENTS_DIR, _SKILLS_MONI, str(_PROJECT_ROOT)]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import requests
from app.config import settings
from app.utils.mock_trading_normalize import extract_orders_dicts, normalize_mock_order_row

# базовый адрес API
MX_API_URL = "https://mkapi2.dfcfs.com/finskillshub"


def _make_request(endpoint: str, body: dict) -> dict:
"""Отправить запрос API имитации торговли

    Args:
конечная точка: путь к конечной точке API
тело: тело запроса

    Returns:
Ответ API в формате JSON
    """
    headers = {
        "apikey": settings.MX_APIKEY,
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{MX_API_URL}{endpoint}",
        headers=headers,
        json=body,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _check_api_ready() -> Optional[dict]:
    """检查API是否就绪，未就绪返回错误字典"""
    if not settings.MX_APIKEY or settings.MX_APIKEY == "your-mx-apikey-here":
        return {"error": "MX_APIKEY 未配置"}
    return None


def get_positions() -> dict:
"""Запрос смоделированных позиций

    Returns:
        {
            "success": True/False,
            "positions": [{"code": str, "name": str, "quantity": int, ...}, ...],
            "total": int,
            "error": str or None
        }
    """
    result = {
        "success": False,
        "positions": [],
        "total": 0,
        "error": None,
    }

    api_error = _check_api_ready()
    if api_error:
        result["error"] = api_error["error"]
        return result

    try:
        raw = _make_request("/api/claw/mockTrading/positions", {"moneyUnit": 1})

        if not raw.get("success") and str(raw.get("code")) != "200":
            result["error"] = raw.get("message", "查询持仓失败")
            return result

        data = raw.get("data", {})
        positions = data.get("positions", [])

        parsed = []
        for pos in (positions or []):
            parsed.append({
                "stock_code": pos.get("stockCode", ""),
                "stock_name": pos.get("stockName", ""),
                "quantity": pos.get("quantity", 0),
                "cost_price": pos.get("costPrice", 0),
                "current_price": pos.get("currentPrice", 0),
                "profit_loss": pos.get("profitLoss", 0),
                "profit_loss_rate": pos.get("profitLossRate", 0),
                "market_value": pos.get("marketValue", 0),
            })

        result["success"] = True
        result["positions"] = parsed
        result["total"] = len(parsed)
        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def get_balance() -> dict:
"""Запрос средств на демо-счете

    Returns:
        {
            "success": True/False,
            "balance": {...},
            "error": str or None
        }
    """
    result = {
        "success": False,
        "balance": {},
        "error": None,
    }

    api_error = _check_api_ready()
    if api_error:
        result["error"] = api_error["error"]
        return result

    try:
        raw = _make_request("/api/claw/mockTrading/balance", {"moneyUnit": 1})

        if not raw.get("success") and str(raw.get("code")) != "200":
            result["error"] = raw.get("message", "查询资金失败")
            return result

        data = raw.get("data", {})
        result["success"] = True
        result["balance"] = {
            "total_assets": data.get("totalAssets", 0),
            "available_balance": data.get("availBalance", 0),
            "frozen_balance": data.get("frozenBalance", 0),
            "market_value": data.get("marketValue", 0),
            "total_profit_loss": data.get("totalProfitLoss", 0),
        }
        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def get_orders() -> dict:
"""Запрос комиссионных записей

    Returns:
        {
            "success": True/False,
            "orders": [...],
            "total": int,
            "error": str or None
        }
    """
    result = {
        "success": False,
        "orders": [],
        "total": 0,
        "error": None,
    }

    api_error = _check_api_ready()
    if api_error:
        result["error"] = api_error["error"]
        return result

    try:
        raw = _make_request("/api/claw/mockTrading/orders", {
            "fltOrderDrt": 0,
            "fltOrderStatus": 0,
        })

        if not raw.get("success") and str(raw.get("code")) != "200":
            result["error"] = raw.get("message", "查询委托失败")
            return result

        data = raw.get("data", {}) or {}
# Miaoxiang может возвращать список, или { rows: [] }, или поле текущего дня/сегмента истории
        orders = extract_orders_dicts(data)

        parsed = []
        for order in orders:
            if not isinstance(order, dict):
                continue
# Унифицированный анализ названий полей и перечислений (числовое направление покупки и продажи, статус комиссии и т. д.)
            parsed.append(normalize_mock_order_row(order))

        result["success"] = True
        result["orders"] = parsed
        result["total"] = len(parsed)
        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def place_order(
    trade_type: str,
    stock_code: str,
    quantity: int,
    price: Optional[float] = None,
) -> dict:
"""Имитировать ордер (купить/продать)

    Args:
trade_type: тип транзакции «покупка» или «продажа»
stock_code: 6-значный код акции
количество: количество заказа (должно быть целым числом, кратным 100).
цена: цена ордера (Нет указывает на рыночную цену ордера)

    Returns:
        {
            "success": True/False,
            "order_id": str,
            "message": str,
            "error": str or None
        }
    """
    result = {
        "success": False,
        "order_id": "",
        "message": "",
        "error": None,
    }

# Проверка параметров
    if trade_type not in ("buy", "sell"):
result["error"] = "Неверный тип транзакции, используйте покупку или продажу"
        return result

    if not stock_code or len(str(stock_code)) < 6:
result["error"] = "Пожалуйста, введите действительный 6-значный код акции"
        return result

    if quantity <= 0:
result["error"] = "Количество комиссий должно быть больше 0"
        return result

    if quantity % 100 != 0:
result["error"] = "Количество транзакций с акциями A должно быть целым кратным 100 акциям"
        return result

    api_error = _check_api_ready()
    if api_error:
        result["error"] = api_error["error"]
        return result

    try:
        body = {
            "type": trade_type,
            "stockCode": str(stock_code),
            "quantity": int(quantity),
            "useMarketPrice": price is None,
        }
        if price is not None:
            body["price"] = float(price)

        raw = _make_request("/api/claw/mockTrading/trade", body)

        if not raw.get("success") and str(raw.get("code")) != "200":
            result["error"] = raw.get("message", "下单失败")
            return result

        data = raw.get("data", {})
        order_id = data.get("orderId", "")

        result["success"] = True
        result["order_id"] = order_id
        direction_cn = "买入" if trade_type == "buy" else "卖出"
        price_info = f"@{price}元" if price else "市价"
result["message"] = f"Заказ {direction_cn} отправлен: {stock_code} {quantity} акций {price_info}"
        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def cancel_order(order_id: str, stock_code: str = "") -> dict:
"""Отменить заказ

    Args:
order_id: номер заказа
        stock_code: 股票代码（可选）

    Returns:
        {
            "success": True/False,
            "message": str,
            "error": str or None
        }
    """
    result = {
        "success": False,
        "message": "",
        "error": None,
    }

    if not order_id:
result["error"] = "Укажите номер комиссии"
        return result

    api_error = _check_api_ready()
    if api_error:
        result["error"] = api_error["error"]
        return result

    try:
        body = {
            "type": "order",
            "orderId": str(order_id),
        }
        if stock_code:
            body["stockCode"] = str(stock_code)

        raw = _make_request("/api/claw/mockTrading/cancel", body)

        if not raw.get("success") and str(raw.get("code")) != "200":
            result["error"] = raw.get("message", "撤单失败")
            return result

        result["success"] = True
result["message"] = f"Делегирование {order_id} отозвано"
        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def cancel_all_orders() -> dict:
"""Отмена заказов одним кликом (отмена всех невыполненных заказов)

    Returns:
        {
            "success": True/False,
            "message": str,
            "error": str or None
        }
    """
    result = {
        "success": False,
        "message": "",
        "error": None,
    }

    api_error = _check_api_ready()
    if api_error:
        result["error"] = api_error["error"]
        return result

    try:
        raw = _make_request("/api/claw/mockTrading/cancel", {"type": "all"})

        if not raw.get("success") and str(raw.get("code")) != "200":
            result["error"] = raw.get("message", "一键撤单失败")
            return result

        result["success"] = True
result["message"] = "Все невыполненные заказы отменены"
        return result

    except Exception as e:
        result["error"] = str(e)
        return result
