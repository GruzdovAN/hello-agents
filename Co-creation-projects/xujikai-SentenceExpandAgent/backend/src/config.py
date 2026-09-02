"""
Конфигурация LLM — агент расширения английских предложений
"""
import os
import logging
from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM

load_dotenv()

logger = logging.getLogger(__name__)

def tool_listener(call_info):
    logger.info(f"Agent: {call_info['agent_name']}")
    logger.info(f"Tool: {call_info['tool_name']}")
    logger.info(f"Parameters: {call_info['parsed_parameters']}")
    logger.info(f"Result: {call_info['result']}")

# Конфигурация LLM
class LLMConfig:
"""Класс конфигурации LLM"""
    
# Читаем конфигурацию из переменных среды
    API_KEY = os.getenv("LLM_API_KEY", "")
    MODEL_ID = os.getenv("LLM_MODEL_ID", "")
    BASE_URL = os.getenv("LLM_BASE_URL", "")
    
    @classmethod
    def create_llm(cls) -> HelloAgentsLLM:
        """
Создать экземпляр LLM
        
        Returns:
HelloAgentsLLM: настроенный экземпляр LLM
        """
        return HelloAgentsLLM(
            api_key=cls.API_KEY,
            model_id=cls.MODEL_ID,
            base_url=cls.BASE_URL
        )


# Глобальный экземпляр LLM (ленивая загрузка)
_llm_instance = None


def get_llm() -> HelloAgentsLLM:
    """
    获取全局 LLM 实例（单例模式）
    
    Returns:
HelloAgentsLLM: экземпляр LLM
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMConfig.create_llm()
    return _llm_instance


def reset_llm():
"""Сбросить экземпляр LLM (для тестирования или изменения конфигурации)"""
    global _llm_instance
    _llm_instance = None
