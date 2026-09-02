"""Маршрутизация API чата"""
import json
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """запрос в чат"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Ответ в чате"""
    content: str
    session_id: Optional[str] = None


def get_agent():
    """Получить глобальный экземпляр агента"""
    from ..main import get_agent as _get_agent
    return _get_agent()


@router.post("/send/sync", response_model=ChatResponse)
async def send_message_sync(request: ChatRequest):
    """Отправьте сообщение и получите синхронный ответ"""
    agent = get_agent()
    if not agent:
        return ChatResponse(content="Agent not initialized", session_id=request.session_id)

    response = agent.chat(request.message, request.session_id)
    return ChatResponse(content=response, session_id=request.session_id)


@router.post("/send/stream")
async def send_message_stream(request: ChatRequest):
    """Отправьте сообщение и получите потоковый ответ (SSE)

    Тип события:
    - сеанс: информация о сеансе (включая session_id)
    -step_start: начало шага
    - чанк: текстовый блок LLM
    -tool_start: запуск инструмента
    -tool_finish: вызов инструмента завершается
    -step_finish: конец шага
    - сделано: завершено
    - ошибка: ошибка"""

    async def event_generator():
        agent = get_agent()
        if not agent:
            yield {
                "event": "error",
                "data": json.dumps({"error": "Agent not initialized"}, ensure_ascii=False)
            }
            return

        try:
            async for event in agent.achat(request.message, request.session_id):
                event_type = event.type.value
                event_data = event.data

                # Обрабатывать разные типы событий

                if event_type == "agent_start":
                    # Отправить информацию о сеансе

                    session_id = getattr(agent, '_current_session_id', None)
                    yield {
                        "event": "session",
                        "data": json.dumps({"session_id": session_id}, ensure_ascii=False)
                    }

                elif event_type == "step_start":
                    # Начало шага

                    yield {
                        "event": "step_start",
                        "data": json.dumps({
                            "step": event_data.get("step", 1),
                            "max_steps": event_data.get("max_steps", 10)
                        }, ensure_ascii=False)
                    }

                elif event_type == "llm_chunk":
                    # Текстовый блок LLM

                    chunk = event_data.get("chunk", "")
                    yield {
                        "event": "chunk",
                        "data": json.dumps({"content": chunk}, ensure_ascii=False)
                    }

                elif event_type == "tool_call_start":
                    # Начинается вызов инструмента

                    yield {
                        "event": "tool_start",
                        "data": json.dumps({
                            "tool": event_data.get("tool_name", ""),
                            "args": event_data.get("args", {})
                        }, ensure_ascii=False)
                    }

                elif event_type == "tool_call_finish":
                    # Вызов инструмента завершается

                    yield {
                        "event": "tool_finish",
                        "data": json.dumps({
                            "tool": event_data.get("tool_name", ""),
                            "result": event_data.get("result", "")
                        }, ensure_ascii=False)
                    }

                elif event_type == "step_finish":
                    # Конец шага

                    yield {
                        "event": "step_finish",
                        "data": json.dumps({
                            "step": event_data.get("step", 1)
                        }, ensure_ascii=False)
                    }

                elif event_type == "agent_finish":
                    # Агент завершает работу, сохраните сеанс

                    session_id = agent.save_current_session()
                    final_content = event_data.get("result", "")

                    yield {
                        "event": "done",
                        "data": json.dumps({
                            "content": final_content,
                            "session_id": session_id
                        }, ensure_ascii=False)
                    }

                elif event_type == "error":
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": event_data.get("error", "Unknown error")}, ensure_ascii=False)
                    }

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False)
            }

    return EventSourceResponse(event_generator())


@router.post("/send")
async def send_message(request: ChatRequest):
    """Отправить сообщение (временно вернуть синхронный ответ)"""
    return await send_message_sync(request)
