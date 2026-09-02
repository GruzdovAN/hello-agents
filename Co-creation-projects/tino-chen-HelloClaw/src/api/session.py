"""Маршрутизация API сеанса"""
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union, Literal

router = APIRouter(prefix="/session", tags=["session"])


class SessionInfo(BaseModel):
    """информация о сеансе"""
    id: str
    created_at: float
    updated_at: float


class SessionListResponse(BaseModel):
    """Ответ списка сеансов"""
    sessions: List[SessionInfo]


class SessionCreateRequest(BaseModel):
    """Создать запрос на сеанс"""
    summarize_old: bool = False  # Стоит ли подводить итоги старых разговоров

    old_session_id: Optional[str] = None  # Старый идентификатор сеанса для подведения итогов



class SessionCreateResponse(BaseModel):
    """Создать ответ сеанса"""
    session_id: str
    message: str = "Session created successfully"
    summary_file: Optional[str] = None  # Если суммируются старые сеансы, вернуть имя файла сводки.



class SessionSummaryInfo(BaseModel):
    """Сводная информация о сеансе"""
    filename: str
    date: str
    slug: str
    size: int
    updated_at: float


class SessionSummaryListResponse(BaseModel):
    """Ответ на список сводных данных сеанса"""
    summaries: List[SessionSummaryInfo]


# ==================== Стандартный формат сообщения OpenAI ===================


class ToolCallFunction(BaseModel):
    """Функция вызова инструмента"""
    name: str
    arguments: str  # JSON-строка



class ToolCall(BaseModel):
    """Вызов инструмента"""
    id: str
    type: Literal["function"] = "function"
    function: ToolCallFunction


class ChatMessage(BaseModel):
    """Сообщения чата (стандартный формат OpenAI)"""
    role: Literal["user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None  # Вызовы инструментов в сообщениях помощника

    tool_call_id: Optional[str] = None  # Идентификатор вызова в сообщении инструмента



class SessionHistoryResponse(BaseModel):
    """Ответ истории сеанса"""
    session_id: str
    messages: List[ChatMessage]


def get_agent():
    """Получить глобальный экземпляр агента"""
    from ..main import get_agent as _get_agent
    return _get_agent()


@router.get("/list", response_model=SessionListResponse)
async def list_sessions():
    """Получить список сеансов

    Вернуть все сеансы, отсортированные по убыванию времени обновления."""
    agent = get_agent()
    if not agent:
        return SessionListResponse(sessions=[])

    sessions = agent.list_sessions()
    return SessionListResponse(sessions=[
        SessionInfo(
            id=s["id"],
            created_at=s["created_at"],
            updated_at=s["updated_at"]
        )
        for s in sessions
    ])


@router.post("/create", response_model=SessionCreateResponse)
async def create_session(request: SessionCreateRequest = None):
    """Создать новый сеанс

    Дополнительные параметры:
    - summe_old: следует ли суммировать старые сеансы перед созданием новых.
    - old_session_id: идентификатор старого сеанса для суммирования (если не указан, суммируется самый последний сеанс)

    Возвращает идентификатор нового сеанса"""
    agent = get_agent()
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    request = request or SessionCreateRequest()
    summary_file = None

    # Если вам нужно подвести итоги старых сессий

    if request.summarize_old:
        old_session_id = request.old_session_id

        # Если старая сессия не указана, будет найдена самая последняя.

        if not old_session_id:
            sessions = agent.list_sessions()
            if sessions:
                old_session_id = sessions[0]["id"]

        # Подведите итоги старых разговоров

        if old_session_id:
            summary_file = await _summarize_session(agent, old_session_id)

    # Создать новый сеанс

    session_id = agent.create_session()

    return SessionCreateResponse(
        session_id=session_id,
        summary_file=summary_file,
        message="Session created successfully" + (f", old session summarized to {summary_file}" if summary_file else "")
    )


async def _summarize_session(agent, session_id: str) -> Optional[str]:
    """Подвести итоги данного занятия

    Аргументы:
        агент: экземпляр агента
        session_id: идентификатор сеанса

    Возврат:
        Суммировать имена файлов, возвращая None в случае неудачи"""
    try:
        from ..memory import SessionSummarizer

        # Получить историю сеансов

        messages = agent.get_session_history(session_id)
        if not messages:
            return None

        # Создать сводку

        summarizer = SessionSummarizer(
            workspace_manager=agent.workspace,
            model_id=agent._model_id,
            api_key=agent._api_key,
            base_url=agent._base_url,
        )

        # управляющее резюме

        summary_file = await summarizer.summarize_session(
            messages=messages,
            last_n=10,
            session_id=session_id,
        )

        return summary_file

    except Exception as e:
        print(f"⚠️ Ошибка сводки сессии: {e}")
        return None


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Получить подробную информацию о сеансе

    Возврат основной информации о сеансе"""
    agent = get_agent()
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    sessions = agent.list_sessions()
    for s in sessions:
        if s["id"] == session_id:
            return SessionInfo(
                id=s["id"],
                created_at=s["created_at"],
                updated_at=s["updated_at"]
            )

    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    """Получить сообщения истории сеансов

    Возвращает всю историю чата сеанса в стандартном формате OpenAI."""
    agent = get_agent()
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    raw_messages = agent.get_session_history(session_id)
    if raw_messages is None:
        raw_messages = []

    # Преобразование в стандартный формат OpenAI

    chat_messages: List[ChatMessage] = []

    for m in raw_messages:
        role = m.get("role", "")
        content = m.get("content", "")
        metadata = m.get("metadata", {})

        if role == "user":
            chat_messages.append(ChatMessage(role="user", content=content))

        elif role == "assistant":
            tool_calls_data = metadata.get("tool_calls")
            if tool_calls_data:
                # сообщение помощника, содержащее вызовы инструментов

                tool_calls = [
                    ToolCall(
                        id=tc.get("id", ""),
                        type="function",
                        function=ToolCallFunction(
                            name=tc.get("function", {}).get("name", ""),
                            arguments=tc.get("function", {}).get("arguments", "{}")
                        )
                    )
                    for tc in tool_calls_data
                ]
                chat_messages.append(ChatMessage(
                    role="assistant",
                    content=content if content else None,
                    tool_calls=tool_calls
                ))
            elif content:
                # Обычные текстовые сообщения помощника

                chat_messages.append(ChatMessage(role="assistant", content=content))

        elif role == "tool":
            # сообщение инструмента

            tool_call_id = metadata.get("tool_call_id")
            chat_messages.append(ChatMessage(
                role="tool",
                content=content,
                tool_call_id=tool_call_id
            ))

    return SessionHistoryResponse(
        session_id=session_id,
        messages=chat_messages
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Удалить сеанс

    Удалить указанную сессию и ее историю"""
    agent = get_agent()
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    success = agent.delete_session(session_id)
    if success:
        return {"message": "Session deleted successfully", "session_id": session_id}

    raise HTTPException(status_code=404, detail="Session not found")


# =================== API сводки сеанса ===================


@router.get("/summaries/list", response_model=SessionSummaryListResponse)
async def list_session_summaries():
    """Получить список всех сводок сеансов

    Возвращает сводку сеанса, отсортированную по дате в обратном порядке."""
    agent = get_agent()
    if not agent:
        return SessionSummaryListResponse(summaries=[])

    summaries = agent.workspace.list_session_summaries()
    return SessionSummaryListResponse(summaries=[
        SessionSummaryInfo(
            filename=s["filename"],
            date=s["date"],
            slug=s["slug"],
            size=s["size"],
            updated_at=s["updated_at"]
        )
        for s in summaries
    ])


@router.get("/summaries/{filename}")
async def get_session_summary(filename: str):
    """Получить сводку сеанса

    Аргументы:
        имя файла: сводное имя файла"""
    agent = get_agent()
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    content = agent.workspace.load_session_summary(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Summary not found")

    return {"filename": filename, "content": content}
