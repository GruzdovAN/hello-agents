"""
Уровень службы помощника по диалогу с искусственным интеллектом — итерация событий NDJSON агента-координатора (соглашение о решении по внедрению)
"""

from typing import Any, Iterator, List


def iter_chat_stream_events(
    message: str,
    stock_code: str = "",
    stock_name: str = "",
    history: List[Any] | None = None,
) -> Iterator[dict]:
    """产出与 POST /api/v1/chat/stream 一致的 NDJSON 事件字典。"""
    from agents.agent_system import get_agent_system

    asys = get_agent_system()
    text = message
    if (stock_code or stock_name).strip():
        text = f"[股票: {stock_name}({stock_code})] {message}"
    yield from asys.chat_stream(text, history or [])
