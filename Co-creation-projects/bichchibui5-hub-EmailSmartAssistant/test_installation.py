#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт проверки установки
Installation Test Script

Для проверки корректности установки всех зависимостей
"""

import sys
from rich.console import Console
from rich.table import Table

console = Console()

def test_imports():
    """Проверка импорта всех необходимых библиотек"""
    test_results = []
    
    # Проверка основных библиотек
    libraries = [
        ('imaplib', 'Протокол IMAP для почты'),
        ('smtplib', 'Протокол SMTP для почты'), 
        ('email', 'Обработка почты'),
        ('json', 'Обработка JSON'),
        ('pandas', 'Обработка данных'),
        ('numpy', 'Численные вычисления'),
        ('jieba', 'Сегментация текста'),
        ('textblob', 'Обработка текста'),
        ('langdetect', 'Определение языка'),
        ('sklearn', 'Машинное обучение'),
        ('dateparser', 'Разбор дат'),
        ('arrow', 'Работа со временем'),
        ('jinja2', 'Движок шаблонов'),
        ('matplotlib', 'Построение графиков'),
        ('seaborn', 'Статистические графики'),
        ('tqdm', 'Индикатор прогресса'),
        ('rich', 'Оформление терминала')
    ]
    
    for lib_name, description in libraries:
        try:
            __import__(lib_name)
            test_results.append((lib_name, description, "✅ Успех", "green"))
        except ImportError as e:
            test_results.append((lib_name, description, f"❌ Ошибка: {str(e)}", "red"))
    
    return test_results

def test_files():
    """Проверка наличия необходимых файлов"""
    import os
    
    files_to_check = [
        ('config/email_config.json', 'Файл конфигурации почты'),
        ('templates/reply_templates.json', 'Файл шаблонов ответов'),
        ('EmailSmartAssistant.ipynb', 'Основной Notebook'),
        ('requirements.txt', 'Список зависимостей'),
        ('README.md', 'Документация')
    ]
    
    file_results = []
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            file_results.append((file_path, description, "✅ Есть", "green"))
        else:
            file_results.append((file_path, description, "❌ Отсутствует", "red"))
    
    return file_results

def main():
    """Главная функция тестирования"""
    console.print("🧪 Умный почтовый ассистент — проверка установки", style="bold blue")
    console.print("=" * 50)
    
    # Проверка версии Python
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    console.print(f"Версия Python: {python_version}", style="cyan")
    
    if sys.version_info < (3, 7):
        console.print("⚠️  Рекомендуется Python 3.7 или выше", style="yellow")
    
    console.print()
    
    # Проверка импорта библиотек
    console.print("📚 Проверка импорта библиотек...", style="bold")
    import_results = test_imports()
    
    table = Table(title="Результаты проверки импорта библиотек")
    table.add_column("Библиотека", style="cyan")
    table.add_column("Описание", style="white")
    table.add_column("Статус", style="white")
    
    success_count = 0
    for lib_name, description, status, color in import_results:
        table.add_row(lib_name, description, status)
        if "Успех" in status:
            success_count += 1
    
    console.print(table)
    console.print(f"Успешно импортировано: {success_count}/{len(import_results)}", style="green" if success_count == len(import_results) else "yellow")
    
    console.print()
    
    # Проверка наличия файлов
    console.print("📁 Проверка целостности файлов...", style="bold")
    file_results = test_files()
    
    file_table = Table(title="Проверка целостности файлов")
    file_table.add_column("Путь к файлу", style="cyan")
    file_table.add_column("Описание", style="white") 
    file_table.add_column("Статус", style="white")
    
    file_success = 0
    for file_path, description, status, color in file_results:
        file_table.add_row(file_path, description, status)
        if "Есть" in status:
            file_success += 1
    
    console.print(file_table)
    console.print(f"Файлы на месте: {file_success}/{len(file_results)}", style="green" if file_success == len(file_results) else "yellow")
    
    console.print()
    
    # Итог
    if success_count == len(import_results) and file_success == len(file_results):
        console.print("🎉 Все проверки пройдены! Можно начинать работу с умным почтовым ассистентом.", style="bold green")
        console.print("💡 Следующий шаг: запустите 'jupyter notebook EmailSmartAssistant.ipynb'", style="blue")
    else:
        console.print("⚠️  Обнаружены проблемы, проверьте пункты с ошибками выше.", style="bold yellow")
        if success_count < len(import_results):
            console.print("📦 Установите недостающие библиотеки: pip install -r requirements.txt", style="cyan")

if __name__ == "__main__":
    main()
