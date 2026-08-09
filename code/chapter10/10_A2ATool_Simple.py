"""
10.3.4 Использование инструментов A2A в агентах
(1) Используйте оболочку A2ATool.
"""

from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import A2ATool
from dotenv import load_dotenv

load_dotenv()
llm = HelloAgentsLLM()

# Предположим, что служба агента-исследователя уже работает по адресу http://localhost:5000.

# Создать агент-координатор
coordinator = SimpleAgent(name="координатор", llm=llm)

# Добавьте инструмент A2A для подключения к агенту-исследователю.
researcher_tool = A2ATool(agent_url="http://localhost:5000")
coordinator.add_tool(researcher_tool)

# Координатор может позвонить агенту-исследователю
# Используйте action="ask", чтобы задать вопрос агенту.
response = coordinator.run("Используйте инструмент a2a, чтобы спросить агента: пожалуйста, изучите применение ИИ в образовании.")
print(response)

