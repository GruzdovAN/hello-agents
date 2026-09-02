"""
Интеллектуальный помощник по анализу акций — API-интерфейс Buffett Investment Evaluation

Предоставляет интерфейсы запроса структуры инвестиций Баффета и оценки инвестиций.
"""

import asyncio
import json

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services import buffett_service
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/buffett", tags=["巴菲特投资评估"])


class BuffettEvaluateRequest(BaseModel):
"""Запрос на оценку инвестиций Баффета"""
stock_code: str = Field(...,description="6-значный код акции", min_length=4, max_length=10)
    stock_name: str = Field(default="", description="股票名称（可选）")
    include_market: bool = Field(default=True, description="是否包含行情数据")
include_financial: bool = Field(default=True,description="Включать ли финансовые данные")


@router.get("/framework")
async def get_buffett_framework():
"""Получите систему оценки инвестиций Баффета.

Вернитесь к полной системе мышления Баффета в области стоимостного инвестирования, включая:
- Контрольный список из 8 вопросов для быстрой проверки
- Пять типов анализа рва
- Три измерения управленческой оценки
- Шаблоны финансовых показателей (ROIC, доходы владельцев, коэффициент конверсии денежных средств)
- Методы оценки и запас прочности.
- Классификация оценки риска
- Четыре критерия продажи
    """
    result = buffett_service.get_buffett_framework()
    return success_response(
        data={
            "framework": result["framework"],
            "description": result["description"],
        },
message="Система оценки инвестиций Баффета готова",
    )


@router.post("/evaluate")
async def evaluate_stock(body: BuffettEvaluateRequest):
«»»Используйте инвестиционную структуру Баффета для оценки акций

Создайте контекст оценки стоимостных инвестиций в стиле Баффета, возвращая структурированные шаблоны оценки и системы отсчета.

- **stock_code**: 6-значный код акции, например 600519 (Квейчоу Мутай).
- **stock_name**: название акции (необязательно, используется в заголовке отчета).
- **include_market**: пытаться ли получить рыночные данные.
- **include_financial**: следует ли пытаться получить финансовые данные.
    """
    if not body.stock_code or len(body.stock_code.strip()) < 4:
        return error_response(code=400, message="请输入有效的股票代码")

    # 构建数据上下文（尝试收集数据，不因单个数据失败而中断）
    data_context = {}
    errors = []

    if body.include_market:
        try:
            from app.services import market_service
            market_result = market_service.get_stock_quote(body.stock_code.strip())
            if market_result.get("success"):
                data_context["market"] = market_result
        except Exception as e:
            errors.append(f"行情数据获取失败: {e}")

    if body.include_financial:
        try:
            from app.services import market_service
            financial_result = market_service.get_stock_financial(body.stock_code.strip())
            if financial_result.get("success"):
                data_context["financial"] = financial_result
        except Exception as e:
            errors.append(f"财务数据获取失败: {e}")

# Выполните оценку Баффета
    result = buffett_service.evaluate_with_buffett(
        stock_code=body.stock_code.strip(),
        stock_name=body.stock_name.strip() or "",
        data_context=data_context,
    )

    if not result["success"]:
        return error_response(code=500, message=result.get("error", "评估失败"))

    data_warnings = ""
    if errors:
        data_warnings = "; ".join(errors)

    slim_ctx = buffett_service.slim_evaluation_context_for_api(result["evaluation_context"])

    return success_response(
        data={
            "stock_code": result["stock_code"],
            "stock_name": result["stock_name"],
            "evaluation_context": slim_ctx,
            "report_template": result["report_template"],
            "data_warnings": data_warnings or None,
        },
message=f"Контекст оценки Баффета для {result['stock_name'] или result['stock_code']} создан",
    )


@router.post("/report/generate-ai")
async def generate_ai_buffett_report(body: BuffettEvaluateRequest):
"""Создание отчета об оценке стоимостных инвестиций Баффета (LLM, синхронизированный JSON) одним щелчком мыши"""
    if not body.stock_code or len(body.stock_code.strip()) < 4:
        return error_response(code=400, message="请输入有效的股票代码")

    result = await asyncio.to_thread(
        buffett_service.generate_buffett_ai_report,
        body.stock_code.strip(),
        (body.stock_name or "").strip(),
    )

    if not result.get("success"):
        return error_response(
            code=503,
            message=result.get("error") or "AI 评估报告生成失败",
            data={"stock_code": body.stock_code.strip()},
        )

    return success_response(
        data={
            "stock_code": body.stock_code.strip(),
            "stock_name": (body.stock_name or "").strip(),
            "report_markdown": result["report_markdown"],
        },
message="Отчет об оценке ИИ Баффета создан",
    )


def _buffett_ai_report_ndjson_bytes(stock_code: str, stock_name: str):
    for evt in buffett_service.iter_buffett_ai_report_events(stock_code, stock_name):
        line = json.dumps(evt, ensure_ascii=False) + "\n"
        yield line.encode("utf-8")


@router.post("/report/generate-ai/stream")
async def stream_ai_buffett_report(body: BuffettEvaluateRequest):
    """流式生成巴菲特 AI 评估报告（NDJSON：meta → delta → … → done）"""
    if not body.stock_code or len(body.stock_code.strip()) < 4:
        return error_response(code=400, message="请输入有效的股票代码")

    return StreamingResponse(
        _buffett_ai_report_ndjson_bytes(
            body.stock_code.strip(),
            (body.stock_name or "").strip(),
        ),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/evaluate/stream")
async def stream_buffett_evaluate(body: BuffettEvaluateRequest):
"""План реализации согласовывает путь POST /api/v1/buffett/evaluate/stream, который эквивалентен report/generate-ai/stream"""
    if not body.stock_code or len(body.stock_code.strip()) < 4:
        return error_response(code=400, message="请输入有效的股票代码")

    return StreamingResponse(
        _buffett_ai_report_ndjson_bytes(
            body.stock_code.strip(),
            (body.stock_name or "").strip(),
        ),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/report/template")
async def get_report_template(
    code: str = Query(..., description="股票代码", min_length=4),
    name: str = Query(default="", description="股票名称"),
):
"""Получить шаблон отчета об оценке в стиле Баффета

Возвращает шаблон отчета в формате Markdown, содержащий все необходимые разделы, который можно напрямую использовать для заполнения результатов анализа.

- **код**: 6-значный код акций.
- **name**: название акции (необязательно).
    """
    template = buffett_service._build_buffett_report_template(code, name)
    return success_response(
        data={"template": template, "stock_code": code, "stock_name": name},
message="Шаблон отчета создан",
    )


@router.get("/reference/{ref_name}")
async def get_reference_file(
    ref_name: str,
):
    """获取巴菲特投资思维参考文件内容

Доступные справочные документы:
- 01-thinking-frameworks (рамки мышления)
- 02-investment-philosophy (философия инвестиций)
- 03-бизнес-ров (деловой ров)
- 04-management-governance (управление управлением)
- 05-financial-metrics (финансовые показатели)
- 06-valuation-capital (Оценка и капитал)
- 07-risk-behavior (риск и поведение)
- 08-отраслевые руководства (отраслевые руководства)

- **ref_name**: имя справочного файла, например «03-business-moat».
    """
    content = buffett_service.load_buffett_reference(ref_name)
    if content is None:
        return error_response(code=404, message=f"参考文件 '{ref_name}' 不存在或无法读取")

#Усекаем первые 5000 символов и возвращаем результат
    preview = content[:5000]
    is_truncated = len(content) > 5000

    return success_response(
        data={
            "ref_name": ref_name,
            "content": preview,
            "full_length": len(content),
            "truncated": is_truncated,
        },
message=f"Справочный файл {ref_name} ({'Предварительный просмотр первых 5000 символов', если is_truncated, иначе 'Полное содержимое'})",
    )
