"""
Адаптер LLM — на основе платформы HelloAgent.
"""

import logging
from typing import Dict, Any, Optional
from core.config import get_config

logger = logging.getLogger(__name__)

class LLMAdapter:
"""Адаптер LLM на основе платформы HelloAgent"""
    
    def __init__(self):
"""Инициализировать адаптер LLM"""
        self.config = get_config()
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
"""Инициализировать HelloAgent LLM"""
        try:
            from hello_agents import HelloAgentsLLM
            
# Согласно документации, параметры инициализации HelloAgentsLLM
            self.llm = HelloAgentsLLM(
                model=self.config.llm.model_name,
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                timeout=self.config.llm.timeout
            )
logger.info(f"Инициализация HelloAgent LLM успешна: {self.config.llm.model_name}")
        except ImportError as e:
            logger.error(f"hello-agents 未安装: {str(e)}")
поднять ImportError("Пожалуйста, установите hello-агенты: pip install 'hello-agents[all]>=0.2.7'")
        except Exception as e:
            logger.error(f"HelloAgent LLM 初始化失败: {str(e)}")
            raise
    
    def _format_messages(self, prompt: str) -> list:
        """
Форматирование слов подсказки в списке сообщений
        
        Args:
подсказка: строка подсказки
            
        Returns:
            消息列表，格式为 [{"role": "user", "content": "..."}]
        """
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            return prompt
        else:
            return [{"role": "user", "content": str(prompt)}]
    
    async def ainvoke(self, prompt: str, **kwargs) -> str:
        """
Вызов LLM асинхронно
        
        Args:
подсказка: слово подсказки (строка или список сообщений)
**kwargs: дополнительные параметры
            
        Returns:
Текст ответа LLM
        """
        try:
# Форматируем сообщение
            messages = self._format_messages(prompt)
            
# HelloAgent использует синхронный вызов и вызывается в асинхронном контексте
            import asyncio
            response = await asyncio.to_thread(self.llm.invoke, messages, **kwargs)
            
#Извлечение текстового содержимого
            if isinstance(response, str):
                return response
            elif hasattr(response, 'content'):
                return response.content
            elif hasattr(response, 'text'):
                return response.text
            else:
                return str(response)
        except Exception as e:
logger.error(f"Ошибка асинхронного вызова LLM: {str(e)}")
            raise
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """
Синхронный вызов LLM
        
        Args:
подсказка: слово подсказки (строка или список сообщений)
**kwargs: дополнительные параметры
            
        Returns:
Текст ответа LLM
        """
        try:
# Форматируем сообщение
            messages = self._format_messages(prompt)
            
# Синхронный вызов HelloAgent
            response = self.llm.invoke(messages, **kwargs)
            
#Извлечение текстового содержимого
            if isinstance(response, str):
                return response
            elif hasattr(response, 'content'):
                return response.content
            elif hasattr(response, 'text'):
                return response.text
            else:
                return str(response)
        except Exception as e:
            logger.error(f"LLM 同步调用失败: {str(e)}")
            raise

# Экземпляр глобального адаптера LLM
_llm_adapter = None

def get_llm_adapter() -> LLMAdapter:
"""Получить экземпляр глобального адаптера LLM"""
    global _llm_adapter
    if _llm_adapter is None:
        _llm_adapter = LLMAdapter()
    return _llm_adapter
