"""Одноэлементный элемент LLM в процессе (несколько агентов используют один и тот же клиент модели, чтобы избежать повторной инициализации)."""

from hello_agents import HelloAgentsLLM

from ..utils.logger import get_logger

logger = get_logger("app.llm")

_llm_instance: HelloAgentsLLM | None = None


def get_llm() -> HelloAgentsLLM:
"""HelloAgentsLLM автоматически считывает LLM_API_KEY / LLM_BASE_URL / LLM_MODEL_ID."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = HelloAgentsLLM()
        logger.info(
"Инициализация LLM: поставщик=%s модель=%s",
            getattr(_llm_instance, "provider", "?"),
            getattr(_llm_instance, "model", "?"),
        )
    return _llm_instance


def reset_llm() -> None:
    global _llm_instance
    _llm_instance = None
