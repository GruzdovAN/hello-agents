from hello_agents.protocols.a2a.implementation import A2AServer, A2A_AVAILABLE

def create_calculator_agent():
    """Создать агент калькулятора"""
    if not A2A_AVAILABLE:
        print("❌ A2A SDK не установлен, запустите: pip install a2a-sdk")
        return None

    print("🧮Создать агент калькулятора")

    # Создать сервер A2A
    calculator = A2AServer(
        name="calculator-agent",
        description="Профессиональный математический вычислительный агент",
        version="1.0.0",
        capabilities={
            "math": ["addition", "subtraction", "multiplication", "division"],
            "advanced": ["power", "sqrt", "factorial"]
        }
    )

    # Добавьте базовые компьютерные навыки
    @calculator.skill("add")
    def add_numbers(query: str) -> str:
        """Добавление"""
        try:
            # Простой разбор формата «посчитать 5+3»
            parts = query.replace("вычислить", "").replace("добавлять", "+").replace("плюс", "+")
            if "+" in parts:
                numbers = [float(x.strip()) for x in parts.split("+")]
                result = sum(numbers)
                return f"Результат расчета: {' + '.join(map(str, Numbers))} = {result}"
            else:
                return "Пожалуйста, используйте формат: посчитать 5 + 3."
        except Exception as e:
            return f"Ошибка расчета: {e}"

    @calculator.skill("multiply")
    def multiply_numbers(query: str) -> str:
        """Расчет умножения"""
        try:
            parts = query.replace("вычислить", "").replace("умножить на", "*").replace("×", "*")
            if "*" in parts:
                numbers = [float(x.strip()) for x in parts.split("*")]
                result = 1
                for num in numbers:
                    result *= num
                return f"Результат расчета: {' × '.join(map(str, Numbers))} = {result}"
            else:
                return "Пожалуйста, используйте формат: расчет 5 * 3."
        except Exception as e:
            return f"Ошибка расчета: {e}"

    @calculator.skill("info")
    def get_info(query: str) -> str:
        """Получить информацию об агенте"""
        return f"Меня зовут {calculator.name}, и я могу выполнять базовые математические вычисления. Поддерживаемые навыки: {list(calculator.skills.keys())}"

    print(f"✅ Агент калькулятора успешно создан и поддерживает навыки: {list(calculator.skills.keys())}")
    return calculator

# Создать агента
calc_agent = create_calculator_agent()
if calc_agent:
    # Тестирование навыков
    print("\n🧪 Проверьте навыки агента:")
    test_queries = [
        "Получить информацию",
        "Посчитайте 10 + 5",
        "Посчитайте 6*7"
    ]

    for query in test_queries:
        if "информация" in query:
            result = calc_agent.skills["info"](query)
        elif "+" in query:
            result = calc_agent.skills["add"](query)
        elif "*" in query or "×" in query:
            result = calc_agent.skills["multiply"](query)
        else:
            result = "Неизвестный тип запроса"

        print(f"  📝 Запрос: {query}")
        print(f"  🤖 Ответ: {result}")
        print()