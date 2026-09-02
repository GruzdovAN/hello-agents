"""
Маршрутизация API, связанная с задачей
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import json
import asyncio

# from ...agents.controller import agent_controller, TaskType
# Временные комментарии, чтобы избежать относительных ошибок импорта.
agent_controller = None
TaskType = None

logger = logging.getLogger(__name__)
router = APIRouter()

# Пидантическая модель
class TaskSubmitRequest(BaseModel):
    task_type: str
    input_data: Dict[str, Any]
    priority: int = 0

class TaskResponse(BaseModel):
    id: str
    type: str
    status: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    priority: int

# Управление соединением WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
# Соединение прервано, удалите
                self.active_connections.remove(connection)

manager = ConnectionManager()

@router.post("/submit", response_model=Dict[str, Any])
async def submit_task(request: TaskSubmitRequest):
"""Отправить задачу"""
    try:
# Проверьте тип задачи
        try:
            task_type = TaskType(request.task_type)
        except ValueError:
поднять HTTPException(status_code=400, Detail=f"Неподдерживаемый тип задачи: {request.task_type}")
        
# Отправить задачу
        task_id = await agent_controller.submit_task(
            task_type=task_type,
            input_data=request.input_data,
            priority=request.priority
        )
        
        return {
            "success": True,
            "task_id": task_id,
"message": "Задание отправлено"
        }
        
    except HTTPException:
        raise
    except Exception as e:
logger.error(f «Не удалось отправить задачу: {str(e)}»)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}/execute", response_model=Dict[str, Any])
async def execute_task(task_id: str):
"""Выполнять задания"""
    try:
        result = await agent_controller.execute_task(task_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
logger.error(f «Не удалось выполнить задачу: {str(e)}»)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}/status", response_model=TaskResponse)
async def get_task_status(task_id: str):
"""Получить статус задачи"""
    try:
        status = await agent_controller.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return TaskResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
logger.error(f «Не удалось получить статус задачи: {str(e)}»)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{task_id}", response_model=Dict[str, Any])
async def cancel_task(task_id: str):
"""Отменить задачу"""
    try:
        success = await agent_controller.cancel_task(task_id)
        
        if success:
            return {"success": True, "message": "任务已取消"}
        else:
            return {"success": False, "message": "任务无法取消（可能正在执行或已完成）"}
        
    except Exception as e:
logger.error(f «Не удалось отменить задачу: {str(e)}»)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[TaskResponse])
async def list_tasks():
"""Получить список задач"""
    try:
# Получайте активные задачи
        active_tasks = []
        for task_id, task in agent_controller.active_tasks.items():
            active_tasks.append(TaskResponse(
                id=task["id"],
                type=task["type"].value,
                status=task["status"].value,
                created_at=task["created_at"].isoformat(),
                started_at=task["started_at"].isoformat() if task["started_at"] else None,
                completed_at=task["completed_at"].isoformat() if task["completed_at"] else None,
                priority=task["priority"]
            ))
        
# Получите исторические задания (последние 50)
        history_tasks = []
        for task in agent_controller.task_history[-50:]:
            history_tasks.append(TaskResponse(
                id=task["id"],
                type=task["type"].value,
                status=task["status"].value,
                created_at=task["created_at"].isoformat(),
                started_at=task["started_at"].isoformat() if task["started_at"] else None,
                completed_at=task["completed_at"].isoformat() if task["completed_at"] else None,
                priority=task["priority"]
            ))
        
        return active_tasks + history_tasks
        
    except Exception as e:
logger.error(f «Не удалось получить список задач: {str(e)}»)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/status", response_model=Dict[str, Any])
async def get_agents_status():
"""Получить статус агента"""
    try:
        status = await agent_controller.get_agent_status()
        return {
            "success": True,
            "agents": status
        }
        
    except Exception as e:
logger.error(f «Не удалось получить статус агента: {str(e)}»)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow/full", response_model=Dict[str, Any])
async def run_full_workflow(input_data: Dict[str, Any]):
"""Запустите весь рабочий процесс"""
    try:
# Отправьте полную задачу рабочего процесса
        task_id = await agent_controller.submit_task(
            task_type=TaskType.FULL_WORKFLOW,
            input_data=input_data,
Priority=1 # высокий приоритет
        )
        
# Выполняем задачи
        result = await agent_controller.execute_task(task_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
logger.error(f «Не удалось запустить весь рабочий процесс: {str(e)}»)
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{task_id}")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
"""Обновление задачи WebSocket"""
    await manager.connect(websocket)
    try:
# Отправляем начальный статус
        status = await agent_controller.get_task_status(task_id)
        if status:
            await manager.send_personal_message(
                json.dumps({"type": "status", "data": status}),
                websocket
            )
        
# Отслеживать изменения статуса задачи
        while True:
await asyncio.sleep(1) # Проверяем каждую секунду
            
            status = await agent_controller.get_task_status(task_id)
            if status:
                await manager.send_personal_message(
                    json.dumps({"type": "status", "data": status}),
                    websocket
                )
                
# Если задача выполнена, отключите
                if status["status"] in ["completed", "failed", "cancelled"]:
                    break
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
logger.error(f"Исключение соединения WebSocket: {str(e)}")
        manager.disconnect(websocket)

@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
"""Потоковая связь через WebSocket (для взаимодействия в реальном времени, например, помощников по написанию)"""
    await manager.connect(websocket)
    try:
        while True:
#Получить сообщения
            data = await websocket.receive_text()
            message = json.loads(data)
            
# Обработка различных типов сообщений
            if message.get("type") == "writing_assistance":
# Обрабатывать запросы на помощь в написании
                await handle_writing_assistance(websocket, message.get("data", {}))
            elif message.get("type") == "ping":
                # 心跳检测
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket流式通信异常: {str(e)}")
        manager.disconnect(websocket)

async def handle_writing_assistance(websocket: WebSocket, data: Dict[str, Any]):
"""Обработка запросов на помощь в написании"""
    try:
# Отправляйте задания по помощи в написании
        task_id = await agent_controller.submit_task(
            task_type=TaskType.WRITING_ASSISTANCE,
            input_data=data
        )
        
# Отправить идентификатор задачи
        await manager.send_personal_message(
            json.dumps({"type": "task_started", "task_id": task_id}),
            websocket
        )
        
# Выполняем задачи
        result = await agent_controller.execute_task(task_id)
        
# Отправить результаты
        await manager.send_personal_message(
            json.dumps({"type": "task_completed", "result": result}),
            websocket
        )
        
    except Exception as e:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": str(e)}),
            websocket
        )