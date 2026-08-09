"""
Пример базового использования ContextBuilder

Показывает, как использовать ContextBuilder для создания оптимизированных контекстов, в том числе:
1. Инициализируйте ContextBuilder
2. Подготовьте историю разговоров
3. Добавьте воспоминания
4. Создайте структурированный контекст
"""
from dotenv import load_dotenv
load_dotenv()
from hello_agents.context import ContextBuilder, ContextConfig
from hello_agents.tools import MemoryTool, RAGTool
from hello_agents.core.message import Message
from datetime import datetime


def main():
    print("=" * 80)
    print("Пример базового использования ContextBuilder")
    print("=" * 80 + "\n")

    # 1. Инструмент инициализации (дополнительно)
    print("1. Инструмент инициализации...")
    # memory_tool = MemoryTool(user_id="user123")
    # rag_tool = RAGTool(knowledge_base_path="./knowledge_base")

    # 2. Создайте ContextBuilder
    print("2. Создайте ContextBuilder...")
    config = ContextConfig(
        max_tokens=3000,
        reserve_ratio=0.2,
        min_relevance=0,#Минимальный порог корреляции, 0 означает, что вся историческая информация будет сохранена.
        enable_compression=True
    )

    builder = ContextBuilder(
        # memory_tool=memory_tool,
        # rag_tool=rag_tool,
        config=config
    )

    # 3. Подготовьте историю разговоров
    print("3. Подготовьте историю разговоров...")
    conversation_history = [
        Message(content="Я разрабатываю инструмент анализа данных", role="user", timestamp=datetime.now()),
        Message(content="Большой! Инструментам анализа данных часто приходится обрабатывать большие объемы данных. Какой стек технологий вы планируете использовать?", role="assistant", timestamp=datetime.now()),
        Message(content="Я планирую использовать Python и Pandas и завершил модуль чтения CSV.", role="user", timestamp=datetime.now()),
        Message(content="Отличный выбор! Pandas очень эффективен, когда дело доходит до обработки данных. Далее вы можете рассмотреть возможность очистки и преобразования данных.", role="assistant", timestamp=datetime.now()),
    ]

    # 4. Добавьте немного воспоминаний
    print("4. Добавьте воспоминания...")
    # memory_tool.run({
    #     "action": "add",
    #     "content": "Пользователь разрабатывает инструменты анализа данных с использованием Python и Pandas",
    #     "memory_type": "semantic",
    #     "importance": 0.8
    # })

    # memory_tool.run({
    #     "action": "add",
    #     "content": "Разработка модуля чтения CSV завершена",
    #     "memory_type": "episodic",
    #     "importance": 0.7
    # })

    # 5. Создайте контекст
    print("5. Создайте контекст...\n")
    context_str = builder.build(
        user_query="Как оптимизировать использование памяти Pandas?",
        conversation_history=conversation_history,
        system_instructions="Вы старший консультант по разработке данных Python. Ваш ответ должен: 1) предоставить конкретные и осуществимые предложения 2) объяснить технические принципы 3) привести примеры кода"
    )

    print("=" * 80)
    print("Созданный контекст (структурированная строка):")
    print("=" * 80)
    print(context_str)
    print("=" * 80)
    print()

    # 6. Преобразуйте строку контекста в формат сообщения для использования LLM.
    print("6. Передайте контекст в LLM...")
    messages = [
        {"role": "system", "content": context_str},
        {"role": "user", "content": "пожалуйста, ответьте"}

    ]

    from hello_agents.core.llm import HelloAgentsLLM
    llm = HelloAgentsLLM()
    # Примечание. LLM необходимо настроить для фактического использования.
    response = llm.invoke(messages)
    print(f"LLM ответил: {response}")

    print("✅ Демо-версия ContextBuilder завершена!")
    print("\nСовет: ContextBuilder возвращает структурированную строку контекста.")
    print("      Его можно передать непосредственно в LLM как системное сообщение.")


if __name__ == "__main__":
    main()
