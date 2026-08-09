# test_simple_agent.py
from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM, ToolRegistry
from hello_agents.tools import CalculatorTool
from my_simple_agent import MySimpleAgent

# Загрузить переменные среды
load_dotenv()

# Создать экземпляр LLM
llm = HelloAgentsLLM()

# Тест 1. Базовый агент диалога (без инструментов)
print("=== Тест 1: Базовый разговор ===")
basic_agent = MySimpleAgent(
    name="Базовый помощник",
    llm=llm,
    system_prompt="Вы дружелюбный ИИ-помощник, пожалуйста, отвечайте на вопросы кратко и ясно."
)

response1 = basic_agent.run("Здравствуйте, представьтесь, пожалуйста")
print(f"Основной ответ в диалоге: {response1}\n")

# Тест 2: Агент с инструментами
print("=== Тест 2: Диалоги с расширенными инструментами ===")
tool_registry = ToolRegistry()
calculator = CalculatorTool()
tool_registry.register_tool(calculator)

enhanced_agent = MySimpleAgent(
    name="Расширенный помощник",
    llm=llm,
    system_prompt="Вы умный помощник, который может использовать инструменты, помогающие пользователям.",
    tool_registry=tool_registry,
    enable_tool_calling=True
)

response2 = enhanced_agent.run("Помогите пожалуйста посчитать 15*8+32.")
print(f"Расширенный ответ инструмента: {response2}\n")

# Тест 3. Потоковая передача ответа
print("=== Тест 3: потоковая передача ответа ===")
print("Потоковое ответ: ", end="")
for chunk in basic_agent.stream_run("Объясните пожалуйста, что такое искусственный интеллект?"):
    pass  # Содержимое распечатывалось в потокеstream_run в реальном времени.

# Тест 4. Динамическое добавление инструментов
print("\n=== Тест 4. Динамическое управление инструментом ===")
print(f"Перед добавлением инструментов: {basic_agent.has_tools()}")
basic_agent.add_tool(calculator)
print(f"После добавления инструментов: {basic_agent.has_tools()}")
print(f"Доступные инструменты: {basic_agent.list_tools()}")

# Просмотреть историю разговоров
print(f"\nИстория разговоров: {len(basic_agent.get_history())} сообщений")