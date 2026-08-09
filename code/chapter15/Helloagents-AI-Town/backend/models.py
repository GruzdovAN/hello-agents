"""Определение модели данных"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    """Запрос на разговор с одним NPC"""
    npc_name: str = Field(..., description="Имя НПС")
    message: str = Field(..., description="новости игрока")
    
    class Config:
        json_schema_extra = {
            "example": {
                "npc_name": "Чжан Сан",
                "message": "Привет, что ты делаешь?"
            }
        }

class ChatResponse(BaseModel):
    """Одиночный диалоговый ответ NPC"""
    npc_name: str = Field(..., description="Имя НПС")
    npc_title: str = Field(..., description="Позиции NPC")
    message: str = Field(..., description="Ответ NPC")
    success: bool = Field(default=True, description="Это успешно?")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Временная метка")
    
    class Config:
        json_schema_extra = {
            "example": {
                "npc_name": "Чжан Сан",
                "npc_title": "Python-инженер",
                "message": "Привет! Я пишу код для отладки ошибки в многоагентной системе.",
                "success": True
            }
        }

class NPCInfo(BaseModel):
    """Информация о NPC"""
    name: str = Field(..., description="Имя НПС")
    title: str = Field(..., description="Позиции NPC")
    location: str = Field(..., description="Местоположение НПС")
    activity: str = Field(..., description="текущая деятельность")
    available: bool = Field(default=True, description="Можно ли поговорить?")

class NPCStatusResponse(BaseModel):
    """Ответ о статусе NPC"""
    dialogues: Dict[str, str] = Field(..., description="Содержание текущего разговора с NPC")
    last_update: Optional[datetime] = Field(None, description="Последнее обновление")
    next_update_in: int = Field(..., description="Обратный отсчет до следующего обновления (секунды)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dialogues": {
                    "Чжан Сан": "Наконец-то ошибка была исправлена ​​и тест пройден!",
                    "Джон Доу": "Нам нужно подготовить некоторые материалы для совещания по обзору продукта на следующей неделе.",
                    "Ван Ву": "Цветовая схема этого интерфейса еще нуждается в оптимизации."
                },
                "last_update": "2024-01-15T10:30:00",
                "next_update_in": 25
            }
        }

class NPCListResponse(BaseModel):
    """Ответ по списку NPC"""
    npcs: List[NPCInfo] = Field(..., description="Список NPC")
    total: int = Field(..., description="Общее количество NPC")

