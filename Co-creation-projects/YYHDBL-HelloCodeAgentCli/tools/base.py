"""Базовый класс инструмента"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel

class ToolParameter(BaseModel):
    """Определение параметра инструмента"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None

class Tool(ABC):
    """Базовый класс инструмента"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def run(self, parameters: Dict[str, Any]) -> str:
        """Выполняет инструмент"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """Возвращает определения параметров инструмента"""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Проверяет параметры"""
        required_params = [p.name for p in self.get_parameters() if p.required]
        return all(param in parameters for param in required_params)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в формат словаря"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [param.dict() for param in self.get_parameters()]
        }
    
    def __str__(self) -> str:
        return f"Tool(name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()
