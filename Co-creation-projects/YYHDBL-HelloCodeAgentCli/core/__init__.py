"""Модули ядра фреймворка

Примечание: модули ядра этого репозитория содержат опциональные зависимости
(например, pydantic). Чтобы часть возможностей (например, только LLM-клиент)
можно было переиспользовать в минимальном окружении, здесь используется
ленивый/отказоустойчивый импорт опциональных зависимостей.
"""

from .exceptions import HelloAgentsException
from .llm import HelloAgentsLLM

try:
    from .agent import Agent
    from .config import Config
    from .message import Message
except Exception:  # optional deps may be missing in minimal environments
    Agent = None  # type: ignore[assignment]
    Config = None  # type: ignore[assignment]
    Message = None  # type: ignore[assignment]

__all__ = ["HelloAgentsLLM", "HelloAgentsException", "Agent", "Config", "Message"]
