"""
Интеллектуальный помощник по анализу акций — API-маршрутизация интеллектуального выбора акций

Обеспечивает условный выбор акций и доступные интерфейсы запроса условий выбора акций.
"""

from fastapi import APIRouter, Query
from app.services import screener_service
from app.utils.mx_http import mx_result_to_http
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/screener", tags=["智能选股"])


@router.get("/conditions")
async def get_screener_conditions():
"""Получить доступную ссылку на критерии выбора акций

Возвращает классификацию измерений выбора запасов и примеры условий для внешнего отображения и справки для пользователя.
    """
    result = screener_service.get_available_conditions()
    if not result.get("success"):
        return error_response(code=500, message=result.get("error", "获取条件失败"))
    return success_response(data=result)


@router.post("/search")
async def screen_stocks(
    query: str = Query(..., description="自然语言选股条件"),
):
"""Условный выбор акций

Отбирайте акции, соответствующие условиям, на основе условий выбора акций, описанных на естественном языке.

- **запрос**: условия выбора исходного языка на естественном языке, например:
- «Акции с коэффициентом P/E менее 20 и рентабельностью капитала более 15%»
- «Акции новой энергетики с ростом более 1%»
- «10 акций с самой высокой дивидендной доходностью среди акций, входящих в CSI 300»
- «Цена меньше 20 юаней, соотношение цены и прибыли меньше 20, а рост превышает 1%.»
    """
    if not query or not query.strip():
        return error_response(code=400, message="请输入选股条件")

    result = screener_service.screen_stocks(query.strip())
    return mx_result_to_http(result)
