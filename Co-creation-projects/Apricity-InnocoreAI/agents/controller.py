"""
Контроллер агентов InnoCore AI
Отвечает за координацию четырёх агентов и оркестрацию задач
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import logging
from enum import Enum

from agents.base import BaseAgent
from agents.hunter import HunterAgent
from agents.miner import MinerAgent
from agents.coach import CoachAgent
from agents.validator import ValidatorAgent
from core.config import get_config
from core.exceptions import AgentException, TimeoutException

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Перечисление типов задач"""
    PAPER_HUNTING = "paper_hunting"
    PAPER_ANALYSIS = "paper_analysis"
    WRITING_ASSISTANCE = "writing_assistance"
    CITATION_VALIDATION = "citation_validation"
    FULL_WORKFLOW = "full_workflow"

class TaskStatus(Enum):
    """Перечисление статусов задач"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentController:
    """Контроллер агентов"""
    
    def __init__(self):
        self.config = get_config()
        
        # Инициализация агентов
        self.agents = {
            "hunter": HunterAgent(),
            "miner": MinerAgent(),
            "coach": CoachAgent(),
            "validator": ValidatorAgent()
        }
        
        # Управление задачами
        self.active_tasks = {}
        self.task_history = []
        self.task_queue = asyncio.Queue()
        
        # Контроль параллелизма
        self.semaphore = asyncio.Semaphore(self.config.concurrent_agents)
        
        # Колбэки событий
        self.event_callbacks = {
            "task_started": [],
            "task_completed": [],
            "task_failed": [],
            "agent_status_changed": []
        }
    
    async def initialize(self):
        """Инициализировать контроллер"""
        logger.info("Инициализация Agent Controller...")
        
        # Здесь можно добавить логику инициализации агентов
        # например загрузку моделей, установку соединений и т.д.
        
        logger.info("Agent Controller инициализирован")
    
    async def submit_task(self, task_type: TaskType, input_data: Dict[str, Any], 
                         priority: int = 0, callback: Callable = None) -> str:
        """Отправить задачу"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_tasks)}"
        
        task = {
            "id": task_id,
            "type": task_type,
            "input_data": input_data,
            "status": TaskStatus.PENDING,
            "priority": priority,
            "callback": callback,
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
            "agent_results": {}
        }
        
        self.active_tasks[task_id] = task
        await self.task_queue.put((priority, task))
        
        logger.info(f"Задача отправлена: {task_id}, тип: {task_type.value}")
        return task_id
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Выполнить одну задачу"""
        if task_id not in self.active_tasks:
            raise AgentException(f"Задача не существует: {task_id}")
        
        task = self.active_tasks[task_id]
        
        async with self.semaphore:  # контроль параллелизма
            try:
                task["status"] = TaskStatus.RUNNING
                task["started_at"] = datetime.now()
                
                await self._trigger_event("task_started", task)
                
                # Выполнить логику в зависимости от типа задачи
                if task["type"] == TaskType.PAPER_HUNTING:
                    result = await self._execute_paper_hunting(task)
                elif task["type"] == TaskType.PAPER_ANALYSIS:
                    result = await self._execute_paper_analysis(task)
                elif task["type"] == TaskType.WRITING_ASSISTANCE:
                    result = await self._execute_writing_assistance(task)
                elif task["type"] == TaskType.CITATION_VALIDATION:
                    result = await self._execute_citation_validation(task)
                elif task["type"] == TaskType.FULL_WORKFLOW:
                    result = await self._execute_full_workflow(task)
                else:
                    raise AgentException(f"Неподдерживаемый тип задачи: {task['type']}")
                
                task["status"] = TaskStatus.COMPLETED
                task["completed_at"] = datetime.now()
                task["result"] = result
                
                await self._trigger_event("task_completed", task)
                
                # Выполнить колбэк
                if task["callback"]:
                    await task["callback"](task)
                
                return result
                
            except Exception as e:
                task["status"] = TaskStatus.FAILED
                task["completed_at"] = datetime.now()
                task["error"] = str(e)
                
                await self._trigger_event("task_failed", task)
                
                logger.error(f"Ошибка выполнения задачи {task_id}: {str(e)}")
                raise AgentException(f"Ошибка выполнения задачи: {str(e)}")
            
            finally:
                # Перенести в историю
                self.task_history.append(task.copy())
                del self.active_tasks[task_id]
    
    async def _execute_paper_hunting(self, task: Dict) -> Dict[str, Any]:
        """Выполнить задачу поиска статей"""
        input_data = task["input_data"]
        
        # Вызвать Hunter Agent
        hunter_result = await self.agents["hunter"].run(input_data)
        task["agent_results"]["hunter"] = hunter_result
        
        return {
            "task_type": "paper_hunting",
            "papers_found": hunter_result.get("downloaded_papers", []),
            "statistics": {
                "total_found": hunter_result.get("total_found", 0),
                "downloaded": hunter_result.get("downloaded_papers", 0)
            }
        }
    
    async def _execute_paper_analysis(self, task: Dict) -> Dict[str, Any]:
        """Выполнить задачу анализа статьи"""
        input_data = task["input_data"]
        
        # Вызвать Miner Agent
        miner_result = await self.agents["miner"].run(input_data)
        task["agent_results"]["miner"] = miner_result
        
        return {
            "task_type": "paper_analysis",
            "analysis_report": miner_result,
            "paper_id": input_data.get("paper_id")
        }
    
    async def _execute_writing_assistance(self, task: Dict) -> Dict[str, Any]:
        """Выполнить задачу помощи в написании"""
        input_data = task["input_data"]
        
        # Вызвать Coach Agent
        coach_result = await self.agents["coach"].run(input_data)
        task["agent_results"]["coach"] = coach_result
        
        return {
            "task_type": "writing_assistance",
            "assistance_result": coach_result,
            "user_id": input_data.get("user_id")
        }
    
    async def _execute_citation_validation(self, task: Dict) -> Dict[str, Any]:
        """Выполнить задачу проверки цитирования"""
        input_data = task["input_data"]
        
        # Вызвать Validator Agent
        validator_result = await self.agents["validator"].run(input_data)
        task["agent_results"]["validator"] = validator_result
        
        return {
            "task_type": "citation_validation",
            "validation_result": validator_result,
            "paper_info": input_data.get("paper_info")
        }
    
    async def _execute_full_workflow(self, task: Dict) -> Dict[str, Any]:
        """Выполнить полный рабочий процесс"""
        input_data = task["input_data"]
        user_id = input_data.get("user_id")
        keywords = input_data.get("keywords", [])
        
        workflow_result = {
            "task_type": "full_workflow",
            "stages": {},
            "final_papers": [],
            "analysis_reports": []
        }
        
        try:
            # Этап 1: поиск статей
            self._add_to_history("Начало этапа поиска статей")
            hunting_input = {
                "keywords": keywords,
                "max_papers": input_data.get("max_papers", 10),
                "sources": input_data.get("sources", ["arxiv"])
            }
            
            hunting_result = await self.agents["hunter"].run(hunting_input)
            workflow_result["stages"]["hunting"] = hunting_result
            task["agent_results"]["hunter"] = hunting_result
            
            downloaded_papers = hunting_result.get("papers", [])
            workflow_result["final_papers"] = downloaded_papers
            
            # Этап 2: анализ статей
            self._add_to_history("Начало этапа анализа статей")
            for paper in downloaded_papers:
                if paper.get("db_id"):
                    analysis_input = {
                        "paper_id": paper["db_id"],
                        "user_id": user_id,
                        "analysis_type": "full"
                    }
                    
                    try:
                        analysis_result = await self.agents["miner"].run(analysis_input)
                        workflow_result["analysis_reports"].append(analysis_result)
                    except Exception as e:
                        self._add_to_history(f"Ошибка анализа статьи {paper.get('title', 'Unknown')}: {str(e)}")
            
            # Этап 3: проверка цитирования (опционально)
            if input_data.get("validate_citations", False):
                self._add_to_history("Начало этапа проверки цитирования")
                for paper in downloaded_papers:
                    paper_info = {
                        "title": paper.get("title", ""),
                        "authors": paper.get("authors", []),
                        "doi": paper.get("doi", ""),
                        "year": datetime.now().year
                    }
                    
                    validation_input = {
                        "paper_info": paper_info,
                        "formats": ["bibtex", "apa"],
                        "verify_external": True
                    }
                    
                    try:
                        validation_result = await self.agents["validator"].run(validation_input)
                        paper["citations"] = validation_result.get("citations", {})
                    except Exception as e:
                        self._add_to_history(f"Ошибка проверки цитирования {paper.get('title', 'Unknown')}: {str(e)}")
            
            self._add_to_history("Полный рабочий процесс завершён")
            
        except Exception as e:
            self._add_to_history(f"Ошибка выполнения рабочего процесса: {str(e)}")
            raise
        
        return workflow_result
    
    async def start_task_processor(self):
        """Запустить обработчик задач"""
        logger.info("Запуск обработчика задач...")
        
        while True:
            try:
                # Получить задачу (сортировка по приоритету)
                priority, task = await self.task_queue.get()
                
                # Асинхронное выполнение задачи
                asyncio.create_task(self.execute_task(task["id"]))
                
            except Exception as e:
                logger.error(f"Исключение в обработчике задач: {str(e)}")
                await asyncio.sleep(1)
    
    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Получить статус задачи"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "id": task["id"],
                "type": task["type"].value,
                "status": task["status"].value,
                "created_at": task["created_at"].isoformat(),
                "started_at": task["started_at"].isoformat() if task["started_at"] else None,
                "completed_at": task["completed_at"].isoformat() if task["completed_at"] else None,
                "priority": task["priority"]
            }
        else:
            # Поиск в истории
            for task in self.task_history:
                if task["id"] == task_id:
                    return {
                        "id": task["id"],
                        "type": task["type"].value,
                        "status": task["status"].value,
                        "created_at": task["created_at"].isoformat(),
                        "started_at": task["started_at"].isoformat() if task["started_at"] else None,
                        "completed_at": task["completed_at"].isoformat() if task["completed_at"] else None,
                        "priority": task["priority"]
                    }
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Отменить задачу"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if task["status"] == TaskStatus.PENDING:
                task["status"] = TaskStatus.CANCELLED
                task["completed_at"] = datetime.now()
                
                # Перенести в историю
                self.task_history.append(task.copy())
                del self.active_tasks[task_id]
                
                logger.info(f"Задача отменена: {task_id}")
                return True
        
        return False
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Получить состояние всех агентов"""
        agent_status = {}
        for name, agent in self.agents.items():
            agent_status[name] = agent.get_status()
        
        return {
            "agents": agent_status,
            "active_tasks": len(self.active_tasks),
            "queued_tasks": self.task_queue.qsize(),
            "completed_tasks": len(self.task_history),
            "max_concurrent": self.config.concurrent_agents
        }
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """Добавить колбэк события"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
    
    async def _trigger_event(self, event_type: str, data: Any):
        """Вызвать событие"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Ошибка выполнения колбэка события {event_type}: {str(e)}")
    
    def _add_to_history(self, message: str):
        """Добавить запись в историю контроллера"""
        timestamp = datetime.now().isoformat()
        logger.info(f"[{timestamp}] Controller: {message}")
    
    async def shutdown(self):
        """Завершить работу контроллера"""
        logger.info("Завершение работы Agent Controller...")
        
        # Отменить все ожидающие задачи
        for task_id in list(self.active_tasks.keys()):
            await self.cancel_task(task_id)
        
        # Освободить ресурсы агентов
        for agent in self.agents.values():
            if hasattr(agent, 'close'):
                await agent.close()
        
        logger.info("Agent Controller завершён")

# Глобальный экземпляр контроллера
agent_controller = AgentController()
