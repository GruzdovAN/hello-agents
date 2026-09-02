"""
Агент-помощник для базы данных — главная программа
Демонстрация использования DatabaseAgent для запросов на естественном языке
"""
import os
from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM
from react_agent import DatabaseAgent, DatabaseConfig

load_dotenv()


def main():
    print("=" * 60)
    print("🤖 Агент-помощник для базы данных")
    print("=" * 60)
    
    llm = HelloAgentsLLM()
    
    db_config = DatabaseConfig()
    
    if not db_config.validate():
        print("❌ Конфигурация базы данных неполная, проверьте файл .env")
        print("Необходимо настроить: DB_HOST, DB_PORT, DB_SERVICE_NAME, DB_USERNAME, DB_PASSWORD")
        return
    
    agent = DatabaseAgent(
        name="DatabaseAssistant",
        llm=llm,
        db_config=db_config,
        max_steps=5
    )
    
    print("\n📝 Примеры запросов:")
    print("1. Получить информацию обо всех сотрудниках")
    print("2. Найти сотрудников с зарплатой больше 5000")
    print("3. Подсчитать количество сотрудников по отделам")
    print("4. Получить 5 последних принятых на работу сотрудников")
    print("5. Выход")
    
    while True:
        print("\n" + "=" * 60)
        user_input = input("Введите запрос (или '5' для выхода): ").strip()
        
        if user_input.lower() in ['5', 'exit', 'quit', 'выход']:
            print("👋 Спасибо за использование агента-помощника для базы данных!")
            break

        if not user_input:
            print("⚠️ Введите корректный запрос")
            continue
        
        try:
            result = agent.run(user_input)
            print("\n" + "=" * 60)
            print("📊 Результат запроса:")
            print("=" * 60)
            print(result)
        except Exception as e:
            print(f"❌ Ошибка при выполнении запроса: {e}")


if __name__ == "__main__":
    main()
