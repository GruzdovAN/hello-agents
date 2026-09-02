"""
AI Dialogue Assistant API — интерфейс потокового диалога агента-координатора
"""

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["AI对话助手"])


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息", min_length=1)
    stock_code: str = Field("", description="关联股票代码（可选）")
    stock_name: str = Field("", description="关联股票名称（可选）")
    history: list = Field(default_factory=list, description="对话历史")


def _make_chat_stream(message: str, stock_code: str, stock_name: str, history: list):
"""Сгенерировать потоковый ответ NDJSON"""
    try:
        for event in chat_service.iter_chat_stream_events(
            message, stock_code, stock_name, history
        ):
            yield json.dumps(event, ensure_ascii=False) + "\n"
    except Exception as e:
        err = {"type": "error", "content": f"对话服务错误: {e}", "message": f"对话服务错误: {e}"}
        yield json.dumps(err, ensure_ascii=False) + "\n"


@router.post("/stream")
async def chat_stream(body: ChatRequest):
"""Интерфейс потокового ассистента разговора с искусственным интеллектом

Пользователи предоставляют требования посредством диалога, а агент-координатор анализирует требования.
Автоматически вызывайте субагентов и транслируйте результаты анализа.
    """
    return StreamingResponse(
        _make_chat_stream(body.message, body.stock_code, body.stock_name, body.history),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
