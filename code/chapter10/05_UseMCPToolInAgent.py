from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool

print("=" * 70)
print("Способ 1. Используйте встроенный демонстрационный сервер.")
print("=" * 70)

agent = SimpleAgent(name="помощник", llm=HelloAgentsLLM())

# Никакой настройки не требуется, автоматически используется встроенный демонстрационный сервер.
# Встроенный сервер обеспечивает: сложение, вычитание, умножение, деление, приветствие, get_system_info.
mcp_tool = MCPTool()  # Имя по умолчанию="mcp"
agent.add_tool(mcp_tool)

# Агенты могут использовать встроенные инструменты
response = agent.run("Посчитать 123 + 456")
print(response)  # Агент автоматически вызовет инструмент добавления

print("\n" + "=" * 70)
print("Способ 2. Подключитесь к внешнему серверу MCP (используйте несколько серверов).")
print("=" * 70)

# Важно: Укажите другое имя для каждого сервера MCP, чтобы избежать конфликтов имен инструментов.

# Пример 1. Подключение к серверу файловой системы, предоставленному сообществом.
fs_tool = MCPTool(
    name="filesystem",  # Укажите уникальное имя
    description="Доступ к локальной файловой системе",
    server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."]
)
agent.add_tool(fs_tool)

# Пример 2. Подключение к пользовательскому серверу Python MCP
# О том, как написать собственный сервер MCP, см. главу 10.5.
custom_tool = MCPTool(
    name="custom_server",  # использовать другое имя
    description="Пользовательский сервер бизнес-логики",
    server_command=["python", "my_mcp_server.py"]
)
agent.add_tool(custom_tool)

print("\nИнструменты, принадлежащие агенту в настоящее время:")
print(f"- {mcp_tool.name}: {mcp_tool.description}")
print(f"- {fs_tool.name}: {fs_tool.description}")
print(f"- {custom_tool.name}: {custom_tool.description}")

# Теперь агент может использовать эти инструменты автоматически!
response = agent.run("Пожалуйста, прочтите файл my_README.md и кратко изложите его основное содержимое.")
print(response)