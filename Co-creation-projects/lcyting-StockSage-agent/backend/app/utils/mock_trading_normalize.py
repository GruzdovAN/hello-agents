"""
Имитированная торговля Miaoxiang — стандартизация полей списка заказов

上游 `/api/claw/mockTrading/orders` 返回的字段名与取值在不同版本间可能不一致：
- Направление покупки и продажи может быть числовым значением (например, 1 = покупка, 2 = продажа) вместо строки покупки/продажи.
- Статус делегирования в основном представляет собой числовое перечисление, которое необходимо сопоставить с ожидающими/выполненными и т. д., доступными во внешнем интерфейсе.
- Код, имя, номер заказа, время и т. д. могут иметь Snake_case или другие псевдонимы.

Здесь мы сосредоточимся на анализе совместимости для совместного использования инструментов Simulation_service и Agent.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional


def extract_orders_dicts(data: Any) -> list[dict[str, Any]]:
    """从妙想 data 中取出委托对象列表（兼容 list、或 { rows/list/... } 包裹）。"""
    if not isinstance(data, Mapping):
        return []

    def coerce_dict_list(raw: Any) -> list[dict[str, Any]]:
        if raw is None:
            return []
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, dict)]
        if isinstance(raw, dict):
            for inner_key in ("rows", "records", "list", "items", "data"):
                inner = raw.get(inner_key)
                if isinstance(inner, list):
                    return [x for x in inner if isinstance(x, dict)]
        return []

# Установите приоритет для отдельных полей списка (чтобы избежать многократного объединения нескольких фрагментов)
    for key in ("orders", "orderList", "list", "entrustList"):
        chunk = coerce_dict_list(data.get(key))
        if chunk:
            return chunk

# Объединить текущий день + исторические сегменты при возврате (только когда верхний уровень не дает единых ордеров)
    merged: list[dict[str, Any]] = []
    for key in ("todayOrders", "today_order_list", "historyOrders", "hisOrders"):
        merged.extend(coerce_dict_list(data.get(key)))
    return merged


def _first(d: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
"""Получить первое ненулевое значение слева направо (нет/пустая строка пропускается)."""
    for k in keys:
        if k not in d:
            continue
        v = d[k]
        if v is None or v == "":
            continue
        return v
    return None


def _nested_stock(order: Mapping[str, Any]) -> Mapping[str, Any]:
"""Часть ответа помещает информацию о ценных бумагах в подобъект."""
    for k in ("stock", "security", "stockInfo"):
        sub = order.get(k)
        if isinstance(sub, Mapping):
            return sub
    return {}


def parse_trade_type(order: Mapping[str, Any]) -> str:
    """解析为 'buy' 或 'sell'（妙想常见：数值 1=买入，2=卖出）。"""
    # 关键：不能用「第一个非空字段」—— tradeType/trade_type 常为委托类别(如 5)，
    # 真正的买卖方向在 orderDrt/orderBs 等字段，必须逐个尝试直到解析成功。
    dir_keys = (
        "orderDrt",
        "orderBs",
        "orderDirection",
        "bsFlag",
        "bsType",
        "entrustBs",
        "mmlx",
        "direction",
        "side",
        "tradeType",
        "trade_type",
    )
    nested = _nested_stock(order)

    def norm(val: Any) -> Optional[str]:
        if val is None:
            return None
        if isinstance(val, bool):
            return None
        if isinstance(val, (int, float)):
            iv = int(val)
# Восточная система богатства является общей: 1 покупка, 2 продажа.
            if iv == 1:
                return "buy"
            if iv == 2:
                return "sell"
            return None
        s = str(val).strip().lower()
if s in ("купить", "b", "1", "КУПИТЬ", "КУПИТЬ"):
            return "buy"
if s in ("продать", "s", "2", "продать", "продать"):
            return "sell"
        return None

    for src in (order, nested):
        for k in dir_keys:
            if k not in src:
                continue
            val = src[k]
            if val is None or val == "":
                continue
            parsed = norm(val)
            if parsed:
                return parsed

# тип: Некоторые интерфейсы представляют покупку и продажу; они также могут быть бизнес-типами, такими как предельная цена/рыночная цена, поэтому они используются только тогда, когда их можно идентифицировать.
    for src in (order, nested):
        t_raw = src.get("type")
        parsed_t = norm(t_raw)
        if parsed_t:
            return parsed_t

    return ""


def parse_order_status(order: Mapping[str, Any]) -> tuple[str, str]:
    """
Возврат (canonical_status, chinese_label).

canonical используется для логики отмены заказа: ожидание / выполнено / part_deal / отменено / неизвестно.
    """
    nested = _nested_stock(order)
    status_keys = (
        "status",
        "order_status",
        "orderStatus",
        "entrustStatus",
        "wtStatus",
        "dealStatus",
    )

    def to_canonical_and_label(val: Any) -> tuple[str, str]:
        if val is None:
вернуть «неизвестно», «неизвестно»
        if isinstance(val, str):
            sl = val.strip().lower()
            known = {
"pending": ("pending", "Untransacted"),
"незаполнено": ("ожидает", "незаполнено"),
"open": ("ожидание", "Нетранзакция"),
"сделано": ("сделано", "сделано"),
"заполнено": ("выполнено", "сдано"),
"успех": ("сделано", "сделано"),
                "part_deal": ("part_deal", "部分成交"),
                "partial": ("part_deal", "部分成交"),
"отменено": ("отменено", "отменено"),
"отменено": ("отменено", "отменено"),
"снято": ("отменено", "снято"),
            }
            if sl in known:
                return known[sl]
# Уже на китайском языке и т. д.: считать его неизвестным, но сохранить исходное текстовое отображение.
            if sl.isdigit():
                return to_canonical_and_label(int(sl))
            return "unknown", str(val)

        try:
            iv = int(val)
        except (TypeError, ValueError):
            return "unknown", str(val)

# Общие коды статуса брокерской комиссии (консервативное отображение, отображается «статус {n}», если он не покрыт)
        mapping: dict[int, tuple[str, str]] = {
0: («ожидание», «ожидающий отчет/ожидающая транзакция»),
1: («ожидание», «Незавершенная сделка»),
2: ("part_deal", "Частичная сделка"),
3: («Готово», «Раздано»),
4: ("part_deal", "Часть становится частью, часть уходит"),
5: («отменено», «отменено»),
6: («отменено», «отменено»),
7: («сделано», «сделка»),
8: («отменен», «отмененный заказ»),
        }
        if iv in mapping:
            return mapping[iv]
вернуть «неизвестно», f»status{iv}»

    for src in (order, nested):
        for k in status_keys:
            if k not in src:
                continue
            val = src[k]
            if val is None or val == "":
                continue
            return to_canonical_and_label(val)

    return to_canonical_and_label(None)


def normalize_mock_order_row(order: Mapping[str, Any]) -> dict[str, Any]:
"""Преобразовать единое исходное делегирование в единую структуру, используемую интерфейсом/маршрутизацией."""
    nested = _nested_stock(order)

    order_id = _first(
        order,
        (
            "orderId",
            "order_id",
            "orderNo",
            "orderNO",
            "wtOrderId",
            "entrustId",
            "wth",
            "wtbh",
            "contractId",
            "id",
        ),
    )
    stock_code = _first(
        order,
        ("stockCode", "stock_code", "securityCode", "zqdm", "scode", "code", "stockcode"),
    )
    if stock_code is None:
        stock_code = _first(nested, ("stockCode", "stock_code", "securityCode", "zqdm", "code"))

    stock_name = _first(order, ("stockName", "stock_name", "name", "sname", "securityName"))
    if stock_name is None:
        stock_name = _first(nested, ("stockName", "stock_name", "name"))

    price_raw = _first(
        order,
        ("price", "wtjg", "orderPrice", "order_price", "entrustPrice", "limitPrice", "wtPrice"),
    )
    try:
        price = float(price_raw) if price_raw is not None else 0.0
    except (TypeError, ValueError):
        price = 0.0

    qty_raw = _first(
        order,
        (
            "quantity",
            "wtVolume",
            "wtVol",
            "wtvol",
            "orderQty",
            "order_qty",
            "orderVolume",
            "vol",
            "volume",
            "stockNum",
            "entrustAmount",
        ),
    )
    try:
        quantity = int(qty_raw) if qty_raw is not None else 0
    except (TypeError, ValueError):
        quantity = 0

    create_time = _first(
        order,
        (
            "createTime",
            "create_time",
            "orderTime",
            "order_time",
            "entrustTime",
            "reportTime",
            "tradeTime",
            "wtTime",
            "report_time",
        ),
    )
    if create_time is None:
        create_time = _first(nested, ("createTime", "create_time"))

    trade_type = parse_trade_type(order)
    status, status_text = parse_order_status(order)

    return {
        "order_id": str(order_id) if order_id is not None else "",
        "stock_code": str(stock_code) if stock_code is not None else "",
        "stock_name": str(stock_name) if stock_name is not None else "",
        "trade_type": trade_type,
        "price": price,
        "quantity": quantity,
        "status": status,
        "status_text": status_text,
        "create_time": str(create_time) if create_time is not None else "",
    }
