"""
Инструмент написания отчётов — дневной/недельный/месячный
Интерактивный ввод, сохранение в Markdown
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Кодировка консоли UTF-8 (Windows)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def get_week_number(date=None):
    """Получить номер ISO-недели"""
    if date is None:
        date = datetime.now()
    year, week, _ = date.isocalendar()
    return f"{year}-W{week:02d}"


def get_current_date_id(report_type):
    """Получить идентификатор текущей даты"""
    now = datetime.now()
    
    if report_type == "daily":
        return now.strftime("%Y-%m-%d")
    elif report_type == "weekly":
        return get_week_number(now)
    elif report_type == "monthly":
        return now.strftime("%Y-%m")
    else:
        return now.strftime("%Y-%m-%d")


def get_report_dir(base_dir, report_type):
    """Путь к каталогу отчётов"""
    report_dir = base_dir / "archive" / "reports" / report_type
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def input_multiline(prompt="Введите содержание отчёта (пустая строка + Enter — конец):\n"):
    """Многострочный ввод до пустой строки"""
    print(prompt)
    lines = []
    empty_line_count = 0
    
    while True:
        try:
            line = input()
            if line.strip() == "":
                empty_line_count += 1
                if empty_line_count >= 1:
                    break
            else:
                empty_line_count = 0
                lines.append(line)
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n\n⚠️  Ввод отменён")
            return None
    
    return "\n".join(lines) if lines else None


def save_report(report_dir, date_id, content, report_type):
    """Сохранить отчёт в файл"""
    file_path = report_dir / f"{date_id}.md"
    
    if file_path.exists():
        response = input(f"⚠️  Файл {file_path.name} уже существует, перезаписать? (y/n): ").strip().lower()
        if response not in ['y', 'yes', 'да']:
            print("❌ Сохранение отменено")
            return False
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Отчёт сохранён: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False


def create_report(report_type, base_dir):
    """Создать отчёт"""
    print("=" * 70)
    print(f"Создание {report_type}-отчёта")
    print("=" * 70)
    
    date_id = get_current_date_id(report_type)
    print(f"Идентификатор даты: {date_id}")
    
    report_dir = get_report_dir(base_dir, report_type)
    
    existing_file = report_dir / f"{date_id}.md"
    if existing_file.exists():
        print(f"📄 Найден существующий отчёт: {existing_file.name}")
        view = input("Показать текущее содержимое? (y/n): ").strip().lower()
        if view in ['y', 'yes', 'да']:
            try:
                with open(existing_file, 'r', encoding='utf-8') as f:
                    print("\n" + "=" * 70)
                    print("Текущее содержимое:")
                    print("=" * 70)
                    print(f.read())
                    print("=" * 70)
            except Exception as e:
                print(f"⚠️  Ошибка чтения: {e}")
        
        edit = input("\nРедактировать/перезаписать? (y/n): ").strip().lower()
        if edit not in ['y', 'yes', 'да']:
            print("❌ Отменено")
            return
    
    print(f"\nВведите содержание {report_type}-отчёта...")
    print("Подсказка: пустая строка + Enter завершает ввод")
    content = input_multiline()
    
    if content is None or content.strip() == "":
        print("❌ Пустое содержимое, сохранение отменено")
        return
    
    header = f"# {report_type}-отчёт - {date_id}\n\n"
    full_content = header + content
    
    save_report(report_dir, date_id, full_content, report_type)


def list_reports(base_dir, report_type):
    """Список существующих отчётов"""
    report_dir = get_report_dir(base_dir, report_type)
    
    if not report_dir.exists():
        print(f"📁 Каталог не существует: {report_dir}")
        return
    
    reports = sorted(report_dir.glob("*.md"))
    
    if not reports:
        print(f"📁 Нет {report_type}-отчётов")
        return
    
    print(f"\n📋 Список {report_type}-отчётов ({len(reports)}):")
    print("-" * 70)
    for report in reports:
        size = report.stat().st_size
        mtime = datetime.fromtimestamp(report.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {report.name:20s}  {size:6d}  байт  {mtime}")
    print("-" * 70)


def view_report(base_dir, report_type, date_id=None):
    """Просмотр отчёта"""
    if date_id is None:
        date_id = get_current_date_id(report_type)
    
    report_dir = get_report_dir(base_dir, report_type)
    file_path = report_dir / f"{date_id}.md"
    
    if not file_path.exists():
        print(f"❌ Отчёт не найден: {file_path}")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print("\n" + "=" * 70)
        print(f"{report_type}-отчёт - {date_id}")
        print("=" * 70)
        print(content)
        print("=" * 70)
    except Exception as e:
        print(f"❌ Ошибка чтения: {e}")


def main():
    """Главная функция"""
    import sys
    
    base_dir = Path(__file__).parent
    
    if len(sys.argv) > 1 and sys.argv[1] in ['--daily', '--auto-daily']:
        create_report("daily", base_dir)
        return
    
    print("=" * 70)
    print("Инструмент написания отчётов")
    print("=" * 70)
    print("\nВыберите действие:")
    print("  1. Создать дневной отчёт")
    print("  2. Создать недельный отчёт")
    print("  3. Создать месячный отчёт")
    print("  4. Список дневных отчётов")
    print("  5. Список недельных отчётов")
    print("  6. Список месячных отчётов")
    print("  7. Просмотр отчёта")
    print("  0. Выход")
    
    while True:
        choice = input("\nВыбор (0-7): ").strip()
        
        if choice == "0":
            print("👋 До свидания!")
            break
        elif choice == "1":
            create_report("daily", base_dir)
        elif choice == "2":
            create_report("weekly", base_dir)
        elif choice == "3":
            create_report("monthly", base_dir)
        elif choice == "4":
            list_reports(base_dir, "daily")
        elif choice == "5":
            list_reports(base_dir, "weekly")
        elif choice == "6":
            list_reports(base_dir, "monthly")
        elif choice == "7":
            print("\nТип отчёта:")
            print("  1. Дневной")
            print("  2. Недельный")
            print("  3. Месячный")
            type_choice = input("Выбор (1-3): ").strip()
            if type_choice == "1":
                date_id = input("Дата (YYYY-MM-DD, Enter — сегодня): ").strip()
                view_report(base_dir, "daily", date_id if date_id else None)
            elif type_choice == "2":
                date_id = input("Неделя (YYYY-Www, Enter — текущая): ").strip()
                view_report(base_dir, "weekly", date_id if date_id else None)
            elif type_choice == "3":
                date_id = input("Месяц (YYYY-MM, Enter — текущий): ").strip()
                view_report(base_dir, "monthly", date_id if date_id else None)
        else:
            print("⚠️  Неверный выбор, попробуйте снова")


if __name__ == "__main__":
    main()
