"""
Базовый класс агента HealthRecordAgent
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable, Optional, ClassVar
from datetime import datetime

from core.config import get_config
from core.llm_adapter import get_llm_adapter
from core.exceptions import AgentException, TimeoutException

from enum import Enum

# Глобальное управление статусом задач
TASKS = {}

def create_task(task_id: str, user_id: str | None = None):
    TASKS[task_id] = {
        "task_id": task_id,
        "user_id": user_id,
        "state": "running",
        "agents": {
            "PlannerAgent": "pending",
            "HealthIndicatorAgent": "pending",
            "RiskAssessmentAgent": "pending",
            "AdviceAgent": "pending",
            "ReportAgent": "pending"},
"report": Нет, # Итоговый отчет
    }

def update_agent_state(task_id: str, agent_name: str, state: str, partial_report=None):
    task = TASKS.get(task_id)
    if not task:
        return
    task["agents"][agent_name] = state
    if partial_report:
        task["report"] = partial_report
    
def complete_task(task_id: str, report: dict):
    task = TASKS.get(task_id)
    if not task:
        return
    task["state"] = "completed"
    task["report"] = report
    for agent in task["agents"]:
        task["agents"][agent] = "completed"

def get_task_status(task_id: str):
    return TASKS.get(task_id)

class TraceLevel(str, Enum):
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"
    ERROR = "ERROR"

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
Базовый абстрактный класс агента
    """

    def __init__(
        self, name: str, llm = None, 
                 max_steps: int = None, timeout: int = None, debug: bool = True, task_id = None):
        self.name = name
        self.config = get_config()
        self.llm = llm or get_llm_adapter()
        
        self.max_steps = max_steps or self.config.agent.max_steps
        self.timeout = timeout or self.config.agent.timeout

        self.history = []
        self.tools = {}
        self.state = "idle"
        self.created_at = datetime.now()
        self.debug = debug
        self.traces: List[Dict[str, Any]] = []
        self.task_id = task_id
# ========== Основной интерфейс ==========
    @abstractmethod
    async def run(self, **kwargs) -> Any:
"""Вход для выполнения агента"""
        pass

# ========== Мысли LLM ==========
    async def think(self, prompt: str, context: Dict = None) -> str:
"""Позвоните в LLM, подумаем"""
        try:
# Создайте полное слово-подсказку
            full_prompt = prompt
            
#Добавляем контекстную информацию
            if context:
                context_str = json.dumps(context, ensure_ascii=False, indent=2)
full_prompt = f"Контекстная информация:\n{context_str}\n\nЗадача:\n{prompt}"
            
#Добавить историю
            if self.history:
History_str = "\n".join(self.history[-10:]) # Сохраняем только последние 10 записей
                full_prompt += f"\n\n历史记录:\n{history_str}"
            
            self.trace("LLM CALL",
                {
                    "prompt_length": len(full_prompt),
                    "history_length": len(self.history)
                },
                TraceLevel.INFO
            )

            start = datetime.now()
            
# Позвоните в HelloAgent LLM
            response = await asyncio.wait_for(
                self.llm.ainvoke(full_prompt),
                timeout=self.timeout
            )

            duration = (datetime.now() - start).total_seconds()

            self.trace("LLM TTHINKING TIME",
                {
                    "duration_sec": duration,
                    "prompt_tokens": len(full_prompt),
                }
            )
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            self.trace("LLM RESPONSE", response_text)

            self._add_to_history(f"LLM prompt: {prompt}")
            self._add_to_history(f"LLM response: {response_text}")
            
            return response_text
            
        except asyncio.TimeoutError:
поднять TimeoutException(f"Тайм-аут на размышление LLM")
        except Exception as e:
            raise AgentException(f"LLM思考失败: {str(e)}")
# ========== Механизм инструмента ==========
    def add_tool(self, tool_name: str, tool_func: Callable, description: str = ""):
"""Добавить инструменты"""
        self.tools[tool_name] = {
            "function": tool_func,
            "description": description
        }
    
    def get_tools_description(self) -> str:
"""Получить описание инструмента"""
        if not self.tools:
вернуть «Инструменты пока недоступны»
        
        descriptions = []
        for name, tool_info in self.tools.items():
            descriptions.append(f"- {name}: {tool_info['description']}")
        
        return "\n".join(descriptions)
    
    async def call_tool(self, tool_name: str, tool_input: Any) -> Any:
"""Вызов инструментов"""
        if tool_name not in self.tools:
            raise AgentException(f"工具 '{tool_name}' 不存在")
        
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
            raise TimeoutException(f"工具 '{tool_name}' 执行超时")
        except Exception as e:
поднять AgentException(f "Не удалось выполнить инструмент '{tool_name}': {str(e)}")
# ========== Статус и история ==========
    def _add_to_history(self, message: str):
        """添加到历史记录"""
        timestamp = datetime.now().isoformat()
        self.history.append(f"[{timestamp}] {message}")
        
# Ограничить длину записей истории
        if len(self.history) > 100:
            self.history = self.history[-50:]
    
    def get_history(self, limit: int = 10) -> List[str]:
"""Получить историю"""
        return self.history[-limit:]
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []
    
    def set_state(self, state: str):
"""Установить состояние агента"""
        self.state = state

# Обновить статус глобальной задачи
        if self.task_id:
            update_agent_state(self.task_id, self.name, state)

        self.trace("STATE CHANGE",
            {
                "state": state
            }
        )
        logger.info(f"Agent {self.name} state changed to: {state}")
    
    def get_status(self) -> Dict[str, Any]:
"""Получить статус агента"""
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
"""Проверка входных данных"""
        required_fields = self.get_required_fields()
        
        for field in required_fields:
            if field not in input_data:
                raise AgentException(f"缺少必需字段: {field}")
        
        return True
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
"""Получить необходимые поля ввода"""
        pass

    def trace(self, title: str, data: Any, level: TraceLevel = TraceLevel.DEBUG):
"""Вывод отладки унифицированного агента"""
        event = {
        "agent": self.name,
        "title": title,
        "timestamp": datetime.now().isoformat(),
        "data": data
        }

        self.traces.append({
            **event,
            "level": level
        })

        if not self.debug:
            return
        
        if level in [TraceLevel.INFO, TraceLevel.ERROR]:
            logger.info(f"[{self.name}] {title}")
            return

        if level == TraceLevel.DEBUG:
            preview = self._preview(data)
            logger.debug(f"[{self.name}] {title}: {preview}")

        try:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception:
            print(data)

    def trace_step(self, step: str, status: str):
        self.trace(
            "STEP",
            {
                "step": step,
                "status": status
            }
        )
    def get_traces(self) -> List[Dict[str, Any]]:
        return self.traces
    
    def _preview(self, data, max_len: int = 300):
"""Сводка журнала"""
        if data is None:
            return ""

        text = str(data)

        if len(text) > max_len:
            return text[:max_len] + "...(truncated)"

        return text
