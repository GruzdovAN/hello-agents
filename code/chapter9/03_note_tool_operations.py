"""
Пример базовой работы NoteTool

Демонстрирует основные операции NoteTool:
1. Создать заметку (создать)
2. Читать заметки (читать)
3. Обновление заметок (обновление)
4. Поиск заметок (поиск)
5. Примечания к списку (список)
6. Краткое содержание заметки (резюме)
7. Удаление заметок (удалить)
"""

from hello_agents.tools import NoteTool
import re


def extract_note_id(output: str) -> str:
    """Извлечь note_id из выходного текста NoteTool"""
    match = re.search(r"ID:\s*(note_[0-9_]+)", output)
    if not match:
        raise ValueError(f"Невозможно проанализировать note_id:\n{output} из вывода")
    return match.group(1)


def main():
    print("=" * 80)
    print("Пример базовой работы NoteTool")
    print("=" * 80 + "\n")

    # Инициализировать NoteTool
    notes = NoteTool(workspace="./project_notes")

    # 1. Создайте заметку
    print("1. Создайте заметку...")
    create_output_1 = notes.run({
        "action": "create",
        "title": "Проект рефакторинга — этап 1",
        "content": """## Статус завершения
Реконструкция слоя модели данных завершена, уровень покрытия тестами достиг 85%.

## Следующий шаг
Рефакторинг уровня бизнес-логики""",
        "note_type": "task_state",
        "tags": ["refactoring", "phase1"]
    })
    print(create_output_1 + "\n")
    note_id_1 = extract_note_id(create_output_1)

    # Создать вторую заметку
    create_output_2 = notes.run({
        "action": "create",
        "title": "Проблема конфликта зависимостей",
        "content": """## Описание проблемы
Было обнаружено, что некоторые версии сторонних библиотек несовместимы и требуют устранения.

## Сфера влияния
3 модуля уровня бизнес-логики

## Следующий шаг
1. Используйте изоляцию виртуальной среды
2. Заблокированная версия
3. Используйте pipdeptree для анализа деревьев зависимостей.""",
        "note_type": "blocker",
        "tags": ["dependency", "urgent"]
    })
    print(create_output_2 + "\n")
    note_id_2 = extract_note_id(create_output_2)

    # 2. Прочтите заметки
    print("2. Прочитайте заметки...")
    note_detail = notes.run({
        "action": "read",
        "note_id": note_id_1
    })
    print(note_detail + "\n")

    # 3. Обновите заметки
    print("3. Обновить заметки...")
    update_result = notes.run({
        "action": "update",
        "note_id": note_id_1,
        "content": """## Статус завершения
Реконструкция слоя модели данных завершена, уровень покрытия тестами достиг 85%.

## Вопрос
Если возникает конфликт версий зависимостей, это фиксируется в отдельном примечании.

## Следующий шаг
Сначала разрешите конфликты зависимостей, а затем продолжайте восстанавливать уровень бизнес-логики."""
    })
    print(update_result + "\n")

    # 4. Поиск заметок
    print("4. Поиск заметок...")
    search_results = notes.run({
        "action": "search",
        "query": "полагаться",
        "limit": 5
    })
    print(search_results + "\n")

    # 5. Список примечаний
    print("5. Перечислите все примечания к типам блокировщиков...")
    blockers = notes.run({
        "action": "list",
        "note_type": "blocker",
        "limit": 10
    })
    print(blockers + "\n")

    # 6. Краткое описание заметок
    print("6. Создать сводку заметки...")
    summary_output = notes.run({
        "action": "summary"
    })
    print(summary_output + "\n")

    # 7. Удаление заметок (демо, будьте осторожны при реальном использовании)
    print("7. Удаление заметок (демо)...")
    # delete_result = notes.run({
    #     "action": "delete",
    #     "note_id": note_id_2
    # })
    # print(delete_result + "\n")
    print(f"(Фактическое удаление пропущено, идентификатор заметки: {note_id_2})\n")

    print("=" * 80)
    print("Демонстрация работы NoteTool завершена!")
    print("=" * 80)


if __name__ == "__main__":
    main()
