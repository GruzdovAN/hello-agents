from hello_agents.protocols.a2a.implementation import A2AServer, A2A_AVAILABLE

def create_custom_agent():
    """Создайте собственного агента"""
    if not A2A_AVAILABLE:
        print("Сначала установите A2A SDK: pip install a2a-sdk")
        return None

    # Создать агента
    agent = A2AServer(
        name="my-custom-agent",
        description="Мой индивидуальный агент",
        capabilities={"custom": ["skill1", "skill2"]}
    )

    # Добавить навыки
    @agent.skill("greet")
    def greet_user(name: str) -> str:
        """приветствовать пользователя"""
        return f"Здравствуйте, {имя}! Я индивидуальный агент."

    @agent.skill("calculate")
    def simple_calculate(expression: str) -> str:
        """Простой расчет"""
        try:
            # Безопасные вычисления (поддерживаются только базовые операции)
            allowed_chars = set('0123456789+-*/(). ')
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return f"Результат расчета: {выражение} = {результат}"
            else:
                return "Ошибка: поддерживаются только базовые математические операции."
        except Exception as e:
            return f"Ошибка расчета: {e}"

    return agent

# Создание и тестирование пользовательских агентов
custom_agent = create_custom_agent()
if custom_agent:
    # Тестирование навыков
    print("Проверьте свои навыки приветствия:")
    result1 = custom_agent.skills["greet"]("Чжан Сан")
    print(result1)

    print("\nПроверьте свои компьютерные навыки:")
    result2 = custom_agent.skills["calculate"]("10 + 5 * 2")
    print(result2)