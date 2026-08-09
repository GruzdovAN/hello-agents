from hello_agents.tools import MCPTool, A2ATool, ANPTool

# 1. MCP: инструменты доступа
mcp_tool = MCPTool()
result = mcp_tool.run({
    "action": "call_tool",
    "tool_name": "add",
    "arguments": {"a": 10, "b": 20}
})
print(f"Результат расчета MCP: {result}")  # Выход: 30,0

# 2. ANP: обнаружение услуг
anp_tool = ANPTool()
anp_tool.run({
    "action": "register_service",
    "service_id": "calculator",
    "service_type": "math",
    "endpoint": "http://localhost:8080"
})
services = anp_tool.run({"action": "discover_services"})
print(f"Обнаруженные услуги: {services}")

# 3. A2A: Связь с агентом
a2a_tool = A2ATool("http://localhost:5000")
print("Инструмент A2A успешно создан")