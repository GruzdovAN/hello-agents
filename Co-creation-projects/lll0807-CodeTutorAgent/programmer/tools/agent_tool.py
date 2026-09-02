"""
AgentTool: оборачивает SimpleAgent в Tool для прямого вызова.
Более простой мультиагентный режим, чем A2A.
"""
from hello_agents import SimpleAgent
from hello_agents.tools import Tool
from typing import Dict, Any

class AgentTool(Tool):
    """Оборачивает SimpleAgent как инструмент для вызова из другого агента"""
    
    def __init__(self, agent: SimpleAgent, name: str, description: str):
        """
        Args:
            agent: экземпляр SimpleAgent для обёртки
            name: имя инструмента
            description: описание инструмента
        """
        self.agent = agent
        self._name = name
        self._description = description
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    def get_parameters(self) -> list:
        """Определяет параметры инструмента"""
        from hello_agents.tools.base import ToolParameter
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Запрос или инструкция для агента",
                required=True
            )
        ]
    
    def run(self, parameters: Dict[str, Any]) -> str:
        """Выполнение — прямой вызов обёрнутого агента"""
        query = parameters.get('query', '')
        
        if not query:
            return "Ошибка: необходим параметр query"
        
        try:
            # Прямой вызов run агента
            return self.agent.run(query)
        except Exception as e:
            return f"Ошибка при вызове {self.name}: {str(e)}"
