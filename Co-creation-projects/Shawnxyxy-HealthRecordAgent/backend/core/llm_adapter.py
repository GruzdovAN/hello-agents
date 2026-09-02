"""
Адаптер LLM — на основе платформы HelloAgent.
"""

import asyncio
import logging
from typing import Any, List, Union

from core.config import get_config
from core.exceptions import LLMException

logger = logging.getLogger(__name__)

class LLMAdapter:
    def __init__(self):
        self.config = get_config()
        self.llm = None
        self._init_llm()

    def _init_llm(self):
"""Инициализировать HelloAgent LLM"""
        try:
            from hello_agents import HelloAgentsLLM

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
    
    def _format_messages(self, prompt: Union[str, List[dict]]) -> List[dict]:
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        if isinstance(prompt, list):
            return prompt
        return [{"role": "user", "content": str(prompt)}]

    async def ainvoke(self, prompt: Union[str, List[dict]], **kwargs) -> str:
        try:
            messages = self._format_messages(prompt)
            response = await asyncio.to_thread(self.llm.invoke, messages, **kwargs)
            return self._extract_text(response)
        except Exception as e:
поднять LLMException(f"Ошибка вызова LLM: {e}")

    def invoke(self, prompt: Union[str, List[dict]], **kwargs) -> str:
        try:
            messages = self._format_messages(prompt)
            response = self.llm.invoke(messages, **kwargs)
            return self._extract_text(response)
        except Exception as e:
поднять LLMException(f"Ошибка вызова LLM: {e}")

    def _extract_text(self, response: Any) -> str:
        if isinstance(response, str):
            return response
        if hasattr(response, "content"):
            return response.content
        if hasattr(response, "text"):
            return response.text
        return str(response)


# Глобальный экземпляр
_llm_adapter: LLMAdapter | None = None


def get_llm_adapter() -> LLMAdapter:
    global _llm_adapter
    if _llm_adapter is None:
        _llm_adapter = LLMAdapter()
    return _llm_adapter