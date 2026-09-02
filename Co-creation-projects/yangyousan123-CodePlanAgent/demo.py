"""Пример использования CodePlanAgent"""

import os
from dotenv import load_dotenv
from hello_agents.core.llm import HelloAgentsLLM
from code_plan_agent import CodePlanAgent, create_code_plan_agent


def load_env():
    """Загрузить переменные окружения"""
    load_dotenv()

    required_vars = ["LLM_MODEL_ID", "LLM_API_KEY", "LLM_BASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Не заданы переменные окружения: {', '.join(missing_vars)}")
        print("Настройте их в файле .env")
        return False

    return True


def main():
    """Основная функция — демонстрация CodePlanAgent"""
    print("🚀 Демо CodePlanAgent")
    print("=" * 60)

    if not load_env():
        return

    print("\n🔧 Инициализация LLM...")
    llm = HelloAgentsLLM(
        model=os.getenv("LLM_MODEL_ID"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        temperature=0.2,
        max_tokens=4096,
    )

    print(f"✅ LLM инициализирован: {llm.model}")

    print("\n🧠 Создание CodePlanAgent...")
    agent = create_code_plan_agent(llm)
    print(f"✅ CodePlanAgent создан: {agent.name}")

    print("\n" + "=" * 60)
    print("📝 Пример 1: приложение списка задач")
    print("=" * 60)

    requirements1 = """Создайте простое приложение списка задач (Todo) на Python и Flask:

Функциональные требования:
1. Добавление задач (название, описание, срок)
2. Удаление задач
3. Отметка выполнено / не выполнено
4. Фильтрация по статусу (все / выполнено / не выполнено)
5. Постоянное хранение (SQLite)

Технические требования:
- Фреймворк Flask
- SQLAlchemy ORM
- RESTful API
- Поддержка JSON
- Базовая обработка ошибок"""

    plan1 = agent.run(requirements1)

    with open("./outputs/todo_app_plan.md", "w", encoding="utf-8") as f:
        f.write(plan1)
    print("\n📄 План кода сохранён: ./outputs/todo_app_plan.md")

    print("\n🎉 Демо завершено!")


if __name__ == "__main__":
    main()
