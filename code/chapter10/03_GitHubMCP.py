"""
Пример сервиса GitHub MCP

Примечание. Необходимо установить переменные среды.
    Windows: $env:GITHUB_PERSONAL_ACCESS_TOKEN="ваш_токен_здесь"
    Linux/macOS: экспортируйте GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
"""

from hello_agents.tools import MCPTool

# Создайте инструмент GitHub MCP.
github_tool = MCPTool(
    server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
)

# 1. Перечислите доступные инструменты
print("📋Доступные инструменты:")
result = github_tool.run({"action": "list_tools"})
print(result)

# 2. Поиск склада
print("\n🔍 Поиск склада:")
result = github_tool.run({
    "action": "call_tool",
    "tool_name": "search_repositories",
    "arguments": {
        "query": "AI agents language:python",
        "page": 1,
        "perPage": 3
    }
})
print(result)

