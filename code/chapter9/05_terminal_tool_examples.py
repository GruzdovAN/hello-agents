"""
Пример использования TerminalTool

Демонстрирует типичные шаблоны использования TerminalTool:
1. Исследовательская навигация
2. Анализ файла данных
3. Анализ файла журнала
4. Анализ кодовой базы
"""

import os
from pathlib import Path
from hello_agents.tools import TerminalTool

# Получить каталог, в котором находится скрипт
SCRIPT_DIR = Path(__file__).parent.absolute()


def demo_exploratory_navigation():
    """Демонстрация исследовательской навигации"""
    print("\n" + "=" * 80)
    print("Сценарий 1: Разведывательная навигация")
    print("=" * 80 + "\n")

    terminal = TerminalTool(workspace=str(SCRIPT_DIR))

    # Шаг 1. Просмотр текущего каталога
    print("1. Просмотрите текущий каталог:")
    result = terminal.run({"command": "ls -la"})
    print(result)

    # Шаг 2. Просмотр файлов Python
    print("\n2. Просмотр файлов Python:")
    result = terminal.run({"command": "ls -la *.py"})
    print(result)

    # Шаг 3. Найдите определенные файлы
    print("\n3. Найдите файлы с определенным шаблоном:")
    result = terminal.run({"command": "find . -name '*codebase_maintainer.py'"})
    print(result)

    # Шаг 4. Просмотр содержимого файла
    print("\n4. Посмотреть содержимое файла:")
    result = terminal.run({"command": "head -n 20 codebase_maintainer.py"})
    print(result)


def demo_data_file_analysis():
    """Анализ файла демонстрационных данных"""
    print("\n" + "=" * 80)
    print("Сценарий 2: Анализ файла данных")
    print("=" * 80 + "\n")

    terminal = TerminalTool(workspace=str(SCRIPT_DIR / "data"))

    # Просмотрите первые несколько строк файла CSV.
    print("1. Просмотрите первые 5 строк CSV-файла:")
    result = terminal.run({"command": "head -n 5 sales_2024.csv"})
    print(result)

    # Подсчитайте общее количество строк
    print("\n2. Подсчитайте количество строк файла:")
    result = terminal.run({"command": "wc -l *.csv"})
    print(result)

    # Извлечение и подсчет категорий продуктов
    print("\n3. Статистика распределения категорий товаров:")
    result = terminal.run({"command": "tail -n +2 sales_2024.csv | cut -d',' -f3 | sort | uniq -c"})
    print(result)


def demo_log_analysis():
    """Анализ файла демо-журнала"""
    print("\n" + "=" * 80)
    print("Сценарий 3: Анализ файла журнала")
    print("=" * 80 + "\n")

    terminal = TerminalTool(workspace=str(SCRIPT_DIR / "logs"))

    # Просмотрите последний журнал ошибок
    print("1. Просмотрите последний журнал ошибок:")
    result = terminal.run({"command": "tail -n 50 app.log | grep ERROR"})
    print(result)

    # Распределение типов статистических ошибок
    print("\n2. Статистическое распределение типов ошибок:")
    result = terminal.run({"command": "grep ERROR app.log | awk '{print $4}' | sort | uniq -c | sort -rn"})
    print(result)

    # Найти журналы за определенный период времени
    print("\n3. Найти журналы за определенный период времени:")
    result = terminal.run({"command": "grep '2024-01-19 15:' app.log | tail -n 20"})
    print(result)


def demo_codebase_analysis():
    """Анализ базы демо-кода"""
    print("\n" + "=" * 80)
    print("Сценарий 4: Анализ базы кода")
    print("=" * 80 + "\n")

    terminal = TerminalTool(workspace=str(SCRIPT_DIR / "codebase"))

    # Подсчитайте строки кода
    print("1. Подсчитайте количество строк кода:")
    result = terminal.run({"command": "find . -name '*.py' -exec wc -l {} + | tail -n 1"})
    print(result)

    # Найти все комментарии TODO
    print("\n2. Найдите все комментарии TODO:")
    result = terminal.run({"command": "grep -rn 'TODO' --include='*.py'"})
    print(result)

    # Найдите определение конкретной функции
    print("\n3. Найдите определение конкретной функции:")
    result = terminal.run({"command": "grep -rn 'def process_data' --include='*.py'"})
    print(result)


def demo_security_features():
    """Демонстрация функций безопасности"""
    print("\n" + "=" * 80)
    print("Демонстрация функций безопасности")
    print("=" * 80 + "\n")

    terminal = TerminalTool(workspace=str(SCRIPT_DIR / "project"))

    # Была предпринята попытка выполнить команду, которая не разрешена.
    print("1. Попытка выполнить опасную команду (rm):")
    result = terminal.run({"command": "rm -rf /"})
    print(result)

    # Попробуйте получить доступ к файлу за пределами рабочего каталога.
    print("\n2. Попробуйте получить доступ к файлам за пределами рабочего каталога:")
    result = terminal.run({"command": "cat /etc/passwd"})
    print(result)

    # Попробуйте выйти из рабочего каталога
    print("\n3. Попробуйте выйти из рабочего каталога через ..:")
    result = terminal.run({"command": "cd ../../../etc"})
    print(result)


def main():
    print("=" * 80)
    print("Пример использования TerminalTool")
    print("=" * 80)

    # Демонстрация различных сценариев использования
    demo_exploratory_navigation()
    demo_data_file_analysis()
    demo_log_analysis()
    demo_codebase_analysis()
    demo_security_features()

    print("\n" + "=" * 80)
    print("Демонстрация завершена!")
    print("=" * 80)


if __name__ == "__main__":
    main()
