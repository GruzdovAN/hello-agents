#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример кода 01: основные операции MemoryTool
Покажите основной метод выполнения и основные операции MemoryTool.
"""

from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from typing import List
from hello_agents.tools import MemoryTool

def memory_tool_execute_demo():
    """Демонстрация метода выполнения MemoryTool"""
    print("🧠 Демонстрация основных операций MemoryTool")
    print("=" * 50)
    
    # Инициализация MemoryTool
    memory_tool = MemoryTool(
        user_id="demo_user",
        memory_types=["working", "episodic", "semantic", "perceptual"]
    )
    
    print("✅ Инициализация MemoryTool завершена")
    print(f"📋 Поддерживаемые операции: добавление, поиск, сводка, статистика, обновление, удаление, забвение, объединение, очистка_всех.")
    
    return memory_tool

def add_memory_demo(memory_tool):
    """Добавлена ​​демонстрация памяти — имитирует процесс кодирования человеческой памяти."""
    print("\n📝 Добавить демо-версию памяти")
    print("-" * 30)

    # Добавьте рабочую память
    result = memory_tool.run({
        "action":"add",
        "content":"Изучение системы памяти платформы HelloAgents.",
        "memory_type":"working",
        "importance":0.7,
        "task_type":"learning"
    })
    print(f"рабочая память: {result}")
    
    # Добавьте эпизодическую память
    result = memory_tool.run({
        "action":"add",
        "content":"Начните углубленное исследование технологии AI Agent в 2024 году.",
        "memory_type":"episodic",
        "importance":0.8,
        "event_type":"milestone",
        "location":"центр исследований и разработок"
    })
    print(f"Эпизодическая память: {результат}")
    
    # Добавить семантическую память
    result = memory_tool.run({
        "action":"add",
        "content":"Система памяти включает четыре типа: рабочую память, эпизодическую память, смысловую память и перцептивную память.",
        "memory_type":"semantic",
        "importance":0.9,
        "concept":"memory_types",
        "domain":"cognitive_science"
    })
    print(f"Семантическая память: {результат}")
    
    # добавить перцептивную память
    result = memory_tool.run({
        "action":"add",
        "content":"Просмотрели схему архитектуры и код реализации системы памяти.",
        "memory_type":"perceptual",
        "importance":0.6,
        "modality":"document",
        "source":"technical_documentation"
    })
    print(f"Перцептивная память: {result}")

def search_memory_demo(memory_tool):
    """Демонстрация поисковой памяти — извлечение для семантического понимания"""
    print("\n🔍 Демо-версия поиска в памяти")
    print("-" * 30)
    
    # Базовый поиск
    print("Базовый поиск – «система памяти»:")
    result = memory_tool.run({"action":"search", "query":"система памяти", "limit":3})
    print(result)
    
    # Поиск по типу
    print("\nПоиск по типу — «память» в семантической памяти:")
    result = memory_tool.run({
        "action":"search", 
        "query":"память", 
        "memory_type":"semantic", 
        "limit":2
    })
    print(result)
    
    # Установить порог важности
    print("\nПоиск в памяти высокой важности:")
    result = memory_tool.run({
        "action":"search", 
        "query":"AI Agent", 
        "min_importance":0.7, 
        "limit":3
    })
    print(result)

def memory_summary_demo(memory_tool):
    """Демо-версия сводки памяти — дает полное представление о системе."""
    print("\n📋 Демонстрация сводки памяти")
    print("-" * 30)
    
    # Получить сводку памяти
    result = memory_tool.run({"action":"summary", "limit":5})
    print("Краткое описание памяти:")
    print(result)
    
    # Получить статистику
    print("\n📊 Статистика:")
    result = memory_tool.run({"action": "stats"})
    print(result)

def memory_management_demo(memory_tool):
    """Демонстрация управления памятью — забывание и консолидация"""
    print("\n⚙️ Демонстрация управления памятью")
    print("-" * 30)
    
    # Добавьте память низкой важности для забывания тестов
    memory_tool.run({
        "action":"add",
        "content":"Это временная тестовая память очень низкой важности.",
        "memory_type":"working",
        "importance":0.1
    })
    
    # Забывание по важности
    print("Забывание на основе важности (порог = 0,2):")
    result = memory_tool.run({
        "action":"forget",
        "strategy":"importance_based",
        "threshold":0.2
    })
    print(result)
    
    # Консолидация памяти – преобразование важной рабочей памяти в эпизодическую.
    print("\nИнтеграция памяти (рабочая → эпизодическая):")
    result = memory_tool.run({
        "action":"consolidate",
        "from_type":"working",
        "to_type":"episodic",
        "importance_threshold":0.6
    })
    print(result)

def main():
    """основная функция"""
    print("🚀 Полная демонстрация основных операций MemoryTool.")
    print("Продемонстрировать основные функции и методы работы системы памяти.")
    print("=" * 60)
    
    try:
        # 1. Инициализируйте MemoryTool
        memory_tool = memory_tool_execute_demo()
        
        # 2. Добавьте демонстрацию памяти
        add_memory_demo(memory_tool)
        
        # 3. Демонстрация поиска в памяти
        search_memory_demo(memory_tool)
        
        # 4. Демонстрация сводки памяти
        memory_summary_demo(memory_tool)
        
        # 5. Демонстрация управления памятью
        memory_management_demo(memory_tool)
        
        print("\n" + "=" * 60)
        print("🎉 Демонстрация основных операций MemoryTool завершена!")
        print("=" * 60)
        
        print("\n✨ Продемонстрированные основные функции:")
        print("1. 🧠 Добавление и управление четырьмя типами памяти")
        print("2. 🔍 Интеллектуальный семантический поиск и фильтрация")
        print("3. Сводка 📋 памяти и статистический анализ")
        print("4. ⚙️ Консолидация памяти и избирательное забывание.")
        
        print("\n🎯 Особенности конструкции:")
        print("• Единый интерфейс выполнения, простая и последовательная работа.")
        print("• Богатая поддержка метаданных для упрощения классификации и поиска.")
        print("• Интеллектуальная оценка важности и механизм затухания времени")
        print("• Стратегии управления памятью, имитирующие человеческое познание.")
        
    except Exception as e:
        print(f"\n❌ Во время демонстрации произошла ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()