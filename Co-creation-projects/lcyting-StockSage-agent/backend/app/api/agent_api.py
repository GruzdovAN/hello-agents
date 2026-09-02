"""
API потокового анализа агента — анализ общественного мнения, API потокового анализа данных

Псевдонимы путей реализации см. в файле Sentiment.py, data_anaанализ.py (/sentiment/analyze/stream и т. д.).
"""

import json
import threading

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services import history_service

router = APIRouter(prefix="/agent", tags=["Agent分析"])


class AnalysisRequest(BaseModel):
stock_code: str = Field(...,description="код акции", min_length=6, max_length=6)
    stock_name: str = Field("", description="股票名称")


def _save_to_history(analysis_type, content, stock_code, stock_name, title):
"""Сохранить историю анализа в фоновом потоке"""
    import asyncio

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            history_service.save_analysis(
                analysis_type=analysis_type,
                content=content,
                stock_code=stock_code,
                stock_name=stock_name,
                title=title,
            )
        )
        loop.close()
    except Exception:
        pass


def _delta_text(ev: dict) -> str:
    return (ev.get("content") or ev.get("text") or "") if isinstance(ev, dict) else ""


def iter_sentiment_analysis_ndjson(stock_code: str, stock_name: str):
"""Сгенерировать строки NDJSON анализа общественного мнения (строковый итератор, включая завершающую новую строку)."""
    collected_content = []
    try:
        from agents.agent_system import get_agent_system

        asys = get_agent_system()
        for event in asys.analyze_sentiment_stream(stock_code, stock_name):
            if event.get("type") == "delta":
                collected_content.append(_delta_text(event))
            yield json.dumps(event, ensure_ascii=False) + "\n"

        full_content = "".join(collected_content)
        if full_content:
            threading.Thread(
                target=_save_to_history,
                args=(
                    "sentiment",
                    full_content,
                    stock_code,
                    stock_name,
                    f"{stock_name or stock_code} 舆情分析",
                ),
                daemon=True,
            ).start()
    except Exception as e:
        yield json.dumps({"type": "error", "content": f"舆情分析服务错误: {e}"}, ensure_ascii=False) + "\n"


def iter_data_analysis_ndjson(stock_code: str, stock_name: str):
"""Создать строки NDJSON для анализа данных."""
    collected_content = []
    try:
        from agents.agent_system import get_agent_system

        asys = get_agent_system()
        for event in asys.analyze_data_stream(stock_code, stock_name):
            if event.get("type") == "delta":
                collected_content.append(_delta_text(event))
            yield json.dumps(event, ensure_ascii=False) + "\n"

        full_content = "".join(collected_content)
        if full_content:
            threading.Thread(
                target=_save_to_history,
                args=(
                    "data_analysis",
                    full_content,
                    stock_code,
                    stock_name,
                    f"{stock_name or stock_code} 数据分析",
                ),
                daemon=True,
            ).start()
    except Exception as e:
        yield json.dumps({"type": "error", "content": f"数据分析服务错误: {e}"}, ensure_ascii=False) + "\n"


@router.post("/sentiment/stream")
async def sentiment_stream(body: AnalysisRequest):
"""Интерфейс потоковой передачи анализа общественного мнения AI (совместимый путь)"""
    return StreamingResponse(
        iter_sentiment_analysis_ndjson(body.stock_code, body.stock_name),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/data-analysis/stream")
async def data_analysis_stream(body: AnalysisRequest):
"""Потоковый интерфейс анализа данных AI (совместимый путь)"""
    return StreamingResponse(
        iter_data_analysis_ndjson(body.stock_code, body.stock_name),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
