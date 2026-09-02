"""
Уровень маршрутизации FastAPI — агент расширения английского предложения
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import sys
import os

# Добавить внутренний каталог в путь Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.entities import (
    StartRequest,
    SubmitRequest,
    AgentResponse,
    SessionState
)
from services.session_store import get_session_store
from agents.orchestrator import get_orchestrator
from agents.auto_mode_agent import get_auto_mode

router = APIRouter(prefix="/api", tags=["expand"])


@router.post("/session/start", response_model=AgentResponse)
async def start_session(request: StartRequest) -> AgentResponse:
    """
Создайте новый сеанс и вернитесь к первому этапу, чтобы задать вопросы.
    
    Args:
запрос: запрос на начало сеанса, включая исходное предложение и шаблон.
        
    Returns:
AgentResponse: Ответ агента
    """
# Получить хранилище сеансов
    session_store = get_session_store()
    
# Создать сеанс
    session = session_store.create_session(
        seed_sentence=request.seed_sentence,
        mode=request.mode
    )
    
# Получить оркестратор
    orchestrator = get_orchestrator()
    
# Начать сеанс
    response = orchestrator.start_session(session)
    
    return response


@router.post("/session/submit", response_model=AgentResponse)
async def submit_sentence(request: SubmitRequest) -> AgentResponse:
    """
Предложите пользователю расширить предложение, вернуться к комментариям и задать вопросы на следующем этапе (ручной режим)
    
    Args:
запрос: отправьте запрос, включая идентификатор сеанса и предложение пользователя.
        
    Returns:
AgentResponse: Ответ агента
    """
# Получить хранилище сеансов
    session_store = get_session_store()
    
# Получить сессию
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
# Получить оркестратор
    orchestrator = get_orchestrator()
    
# Обработка ввода пользователя
    response = orchestrator.process_user_input(
        session_state=session,
        user_sentence=request.user_sentence
    )
    
# Обновление сеанса
    session_store.update_session(session)
    
    return response


@router.get("/session/{session_id}/auto")
async def auto_mode_stream(session_id: str) -> StreamingResponse:
    """
SSE транслирует три раунда автоматических демонстраций
    
    Args:
session_id: идентификатор сеанса
        
    Returns:
StreamingResponse: ответ потоковой передачи SSE.
    """
# Получить хранилище сеансов
    session_store = get_session_store()
    
# Получить сессию
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
# Получить агент AutoModeAgent
    auto_mode_agent = get_auto_mode()
    
# Генерируем потоковый ответ
    async def event_generator() -> AsyncGenerator[str, None]:
        import json
        try:
# Использовать потоковое выполнение
            async for event in auto_mode_agent.run_auto_mode_stream(session.seed_sentence):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
#Отправить конечное событие
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'detail': str(e), 'type': type(e).__name__}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/session/{session_id}", response_model=SessionState)
async def get_session(session_id: str) -> SessionState:
    """
Получить полный статус текущего сеанса
    
    Args:
session_id: идентификатор сеанса
        
    Returns:
SessionState: состояние сеанса
    """
# Получить хранилище сеансов
    session_store = get_session_store()
    
# Получить сессию
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session
