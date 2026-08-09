from hello_agents.tools import MCPTool

# 1. Memory Transport — перенос памяти (для тестирования)
# Без указания каких-либо параметров используйте встроенный демонстрационный сервер
mcp_tool = MCPTool()

# 2. Stdio Transport — стандартная передача ввода и вывода (локальная разработка)
# Запустите локальный сервер, используя список команд
mcp_tool = MCPTool(server_command=["python", "examples/mcp_example_server.py"])

# 3. Stdio Transport с Args — передача команды с параметрами
# Дополнительные параметры могут быть переданы
mcp_tool = MCPTool(server_command=["python", "examples/mcp_example_server.py", "--debug"])

# 4. Stdio Transport — Сервер сообщества (режим npx)
# Запустите сервер MCP сообщества, используя npx
mcp_tool = MCPTool(server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

# 5. HTTP/SSE/StreamableHTTP Transport
# Примечание. MCPTool в основном используется для передачи данных из Stdio и памяти.
# Для удаленной передачи, например HTTP/SSE, рекомендуется напрямую использовать MCPClient.

from hello_agents.tools import MCPTool

# Использовать встроенный сервер презентаций (передача из памяти)
mcp_tool = MCPTool()

# Список доступных инструментов
result = mcp_tool.run({"action": "list_tools"})
print(result)

# Инструмент вызова
result = mcp_tool.run({
    "action": "call_tool",
    "tool_name": "add",
    "arguments": {"a": 10, "b": 20}
})
print(result)

from hello_agents.tools import MCPTool

# Способ 1: использовать собственный сервер Python
mcp_tool = MCPTool(server_command=["python", "my_mcp_server.py"])

# Способ 2. Использование сервера сообщества (файловой системы)
mcp_tool = MCPTool(server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

# Список инструментов
result = mcp_tool.run({"action": "list_tools"})
print(result)

# Инструмент вызова
result = mcp_tool.run({
    "action": "call_tool",
    "tool_name": "read_file",
    "arguments": {"path": "my_README.md"}
})
print(result)


# Примечание. MCPTool в основном используется для передачи Stdio и памяти.
# Для удаленных передач, таких как HTTP/SSE, рекомендуется использовать базовый MCPClient.

import asyncio
from hello_agents.protocols.mcp.client import MCPClient

async def test_http_transport():
    # Подключитесь к удаленному серверу HTTP MCP.
    client = MCPClient("http://api.example.com/mcp")

    async with client:
        # Получить информацию о сервере
        tools = await client.list_tools()
        print(f"Инструменты удаленного сервера: {len(tools)}")

        # Вызов удаленного инструмента
        result = await client.call_tool("process_data", {
            "data": "Hello, World!",
            "operation": "uppercase"
        })
        print(f"Результат удаленной обработки: {result}")

# ПРИМЕЧАНИЕ. Требуется реальный сервер HTTP MCP.
# asyncio.run(test_http_transport())