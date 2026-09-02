#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Умный почтовый ассистент — версия Python-скрипта
EmailSmartAssistant - Python Script Version

Упрощённая Python-версия Jupyter Notebook, которую можно запустить напрямую.
"""

import json
import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    """Главная функция"""
    console.print(Panel.fit(
        "🤖 Умный почтовый ассистент (EmailSmartAssistant)\n"
        "Версия Python-скрипта\n\n"
        "Функции:\n"
        "• Автоматическая классификация писем\n"
        "• Генерация черновиков умных ответов\n"
        "• Умные напоминания о важных событиях\n"
        "• Извлечение ключевой информации из писем\n"
        "• Архивирование и сортировка писем",
        title="Добро пожаловать",
        style="blue"
    ))
    
    # Проверка файла конфигурации
    try:
        with open('config/email_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        console.print("✅ Файл конфигурации загружен успешно", style="green")
    except FileNotFoundError:
        console.print("❌ Файл конфигурации не найден", style="red")
        console.print("Сначала настройте файл config/email_config.json", style="yellow")
        return
    
    # Проверка файла шаблонов
    try:
        with open('templates/reply_templates.json', 'r', encoding='utf-8') as f:
            templates = json.load(f)
        console.print("✅ Файл шаблонов загружен успешно", style="green")
    except FileNotFoundError:
        console.print("❌ Файл шаблонов не найден", style="red")
        return
    
    console.print("\n📋 Инструкция:", style="bold yellow")
    console.print("1. Для полного функционала используйте EmailSmartAssistant.ipynb")
    console.print("2. Этот скрипт предназначен для быстрой проверки конфигурации и зависимостей")
    console.print("3. После изменения конфигурации запустите этот скрипт для проверки")
    
    # Сводка конфигурации
    console.print(f"\n📧 Количество почтовых аккаунтов: {len(config['email_accounts'])}", style="cyan")
    console.print(f"🏷️  Правила классификации: {len(config['classification_rules'])} категорий", style="cyan")
    console.print(f"📝 Шаблоны ответов: {len(templates)} шт.", style="cyan")
    
    console.print("\n🚀 Всё готово! Используйте Jupyter Notebook для полного функционала.", style="bold green")

if __name__ == "__main__":
    main()
