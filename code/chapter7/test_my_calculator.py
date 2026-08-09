# test_my_calculator.py
from dotenv import load_dotenv
from my_calculator_tool import create_calculator_registry

# Загрузить переменные среды
load_dotenv()

def test_calculator_tool():
    """Тестирование пользовательского калькулятора"""

    # Создайте реестр, содержащий калькулятор
    registry = create_calculator_registry()

    print("🧪 Проверьте свой собственный калькулятор\n")

    # Простой тестовый пример
    test_cases = [
        "2 + 3",           # базовое дополнение
        "10 - 4",          # базовое вычитание
        "5 * 6",           # базовое умножение
        "15 / 3",          # основное подразделение
        "sqrt(16)",        # квадратный корень
    ]

    for i, expression in enumerate(test_cases, 1):
        print(f"Тест {i}: {выражение}")
        result = registry.execute_tool("my_calculator", expression)
        print(f"Результат: {result}\n")

def test_with_simple_agent():
    """Тестовая интеграция с SimpleAgent"""
    from hello_agents import HelloAgentsLLM

    # Создать LLM-клиент
    llm = HelloAgentsLLM()

    # Создайте реестр, содержащий калькулятор
    registry = create_calculator_registry()

    print("🤖 Интеграционное тестирование с SimpleAgent:")

    # Смоделируйте сценарий SimpleAgent с помощью инструментов
    user_question = "Помогите пожалуйста посчитать sqrt(16) + 2 * 3"

    print(f"Вопрос пользователя: {user_question}")

    # Используйте инструменты для расчета
    calc_result = registry.execute_tool("my_calculator", "sqrt(16) + 2 * 3")
    print(f"Результат расчета: {calc_result}")

    # Сформулируйте окончательный ответ
    final_messages = [
        {"role": "user", "content": f"Результат расчета: {calc_result}. Пожалуйста, ответьте на вопрос пользователя на естественном языке: {user_question}"}
    ]

    print("\n🎯 Ответ SimpleAgent:")
    response = llm.think(final_messages)
    for chunk in response:
        print(chunk, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    test_calculator_tool()
    test_with_simple_agent()