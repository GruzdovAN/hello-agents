"""
Базовый класс агента InnoCore AI
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import logging

from core.config import get_config
from core.llm_adapter import get_llm_adapter
from core.exceptions import AgentException, TimeoutException

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Базовый абстрактный класс агента"""
    
    def __init__(self, name: str, llm = None, 
                 max_steps: int = None, timeout: int = None):
        self.name = name
        self.config = get_config()
        self.llm = llm or get_llm_adapter()
        
        self.max_steps = max_steps or self.config.agent_max_steps
        self.timeout = timeout or self.config.agent_timeout
        
        self.history = []
        self.tools = {}
        self.state = "idle"
        self.created_at = datetime.now()
        
    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить задачу агента"""
        pass
    
    def add_tool(self, tool_name: str, tool_func: Callable, description: str = ""):
        """Добавить инструмент"""
        self.tools[tool_name] = {
            "function": tool_func,
            "description": description
        }
    
    def get_tools_description(self) -> str:
        """Получить описание инструментов"""
        if not self.tools:
            return "Нет доступных инструментов"
        
        descriptions = []
        for name, tool_info in self.tools.items():
            descriptions.append(f"- {name}: {tool_info['description']}")
        
        return "\n".join(descriptions)
    
    async def call_tool(self, tool_name: str, tool_input: Any) -> Any:
        """Вызвать инструмент"""
        if tool_name not in self.tools:
            raise AgentException(f"Инструмент '{tool_name}' не существует")
        
        try:
            tool_func = self.tools[tool_name]["function"]
            if asyncio.iscoroutinefunction(tool_func):
                result = await asyncio.wait_for(
                    tool_func(tool_input), 
                    timeout=self.timeout
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(tool_func, tool_input),
                    timeout=self.timeout
                )
            
            self._add_to_history(f"Tool {tool_name} called with input: {tool_input}")
            self._add_to_history(f"Tool {tool_name} result: {result}")
            
            return result
            
        except asyncio.TimeoutError:
            raise TimeoutException(f"Превышено время ожидания выполнения инструмента '{tool_name}'")
        except Exception as e:
            raise AgentException(f"Ошибка выполнения инструмента '{tool_name}': {str(e)}")
    
    async def think(self, prompt: str, context: Dict = None) -> str:
        """Вызвать LLM для рассуждения"""
        try:
            # Собрать полный промпт
            full_prompt = prompt
            
            # Добавить контекст
            if context:
                context_str = json.dumps(context, ensure_ascii=False, indent=2)
                full_prompt = f"Контекст:\n{context_str}\n\nЗадача:\n{prompt}"
            
            # Добавить историю
            if self.history:
                history_str = "\n".join(self.history[-10:])  # только последние 10 записей
                full_prompt += f"\n\nИстория:\n{history_str}"
            
            # Вызов HelloAgent LLM
            response = await asyncio.wait_for(
                self.llm.ainvoke(full_prompt),
                timeout=self.timeout
            )
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            self._add_to_history(f"LLM prompt: {prompt}")
            self._add_to_history(f"LLM response: {response_text}")
            
            return response_text
            
        except asyncio.TimeoutError:
            raise TimeoutException("Превышено время ожидания ответа LLM")
        except Exception as e:
            raise AgentException(f"Ошибка рассуждения LLM: {str(e)}")
    
    def _add_to_history(self, message: str):
        """Добавить запись в историю"""
        timestamp = datetime.now().isoformat()
        self.history.append(f"[{timestamp}] {message}")
        
        # Ограничить длину истории
        if len(self.history) > 100:
            self.history = self.history[-50:]
    
    def get_history(self, limit: int = 10) -> List[str]:
        """Получить историю"""
        return self.history[-limit:]
    
    def clear_history(self):
        """Очистить историю"""
        self.history = []
    
    def set_state(self, state: str):
        """Установить состояние агента"""
        self.state = state
        logger.info(f"Agent {self.name} state changed to: {state}")
    
    def get_status(self) -> Dict[str, Any]:
        """Получить состояние агента"""
        return {
            "name": self.name,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "history_count": len(self.history),
            "tools_count": len(self.tools),
            "max_steps": self.max_steps,
            "timeout": self.timeout
        }
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Проверить входные данные"""
        required_fields = self.get_required_fields()
        
        for field in required_fields:
            if field not in input_data:
                raise AgentException(f"Отсутствует обязательное поле: {field}")
        
        return True
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """Получить обязательные поля входных данных"""
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', state='{self.state}')"
    
    def __repr__(self) -> str:
        return self.__str__()
