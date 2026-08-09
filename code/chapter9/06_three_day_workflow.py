"""
Трехдневная демонстрация рабочего процесса CodebaseMaintainer

Полностью демонстрирует работу агента дальнего действия за три дня:
- День 1: Изучение кодовой базы (автономное исследование агента)
- День 2. Анализ качества кода (независимый от агента анализ).
- Третий день: Задачи планирования и реконструкции (Агентское независимое планирование)
- Через неделю: проверьте прогресс.

"""

import os
# Настройте встроенную модель (выберите один из трех)
# Вариант 1: TF-IDF (самый простой, без дополнительных зависимостей)
os.environ['EMBED_MODEL_TYPE'] = 'tfidf'
os.environ['EMBED_MODEL_NAME'] = ''  # Важно: Необходимо очистить, иначе будут переданы несовместимые параметры.
from dotenv import load_dotenv
load_dotenv()
# Вариант 2: Локальный преобразователь (требуется: pip install преобразователи предложений и токен HF)
# os.environ['EMBED_MODEL_TYPE'] = 'local'
# os.environ['EMBED_MODEL_NAME'] = 'sentence-transformers/all-MiniLM-L6-v2'
# os.environ['HF_TOKEN'] = 'your_hf_token_here' # или используйте вход в Huggingface-cli
# Вариант 3: Тонги Цяньвэнь (требуется ключ API)
# os.environ['EMBED_MODEL_TYPE'] = 'dashscope'
# os.environ['EMBED_MODEL_NAME'] = 'text-embedding-v3'
# os.environ['EMBED_API_KEY'] = 'your_api_key_here'

from hello_agents import HelloAgentsLLM
from datetime import datetime
import json
import time

# Импортировать CodebaseMaintainer
import sys
sys.path.append('.')
from codebase_maintainer import CodebaseMaintainer


def day_1_exploration(maintainer):
    """День 1. Изучение базы кода (агентный способ)
    
    На этом этапе мы даем Агенту только высокоуровневые цели,
    Агент самостоятельно решит:
    - Какие команды оболочки использовать для изучения базы кода.
    - Какие файлы просматривать
    - Стоит ли делать заметки
    """
    print("\n" + "=" * 80)
    print("День 1. Изучение кодовой базы (самоисследование агента)")
    print("=" * 80 + "\n")

    # 1. Первоначальное исследование. Агент самостоятельно решает, как исследовать.
    print("### 1. Предварительное изучение структуры проекта ###")
    print("💡 Совет: агент сам решит, какие команды использовать (например, find, ls, cat)\n")
    response = maintainer.explore()
    print(f"\nСводка Ассистента:\n{response[:500]}...\n")

    # 2. Углубленный анализ определенного модуля - Агент самостоятельно определяет метод анализа.
    print("### 2. Модуль обработки данных анализа ###")
    print("💡 Совет: агент сам решит, как анализировать этот файл\n")
    response = maintainer.run("Пожалуйста, взгляните на файл data_processor.py, чтобы проанализировать структуру его кода.")
    print(f"\nСводка Ассистента:\n{response[:500]}...\n")

    # имитировать таймлапс
    time.sleep(1)


def day_2_analysis(maintainer):
    """День 2. Анализ качества кода (агентный метод)
    
    Агент самостоятельно решит:
    — Какие методы используются для анализа качества кода (grep TODO? Подсчитать количество строк? Проверить сложность?)
    - Вам нужно создавать заметки для записи вопросов?
    - Как систематизировать результаты анализа
    """
    print("\n" + "=" * 80)
    print("День 2. Анализ качества кода (независимый от агента анализ)")
    print("=" * 80 + "\n")

    # 1. Общий анализ качества – Агент самостоятельно определяет метод анализа.
    print("### 1. Анализ качества кода ###")
    print("💡 Совет: агент самостоятельно решит, как анализировать (например, grep TODO, wc -l, анализ сложности)\n")
    response = maintainer.analyze()
    print(f"\nСводка Ассистента:\n{response[:500]}...\n")

    # 2. Просмотр конкретных проблем. Агент самостоятельно проводит углубленный анализ.
    print("### 2. Анализ клиентского кода API ###")
    print("💡 Совет: агент сам решит, как анализировать качество этого файла.\n")
    response = maintainer.run(
        "Проанализируйте качество кода api_client.py, особенно часть обработки ошибок, и дайте предложения по улучшению."
    )
    print(f"\nСводка Ассистента:\n{response[:500]}...\n")

    # имитировать таймлапс
    time.sleep(1)


def day_3_planning(maintainer):
    """День 3. Планирование задач рефакторинга (агентный подход)
    
    Агент самостоятельно решит:
    - Какие исторические заметки рассмотреть
    - Как организовать планирование задач
    - Вам нужно создавать новые заметки?
    - Как расставить приоритеты
    """
    print("\n" + "=" * 80)
    print("День 3: Задачи планирования и реконструкции (независимое планирование агента)")
    print("=" * 80 + "\n")

    # 1. Обзор прогресса. Агент самостоятельно просматривает исторические заметки и планы.
    print("### 1. Обзор текущего прогресса и планирование следующих шагов ###")
    print("💡 Совет: Агент самостоятельно просматривает исторические записи, анализирует текущий прогресс и формулирует планы\n")
    response = maintainer.plan_next_steps()
    print(f"\nСводка Ассистента:\n{response[:500]}...\n")

    # 2. Попросите агента создать подробный план (агент решит, использовать ли NoteTool).
    print("### 2. Позвольте агенту создать подробный план реконструкции ###")
    print("💡 Совет: Агент самостоятельно решит, как составить и организовать план рефакторинга.\n")
    response = maintainer.run(
        "Пожалуйста, составьте подробный план рефакторинга на неделю на основе нашего анализа."
        "План должен включать в себя: цели, список конкретных задач, сроки и риски."
        "Используйте NoteTool, чтобы создать заметку типа Task_state для записи этого плана."
    )
    print(f"\nСводка Ассистента:\n{response[:500]}...\n")

    # имитировать таймлапс
    time.sleep(1)


def week_later_review(maintainer):
    """Через неделю: проверьте прогресс"""
    print("\n" + "=" * 80)
    print("Через неделю: проверьте прогресс")
    print("=" * 80 + "\n")

    # 1. Просмотр сводной информации о заметке
    print("### 1. Краткое изложение примечаний ###")
    summary = maintainer.note_tool.run({"action": "summary"})
    print("📊 Краткое описание заметки:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print()

    # 2. Создать полный отчет
    print("### 2. Отчет о сеансе ###")
    report = maintainer.generate_report()
    print("\n📄 Отчет о сессии:")
    print(json.dumps(report, indent=2, ensure_ascii=False))


def demonstrate_cross_session_continuity():
    """Демонстрация согласованности между сессиями"""
    print("\n" + "=" * 80)
    print("Демонстрация согласованности между сессиями")
    print("=" * 80 + "\n")

    # первая сессия
    print("### Первый сеанс (сеанс_1) ###")
    maintainer_1 = CodebaseMaintainer(
        project_name="demo_codebase",
        #Замените путь к коду при его фактическом использовании.
        codebase_path="/Users/suntao/Documents/GitHub/hello-agents/code/chapter9/codebase",
        llm=HelloAgentsLLM()
    )

    # создать несколько заметок
    maintainer_1.create_note(
        title="Проблемы с качеством кода",
        content="Найдено много комментариев TODO, которые необходимо реализовать, особенно части проверки данных и обработки ошибок.",
        note_type="blocker",
        tags=["quality", "urgent"]
    )

    stats_1 = maintainer_1.get_stats()
    print(f"Статистика сеанса 1: {stats_1['activity']}\n")

    # Сеанс моделирования завершен
    time.sleep(1)

    # Второй сеанс (новый идентификатор сеанса, но примечания сохраняются)
    print("### Второй сеанс (сеанс_2) ###")
    maintainer_2 = CodebaseMaintainer(
        project_name="demo_codebase",  # тот же проект
        #Замените путь к коду при его фактическом использовании.
        codebase_path="/Users/suntao/Documents/GitHub/hello-agents/code/chapter9/codebase",
        llm=HelloAgentsLLM()
    )

    # Получить предыдущие заметки
    response = maintainer_2.run(
        "Какие проблемы с качеством кода мы уже выявили? Что должно быть в приоритете сейчас?"
    )
    print(f"\nОтвет помощника:\n{response[:300]}...\n")

    stats_2 = maintainer_2.get_stats()
    print(f"Статистика сеанса 2: {stats_2['activity']}\n")

    # Показать сводку заметки
    summary = maintainer_2.note_tool.run({"action": "summary"})
    print("📊 Сводная информация о перекрестных сеансах:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def demonstrate_tool_synergy():
    """Продемонстрировать взаимодействие трех основных инструментов (Агентный метод).
    
    В этой демонстрации:
    - Мы больше не вызываем инструменты вручную
    - Вместо этого позвольте агенту решить, какие инструменты использовать.
    - Агент будет автоматически использовать несколько инструментов совместно в зависимости от задач.
    """
    print("\n" + "=" * 80)
    print("Демонстрация взаимодействия трех основных инструментов (автономная координация агента)")
    print("=" * 80 + "\n")

    maintainer = CodebaseMaintainer(
        project_name="synergy_demo",
        #Замените путь к коду при его фактическом использовании.
        codebase_path="/Users/suntao/Documents/GitHub/hello-agents/code/chapter9/codebase",
        llm=HelloAgentsLLM()
    )

    # Агент самостоятельно анализирует и записывает
    print("### Агент самостоятельно анализирует элементы TODO в базе кода ###")
    print("💡 Совет: Агент принимает решение самостоятельно: \n")
    print("   1. Используйте TerminalTool, чтобы найти TODO.")
    print("   2. Используйте NoteTool для записи результатов.")
    print("   3. Используйте MemoryTool, чтобы запомнить ключевую информацию\n")
    
    response = maintainer.run(
        "Пожалуйста, проанализируйте все элементы TODO в вашей кодовой базе и запишите результаты в заметках."
        "Тогда скажите мне, какие функции следует реализовать в первую очередь."
    )
    print(f"Ассистент ответил:\n{response[:500]}...\n")

    # отображать статистику
    stats = maintainer.get_stats()
    print("📊 Статистика использования инструмента:")
    print(f"  – Количество вызовов инструментов: {stats['activity']['tool_calls']}")
    print(f"  - Выполненные команды: {stats['activity']['commands_executed']}")
    print(f"  - Созданы заметки: {stats['activity']['notes_created']}")


def main():
    """основная функция"""
    print("=" * 80)
    print("Трехдневная демонстрация рабочего процесса CodebaseMaintainer (версия Agentic)")
    print("=" * 80)
    
    print("\n✨ Основные функции: автономное принятие решений агентом.")
    print("💡 Используя пример базы кода, который мы создали в главе 9.")
    print("📁 Путь к базе кода: ./codebase")
    print("📦 Включенные файлы: data_processor.py, api_client.py, utils.py, models.py.")
    print("\n🔧 Инструменты, доступные агенту:")
    print("   - TerminalTool: выполнение команд оболочки")
    print("   - NoteTool: создавайте заметки и управляйте ими.")
    print("   - MemoryTool: управление памятью.")
    print("\n⚡ Агент самостоятельно решит:")
    print("   - Какие инструменты использовать")
    print("   - Какую команду выполнить")
    print("   - Как организовать информацию\n")

    # Помощник по инициализации
    maintainer = CodebaseMaintainer(
        project_name="demo_codebase",
        #Замените путь к коду при его фактическом использовании.
        codebase_path="/Users/suntao/Documents/GitHub/hello-agents/code/chapter9/codebase",
        llm=HelloAgentsLLM()
    )

    # Выполните трехдневный рабочий процесс
    day_1_exploration(maintainer)
    day_2_analysis(maintainer)
    day_3_planning(maintainer)
    week_later_review(maintainer)

    # Дополнительная демо-версия
    print("\n\n" + "=" * 80)
    print("Дополнительная демо-версия")
    print("=" * 80)

    demonstrate_cross_session_continuity()
    demonstrate_tool_synergy()

    print("\n" + "=" * 80)
    print("Полная презентация окончена!")
    print("=" * 80)


if __name__ == "__main__":
    main()
