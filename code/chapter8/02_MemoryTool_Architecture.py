#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример кода 02: Проектирование архитектуры MemoryTool
Демонстрация многоуровневой архитектуры MemoryTool и MemoryManager.
"""

from dotenv import load_dotenv
load_dotenv()
from typing import List, Optional, Dict, Any
from datetime import datetime
from hello_agents.tools import MemoryTool
from hello_agents.memory import MemoryConfig

class MemoryToolArchitectureDemo:
    """Демонстрационный класс архитектуры MemoryTool"""
    
    def __init__(self):
        self.memory_config = MemoryConfig()
        self.memory_types = ["working", "episodic", "semantic", "perceptual"]
    
    def demonstrate_memory_tool_init(self):
        """Демонстрация процесса инициализации MemoryTool"""
        print("🏗️ Демонстрация дизайна архитектуры MemoryTool")
        print("=" * 50)
        
        print("📋Процесс инициализации MemoryTool:")
        print("1. Создайте объект конфигурации MemoryConfig.")
        print("2. Укажите тип памяти, который нужно включить.")
        print("3. Инициализируйте менеджер MemoryManager.")
        print("4. Включите различные модули памяти в соответствии с конфигурацией.")
        
        # Демонстрация инициализации MemoryTool
        memory_tool = MemoryTool(
            user_id="architecture_demo_user",
            memory_config=self.memory_config,
            memory_types=self.memory_types
        )
        
        print(f"\n ✅ Инициализация MemoryTool завершена")
        print(f"👤 Идентификатор пользователя: {memory_tool.memory_manager.user_id}")
        print(f"🧠 Включенные типы памяти: {memory_tool.memory_types}")
        print(f"⚙️ Объект конфигурации: {type(memory_tool.memory_config).__name__}")
        
        return memory_tool
    
    def demonstrate_memory_manager_architecture(self, memory_tool):
        """Демонстрация архитектуры режима композиции MemoryManager."""
        print("\n🔧 Проект архитектуры MemoryManager")
        print("-" * 40)
        
        print("MemoryManager разработан в комбинированном режиме:")
        print("- Единый интерфейс работы с памятью")
        print("- Независимые компоненты типа памяти")
        print("- Гибкая настройка и возможности расширения.")
        
        # Получить экземпляр MemoryManager
        memory_manager = memory_tool.memory_manager
        
        print(f"\n📊 Статус MemoryManager:")
        print(f"Идентификатор пользователя: {memory_manager.user_id}")
        print(f"Тип конфигурации: {type(memory_manager.config).__name__}")
        print(f"Количество типов памяти: {len(memory_manager.memory_types)}")
        
        # Отображение состояния каждого типа памяти
        print(f"\n🧠 Компонент типа памяти:")
        for memory_type, memory_instance in memory_manager.memory_types.items():
            print(f"  • {memory_type}: {type(memory_instance).__name__}")
    
    def demonstrate_memory_types_specialization(self, memory_tool):
        """Продемонстрировать особенности специализации четырех типов памяти."""
        print("\n🎯 Профессиональный дизайн четырех типов памяти")
        print("-" * 40)
        
        memory_types_info = {
            "working": {
                "name": "рабочая память",
                "features": ["Ограниченная емкость", "Быстрый доступ", "Автоматическая очистка", "временное хранилище"],
                "storage": "Чистое хранилище памяти",
                "ttl": "Механизм TTL 60 минут."
            },
            "episodic": {
                "name": "эпизодическая память", 
                "features": ["последовательность событий", "временной ряд", "Контекстно-богатый", "ассоциация сеанса"],
                "storage": "Гибридное хранилище SQLite + Qdrant",
                "ttl": "Постоянное хранилище"
            },
            "semantic": {
                "name": "семантическая память",
                "features": ["концептуальные знания", "отношения сущностей", "График знаний", "семантическое рассуждение"],
                "storage": "Гибридное хранилище Neo4j + Qdrant", 
                "ttl": "долгосрочное хранение"
            },
            "perceptual": {
                "name": "перцептивная память",
                "features": ["мультимодальный", "Кросс-модальный поиск", "Сенсорные данные", "генерация контента"],
                "storage": "Модальное векторное хранилище",
                "ttl": "Управляйте по важности"
            }
        }
        
        for memory_type, info in memory_types_info.items():
            print(f"\n📚 {info['name']} ({memory_type}):")
            print(f"   Возможности: {', '.join(info['features'])}")
            print(f"   Хранилище: {info['storage']}")
            print(f"   Жизненный цикл: {info['ttl']}")
            
            # Добавьте образец памяти для демонстрации функций
            if memory_type == "working":
                memory_tool.run({
                    "action":"add",
                    "content":f"Демонстрирует функцию временного хранения {info['name']}.",
                    "memory_type":memory_type,
                    "importance":0.6,
                    "demo_feature":"temporary_storage"
                })
            elif memory_type == "episodic":
                memory_tool.run({
                    "action":"add",
                    "content":f"Демонстрирует функцию регистрации событий {info['name']}.",
                    "memory_type":memory_type,
                    "importance":0.7,
                    "event_type":"demonstration",
                    "session_context":"architecture_demo"
                })
            elif memory_type == "semantic":
                memory_tool.run({
                    "action":"add",
                    "content":f"{info['name']} используется для хранения концептуальных знаний и отношений сущностей.",
                    "memory_type":memory_type,
                    "importance":0.8,
                    "concept":"memory_architecture",
                    "domain":"cognitive_computing"
                })
            elif memory_type == "perceptual":
                memory_tool.run({
                    "action":"add",
                    "content":f"Продемонстрировать мультимодальную обработку данных {info['name']}",
                    "memory_type":memory_type,
                    "importance":0.6,
                    "modality":"text",
                    "data_type":"demonstration"
                })
    
    def demonstrate_unified_interface(self, memory_tool):
        """Демонстрация преимуществ дизайна унифицированных интерфейсов."""
        print("\n🔗 Преимущества единого дизайна интерфейса")
        print("-" * 40)
        
        print("Унифицированный метод выполнения обеспечивает:")
        print("• Последовательный метод вызова")
        print("• Гибкая передача параметров")
        print("• Единая обработка ошибок")
        print("• Упрощенный пользовательский интерфейс.")
        
        # Демонстрация использования единого интерфейса
        operations = [
            ("search", {"query": "Демо", "limit": 2}),
            ("summary", {"limit": 3}),
            ("stats", {}),
        ]
        
        print(f"\n🔧 Демонстрация работы единого интерфейса:")
        for operation, params in operations:
            print(f"\nОперация: {операция}")
            print(f"Параметры: {параметры}")
            result = memory_tool.run({"action":operation, **params})
            print(f"Результат: {result[:100]}..." if len(str(result)) > 100 else f"Результат: {результат}")
    
    def demonstrate_extensibility(self):
        """Проектирование масштабируемости демонстрационной системы"""
        print("\n🚀 Проектирование масштабируемости системы")
        print("-" * 40)
        
        print("Возможности масштабируемости:")
        print("• Тип подключаемой памяти")
        print("• Настраиваемое серверное хранилище.") 
        print("• Гибкие стратегии памяти")
        print("• Модульная конструкция компонентов")
        
        # Демонстрационная пользовательская конфигурация
        custom_config = MemoryConfig()
        custom_config.working_memory_capacity = 100
        custom_config.working_memory_ttl_minutes = 120
        
        print(f"\n⚙️ Пример пользовательской конфигурации:")
        print(f"Объем рабочей памяти: {custom_config.working_memory_capacity}")
        print(f"Срок жизни рабочей памяти: {custom_config.working_memory_ttl_минуты} минут.")
        
        # Демонстрирует выборочное включение типов памяти.
        selective_memory_tool = MemoryTool(
            user_id="selective_user",
            memory_config=custom_config,
            memory_types=["working", "semantic"]  # Включить только некоторые типы
        )
        
        print(f"\n🎯 Пример выборочной активации:")
        print(f"Включенные типы памяти: {selective_memory_tool.memory_types}")
        print("✅ Система поддерживает гибкую настройку в соответствии с потребностями")

def main():
    """основная функция"""
    print("🏗️ Полная демонстрация проектирования архитектуры MemoryTool.")
    print("Демонстрация многоуровневой архитектуры и шаблонов проектирования систем памяти.")
    print("=" * 60)
    
    try:
        demo = MemoryToolArchitectureDemo()
        
        # 1. Демонстрация инициализации MemoryTool
        memory_tool = demo.demonstrate_memory_tool_init()
        
        # 2. Демонстрация архитектуры MemoryManager
        demo.demonstrate_memory_manager_architecture(memory_tool)
        
        # 3. Профессиональная демонстрация типов памяти.
        demo.demonstrate_memory_types_specialization(memory_tool)
        
        # 4. Демонстрация единого интерфейса
        demo.demonstrate_unified_interface(memory_tool)
        
        # 5. Демонстрация масштабируемости
        demo.demonstrate_extensibility()
        
        print("\n" + "=" * 60)
        print("🎉 Демонстрация архитектуры MemoryTool завершена!")
        print("=" * 60)
        
        print("\n✨ Основные моменты архитектурного проектирования:")
        print("1. 🏗️ Многоуровневая архитектура – ​​разделение задач и четкие обязанности.")
        print("2. 🔧 Режим комбинирования – гибкое комбинирование, независимое управление.")
        print("3. 🎯 Профессиональный дизайн – каждый тип памяти имеет отличительные характеристики.")
        print("4. 🔗 Единый интерфейс — упрощенное использование, единообразный опыт")
        print("5. 🚀 Высокая масштабируемость – подключаемый модуль, гибкая настройка.")
        
        print("\n🎯 Принципы дизайна:")
        print("• Принцип единой ответственности – каждый компонент ориентирован на определенную функцию.")
        print("• Принцип открытости-закрытости – открыт для расширения, закрыт для модификации.")
        print("• Принцип инверсии зависимостей. Зависите от абстракции, а не от конкретного.")
        print("• Композиция лучше, чем наследование: гибкая композиция, избегайте сложного наследования.")
        
    except Exception as e:
        print(f"\n❌ Во время демонстрации произошла ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()