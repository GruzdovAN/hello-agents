# test_react_agent.py
from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM, ToolRegistry
from my_react_agent import MyReActAgent

# Загрузить переменные среды
load_dotenv()

def test_react_agent():
    """Проверьте функциональность MyReActAgent."""
    
    # Создать экземпляр LLM
    llm = HelloAgentsLLM()
    
    # Создайте реестр инструментов
    tool_registry = ToolRegistry()
    
    # Зарегистрируйте некоторые основные инструменты для тестирования
    print("🔧Зарегистрировать инструмент тестирования...")
    
    # Зарегистрировать калькулятор
    try:
        from hello_agents import calculate
        tool_registry.register_function("calculate", "Выполняйте математические вычисления и поддерживайте четыре основные арифметические операции.", calculate)
        print("✅ Регистрация калькулятора прошла успешно")
    except ImportError:
        print("⚠️ Калькулятор не найден, регистрация пропущена.")

    # Зарегистрируйте инструмент поиска (если доступен)
    try:
        from hello_agents import search
        tool_registry.register_function("search", "Ищите информацию в Интернете", search)
        print("✅ Регистрация инструмента поиска прошла успешно")
    except ImportError:
        print("⚠️ Инструмент поиска не найден, пропустите регистрацию")
    
    # Создайте собственный ReActAgent.
    agent = MyReActAgent(
        name="Мой помощник в рассуждениях",
        llm=llm,
        tool_registry=tool_registry,
        max_steps=5
    )
    
    print("\n" + "="*60)
    print("Начать тестирование MyReActAgent")
    print("="*60)
    
    # Тест 1: Вопросы по математическим расчетам
    print("\n📊 Тест 1: Вопросы по математическим расчетам")
    math_question = "Помогите пожалуйста посчитать: (25+15)*3 - 8. Какой результат?"
    
    try:
        result1 = agent.run(math_question)
        print(f"\n🎯 Результат теста 1: {result1}")
    except Exception as e:
        print(f"❌ Тест 1 не пройден: {e}")
    
    # Тест 2: Вопросы для поиска
    print("\n🔍 Тест 2: Задача поиска информации")
    search_question = "Когда был выпущен язык программирования Python? Подскажите, пожалуйста, конкретный год."
    
    try:
        result2 = agent.run(search_question)
        print(f"\n🎯 Результаты теста 2: {result2}")
    except Exception as e:
        print(f"❌ Тест 2 не пройден: {e}")
    
    # Тест 3: Сложные вопросы (требующие многоэтапного рассуждения)
    print("\n🧠 Тест 3. Вопросы на сложное рассуждение")
    complex_question = "Сколько мальчиков в классе, если в классе 30 учеников и 60% из них девочки? Пожалуйста, посчитайте сначала количество девочек, а затем количество мальчиков."
    
    try:
        result3 = agent.run(complex_question)
        print(f"\n🎯 Результаты теста 3: {result3}")
    except Exception as e:
        print(f"❌ Тест 3 не пройден: {e}")
    
    # Просмотреть историю разговоров
    print(f"\n📝 История разговоров: {len(agent.get_history())} сообщений")
    
    # Показать статистику использования инструмента
    print(f"\n🛠️ Количество доступных инструментов: {len(tool_registry._tools)}")
    print("Зарегистрированные инструменты:")
    for tool_name in tool_registry._tools.keys():
        print(f"  - {tool_name}")
    
    print("\n🎉 Тест завершен!")

def test_custom_prompt():
    """ReActAgent для тестирования пользовательских слов подсказки"""
    
    print("\n" + "="*60)
    print("MyReActAgent для тестирования пользовательских слов подсказки")
    print("="*60)
    
    # Создайте LLM и реестр инструментов.
    llm = HelloAgentsLLM()
    tool_registry = ToolRegistry()
    
    # Зарегистрировать калькулятор
    try:
        from hello_agents import calculate
        tool_registry.register_function("calculate", calculate, "Инструменты математических вычислений")
    except ImportError:
        pass
    
    # Пользовательские слова-подсказки (более краткая версия)
    custom_prompt = """Вы — помощник ИИ-эксперта по математике.

Доступные инструменты: {инструменты}

Пожалуйста, ответьте в следующем формате:
Мысль: [ваши мысли]
Действие: [имя_инструмента[вход] или Завершить[ответ]]

Вопрос: {вопрос}
История: {история}

Начало:"""
    
    # Создайте агента, который использует пользовательские слова подсказки.
    custom_agent = MyReActAgent(
        name="Помощник эксперта по математике",
        llm=llm,
        tool_registry=tool_registry,
        max_steps=3,
        custom_prompt=custom_prompt
    )
    
    # тестовые вопросы по математике
    math_question = "Вычислить результат 15×8 + 32 ÷ 4"
    
    try:
        result = custom_agent.run(math_question)
        print(f"\n🎯 Результаты теста пользовательского слова-подсказки: {result}")
    except Exception as e:
        print(f"❌ Проверка пользовательского слова-подсказки не удалась: {e}")

if __name__ == "__main__":
    # Запустите базовые тесты
    test_react_agent()
    
    # Запустите пользовательскую проверку слов-подсказок
    test_custom_prompt()
    
    print("\n✨ Все тесты пройдены!")
