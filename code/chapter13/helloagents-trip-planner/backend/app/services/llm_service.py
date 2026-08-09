"""Сервисный модуль LLM"""

from hello_agents import HelloAgentsLLM
from ..config import get_settings

# Глобальный экземпляр LLM
_llm_instance = None


def get_llm() -> HelloAgentsLLM:
    """
    Получить экземпляр LLM (одиночный режим)
    
    Возврат:
        Экземпляр HelloAgentsLLM
    """
    global _llm_instance
    
    if _llm_instance is None:
        settings = get_settings()
        
        # HelloAgentsLLM автоматически считывает конфигурацию из переменных среды.
        # Включая OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL и т. д.
        _llm_instance = HelloAgentsLLM()
        
        print(f"✅ Инициализация службы LLM прошла успешно")
        print(f"   Поставщик: {_llm_instance.provider}")
        print(f"   Модель: {_llm_instance.model}")
    
    return _llm_instance


def reset_llm():
    """Сброс экземпляра LLM (для тестирования или реконфигурации)"""
    global _llm_instance
    _llm_instance = None

