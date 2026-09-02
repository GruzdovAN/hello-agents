"""
Обёртка MCP-инструмента — превращает один MCP-инструмент в Tool HelloAgents

Этот модуль разворачивает каждый инструмент MCP-сервера в отдельный объект Tool HelloAgents,
чтобы агент (Agent) мог вызывать MCP-инструменты так же, как обычные инструменты.
"""

from typing import Dict, Any, List
from ..base import Tool, ToolParameter


class MCPWrappedTool(Tool):
    """
    Обёртка MCP-инструмента — превращает один MCP-инструмент в Tool HelloAgents
    
    Класс оборачивает один инструмент MCP-сервера (например read_file) в отдельный объект Tool.
    При вызове агенту достаточно передать параметры, без знания внутренней структуры MCP.
    
    Пример:
        >>> # Внутреннее использование, создаётся автоматически из MCPTool
        >>> wrapped_tool = MCPWrappedTool(
        ...     mcp_tool=mcp_tool_instance,
        ...     tool_info={
        ...         "name": "read_file",
        ...         "description": "Read a file...",
        ...         "input_schema": {...}
        ...     }
        ... )
    """
    
    def __init__(self,
                 mcp_tool: 'MCPTool',  # type: ignore
                 tool_info: Dict[str, Any],
                 prefix: str = ""):
        """
        Инициализирует обёрнутый MCP-инструмент

        Args:
            mcp_tool: родительский экземпляр MCPTool
            tool_info: информация об MCP-инструменте (name, description, input_schema)
            prefix: префикс имени (например "filesystem_")
        """
        self.mcp_tool = mcp_tool
        self.tool_info = tool_info
        self.mcp_tool_name = tool_info.get('name', 'unknown')

        # Имя инструмента: prefix + mcp_tool_name
        tool_name = f"{prefix}{self.mcp_tool_name}" if prefix else self.mcp_tool_name

        # Описание
        description = tool_info.get('description', f'MCP-инструмент: {self.mcp_tool_name}')

        # Разбор схемы параметров
        self._parameters = self._parse_input_schema(tool_info.get('input_schema', {}))

        # Инициализация базового класса
        super().__init__(
            name=tool_name,
            description=description
        )
    
    def _parse_input_schema(self, input_schema: Dict[str, Any]) -> List[ToolParameter]:
        """
        Преобразует input_schema MCP в список ToolParameter HelloAgents

        Args:
            input_schema: input_schema MCP-инструмента (формат JSON Schema)

        Returns:
            Список ToolParameter
        """
        parameters = []

        properties = input_schema.get('properties', {})
        required_fields = input_schema.get('required', [])

        for param_name, param_info in properties.items():
            param_type = param_info.get('type', 'string')
            param_desc = param_info.get('description', '')
            is_required = param_name in required_fields

            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,  # тип JSON Schema передаётся как строка
                description=param_desc,
                required=is_required
            ))

        return parameters
    
    def get_parameters(self) -> List[ToolParameter]:
        """
        Возвращает определения параметров инструмента

        Returns:
            Список ToolParameter
        """
        return self._parameters

    def run(self, params: Dict[str, Any]) -> str:
        """
        Выполняет MCP-инструмент

        Args:
            params: параметры инструмента (передаются напрямую в MCP)

        Returns:
            Результат выполнения
        """
        # Параметры вызова MCP
        mcp_params = {
            "action": "call_tool",
            "tool_name": self.mcp_tool_name,
            "arguments": params
        }

        # Вызов родительского MCPTool
        return self.mcp_tool.run(mcp_params)
