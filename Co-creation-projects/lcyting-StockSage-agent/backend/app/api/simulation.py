"""
Интеллектуальный помощник по анализу акций — маршрутизация API для имитации торговли

Предоставляет интерфейсы для моделирования запроса позиций, запроса средств, размещения доверенных заказов, отмены заказов и т. д.
"""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from app.services import simulation_service
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/simulation", tags=["模拟交易"])


class PlaceOrderRequest(BaseModel):
"""Запрос заказа"""
trade_type: str = Field(...,description="Тип сделки: покупка (покупка) / продажа (продажа)",pattern="^(buy|sell)$")
stock_code: str = Field(...,description="6-значный код акции", min_length=6, max_length=6)
    quantity: int = Field(..., description="委托数量（100的整数倍）", gt=0)
цена: Необязательно[float] = Поле(по умолчанию=Нет, описание="Цена ордера (если оставить пустым, это будет рыночный ордер)")


class CancelOrderRequest(BaseModel):
"""Запрос на отмену"""
    order_id: str = Field(..., description="委托编号", min_length=1)
    stock_code: str = Field(default="", description="股票代码（可选）")


@router.get("/portfolio")
async def get_portfolio():
"""Запрос смоделированных позиций

Возвращает все акции, хранящиеся на текущем демо-счете, а также информацию о прибылях и убытках.
    """
    result = simulation_service.get_positions()
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "查询持仓失败"))

    return success_response(
        data={
            "positions": result["positions"],
            "total": result["total"],
        },
message=f"Всего {result['total']} только удерживаемых акций",
    )


@router.get("/funds")
async def get_funds():
"""Запрос средств на демо-счете

Возвращает такую ​​информацию, как общие активы, доступные средства, замороженные средства, рыночная стоимость позиций, накопленные прибыли и убытки и т. д.
    """
    result = simulation_service.get_balance()
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "查询资金失败"))

    return success_response(
        data=result["balance"],
        message="资金查询成功",
    )


@router.get("/orders")
async def get_orders():
"""Запрос комиссионных записей

Возвращает список исторических заказов (включая статус выполненных, незавершенных, отмененных и т. д.).
    """
    result = simulation_service.get_orders()
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "查询委托失败"))

    return success_response(
        data={
            "orders": result["orders"],
            "total": result["total"],
        },
message=f"Всего {result['total']} записей комиссий",
    )


@router.post("/order")
async def place_order(body: PlaceOrderRequest):
"""Имитировать ордер (купить/продать)

Отправляйте моделируемые торговые приказы, поддерживайте лимитные и рыночные приказы.

- **trade_type**: покупка=покупка, продажа=продажа.
- **stock_code**: 6-значный код акции, например 600519.
- **количество**: количество заказа должно быть целым числом, кратным 100.
- **цена**: цена ордера (оставьте пустым = рыночная цена ордера).
    """
    result = simulation_service.place_order(
        trade_type=body.trade_type,
        stock_code=body.stock_code,
        quantity=body.quantity,
        price=body.price,
    )
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "下单失败"))

    return success_response(
        data={
            "order_id": result["order_id"],
            "trade_type": body.trade_type,
            "stock_code": body.stock_code,
            "quantity": body.quantity,
            "price": body.price,
        },
        message=result["message"],
    )


@router.delete("/order/{order_id}")
async def cancel_order(
    order_id: str,
    stock_code: str = Query(default="", description="股票代码（可选）"),
):
"""Отменить указанное делегирование

Отменить невыполненные заказы по номеру заказа.

- **order_id**: номер заказа (например, 260854300000078983).
- **stock_code**: код акции (необязательно).
    """
    result = simulation_service.cancel_order(order_id, stock_code)
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "撤单失败"))

    return success_response(data={"order_id": order_id}, message=result["message"])


@router.post("/cancel-all")
async def cancel_all_orders():
"""Отмена заказа в один клик

Отменить все невыполненные заказы по текущему счету.
    """
    result = simulation_service.cancel_all_orders()
    if not result["success"]:
        return error_response(code=500, message=result.get("error", "一键撤单失败"))

    return success_response(data={}, message=result["message"])
