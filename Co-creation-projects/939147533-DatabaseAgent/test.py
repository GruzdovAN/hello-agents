"""
Агент-помощник для базы данных — тестовый скрипт
Для проверки работы отдельных компонентов
"""
import os
from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM
from react_agent import DatabaseAgent, DatabaseConfig
from tools import OracleQueryTool, SQLGeneratorTool

load_dotenv()


def test_database_connection():
    """Проверить подключение к базе данных"""
    print("=" * 60)
    print("Тест 1: Подключение к базе данных")
    print("=" * 60)
    
    db_config = DatabaseConfig()
    
    if not db_config.validate():
        print("❌ Конфигурация базы данных неполная")
        return False
    
    print(f"Информация о конфигурации: {db_config.get_connection_string()}")
    
    oracle_tool = OracleQueryTool(db_config)
    
    if oracle_tool.connect():
        print("✅ Подключение к базе данных успешно")
        schema_info = oracle_tool.get_schema_info()
        print("\nСтруктура таблиц базы данных:")
        print(schema_info)
        oracle_tool.disconnect()
        return True
    else:
        print("❌ Не удалось подключиться к базе данных")
        return False


def test_sql_generation():
    """Проверить генерацию SQL"""
    print("\n" + "=" * 60)
    print("Тест 2: Генерация SQL")
    print("=" * 60)
    
    try:
        llm = HelloAgentsLLM()
        
        sql_generator = SQLGeneratorTool(llm)
        
        test_queries = [
            "Получить информацию обо всех сотрудниках",
            "Найти сотрудников с зарплатой больше 5000",
            "Подсчитать количество сотрудников по отделам"
        ]
        
        for query in test_queries:
            print(f"\nЕстественный язык: {query}")
            sql = sql_generator.generate_sql(query, "Таблица EMPLOYEES: ID (NUMBER), NAME (VARCHAR2), SALARY (NUMBER), DEPARTMENT (VARCHAR2)")
            print(f"Сгенерированный SQL: {sql}")
            
            is_valid, msg = sql_generator.validate_sql(sql)
            print(f"Результат проверки: {msg}")
        
        return True
    except Exception as e:
        print(f"❌ Тест генерации SQL не пройден: {e}")
        return False


def test_agent_query():
    """Проверить запросы через агента"""
    print("\n" + "=" * 60)
    print("Тест 3: Запрос через агента")
    print("=" * 60)
    
    try:
        llm = HelloAgentsLLM()
        
        db_config = DatabaseConfig()
        
        if not db_config.validate():
            print("❌ Конфигурация базы данных неполная")
            return False
        
        agent = DatabaseAgent(
            name="TestAgent",
            llm=llm,
            db_config=db_config,
            max_steps=5
        )
        
        test_query = "Получить информацию обо всех сотрудниках"
        print(f"\nТестовый запрос: {test_query}")
        result = agent.run(test_query)
        print(f"\nРезультат запроса:\n{result}")
        
        return True
    except Exception as e:
        print(f"❌ Тест запроса через агента не пройден: {e}")
        return False


def main():
    """Запустить все тесты"""
    print("🧪 Агент-помощник для базы данных — тестовый набор")
    print("=" * 60)
    
    results = []
    
    results.append(("Подключение к базе данных", test_database_connection()))
    results.append(("Генерация SQL", test_sql_generation()))
    results.append(("Запрос через агента", test_agent_query()))
    
    print("\n" + "=" * 60)
    print("Сводка результатов тестов")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ Пройден" if result else "❌ Не пройден"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nИтого: {passed}/{total} тестов пройдено")


if __name__ == "__main__":
    main()
