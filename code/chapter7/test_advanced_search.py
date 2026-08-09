# test_advanced_search.py
from dotenv import load_dotenv
from my_advanced_search import create_advanced_search_registry, MyAdvancedSearchTool

# Загрузить переменные среды
load_dotenv()

def test_advanced_search():
    """Протестируйте инструменты расширенного поиска"""

    # Создайте реестр с расширенными инструментами поиска.
    registry = create_advanced_search_registry()

    print("🔍 Протестируйте инструменты расширенного поиска\n")

    # Тестовый запрос
    test_queries = [
        "История языка программирования Python",
        "Последние разработки в области искусственного интеллекта",
        "Технологические тенденции в 2024 году"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"Тест {i}: {запрос}")
        result = registry.execute_tool("advanced_search", query)
        print(f"Результат: {result}\n")
        print("-" * 60 + "\n")

def test_api_configuration():
    """Проверка конфигурации тестового API"""
    print("🔧 Проверка конфигурации тестового API:")

    # Создайте экземпляр инструмента поиска напрямую
    search_tool = MyAdvancedSearchTool()

    # Если API не настроен, отобразится запрос на настройку.
    result = search_tool.search("алгоритм машинного обучения")
    print(f"Результаты поиска: {result}")

def test_with_agent():
    """Тестовая интеграция с Агентом"""
    print("\n🤖 Тестирование интеграции с Агентом:")
    print("Инструменты расширенного поиска готовы к интеграции с Агентом")

    # Показать описание инструмента
    registry = create_advanced_search_registry()
    tools_desc = registry.get_tools_description()
    print(f"Описание инструмента:\n{tools_desc}")

if __name__ == "__main__":
    test_advanced_search()
    test_api_configuration()
    test_with_agent()