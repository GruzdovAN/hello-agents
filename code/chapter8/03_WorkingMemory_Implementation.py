#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример кода 03: Подробное объяснение реализации WorkMemory
Продемонстрировать гибридные стратегии поиска и механизмы TTL для рабочей памяти.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from hello_agents.tools import MemoryTool
from hello_agents.memory import MemoryItem
from dotenv import load_dotenv
load_dotenv()

class WorkingMemoryDemo:
    """Демонстрационный класс рабочей памяти"""
    
    def __init__(self):
        self.memory_tool = MemoryTool(
            user_id="working_memory_demo",
            memory_types=["working"]  # Включить только рабочую память
        )
    
    def demonstrate_capacity_management(self):
        """Демонстрация управления мощностью и механизмов TTL"""
        print("🧠 Демонстрация управления объемом рабочей памяти")
        print("=" * 50)
        
        print("Характеристики рабочей памяти:")
        print("• Ограниченная емкость (по умолчанию 50 элементов).")
        print("• Механизм TTL (по умолчанию 60 минут)")
        print("• Автоматическая очистка просроченных воспоминаний.")
        print("• Управление приоритетами (упорядочение важности)")
        
        # Добавьте несколько ячеек памяти, чтобы продемонстрировать управление емкостью
        print(f"\n📝 Добавьте тестовую память...")
        for i in range(10):
            importance = 0.3 + (i * 0.07)  # растущая важность
            self.memory_tool.run({
                "action":"add",
                "content":f"Задание теста рабочей памяти {i+1} — важность {importance:.2f}",
                "memory_type":"working",
                "importance":importance,
                "test_id":i+1,
                "category":"capacity_test"
            })
        
        # Посмотреть текущий статус
        stats = self.memory_tool.run({"action":"stats"})
        print(f"Текущий статус: {stats}")
        
        # Порядок представления по важности
        print(f"\n🔍 Поиск по важности:")
        result = self.memory_tool.run({
            "action":"search", 
            "query":"тестовые задания", 
            "memory_type":"working",
            "limit":5
        })
        print(result)
    
    def demonstrate_mixed_retrieval_strategy(self):
        """Демонстрация стратегий гибридного поиска"""
        print("\n🔍Демонстрация стратегии гибридного поиска")
        print("-" * 40)
        
        print("Стратегии гибридного поиска включают в себя:")
        print("• Векторизованный семантический поиск TF-IDF")
        print("• Поиск соответствия ключевых слов")
        print("• Коэффициент временного затухания")
        print("• Регулировка веса важности")
        
        # Добавляйте различные типы воспоминаний для тестирования поиска.
        test_memories = [
            {
                "content": "Python — это язык программирования высокого уровня с кратким и понятным синтаксисом.",
                "importance": 0.8,
                "topic": "programming",
                "language": "python"
            },
            {
                "content": "Машинное обучение — важная отрасль искусственного интеллекта, включая обучение с учителем и обучение без учителя.",
                "importance": 0.9,
                "topic": "ai",
                "domain": "machine_learning"
            },
            {
                "content": "Структуры данных включают в себя базовые структуры, такие как массивы, связанные списки, стеки и очереди.",
                "importance": 0.7,
                "topic": "computer_science",
                "category": "data_structures"
            },
            {
                "content": "Анализ сложности алгоритма использует обозначение Big O для описания временной и пространственной сложности.",
                "importance": 0.8,
                "topic": "algorithms",
                "analysis": "complexity"
            }
        ]
        
        print(f"\n📝 Добавьте тестовую память...")
        for i, memory in enumerate(test_memories):
            content = memory.pop("content")
            importance = memory.pop("importance")
            self.memory_tool.run({
                "action":"add",
                "content":content,
                "memory_type":"working",
                "importance":importance,
                **memory
            })
        
        # Тестируйте разные типы поиска
        search_tests = [
            ("Программирование на Python", "Тестирование семантического соответствия"),
            ("изучать", "Проверить соответствие ключевых слов"),
            ("сложность", "Тест на частичное совпадение"),
            ("машинное обучение искусственного интеллекта", "Проверьте соответствие нескольких слов")
        ]
        
        print(f"\n🔍 Тест смешанного поиска:")
        for query, description in search_tests:
            print(f"\nЗапрос: '{query}' ({description})")
            result = self.memory_tool.run({
                "action":"search",
                "query":query,
                "memory_type":"working",
                "limit":2
            })
            print(f"Результат: {результат}")
    
    def demonstrate_time_decay_mechanism(self):
        """Продемонстрировать механизм распада во времени"""
        print("\n⏰ Демонстрация механизма распада во времени")
        print("-" * 40)
        
        print("Механизм затухания времени:")
        print("• Новым воспоминаниям придается больший вес.")
        print("• Уменьшение веса старой памяти")
        print("• Имитировать характеристики человеческой памяти")
        print("• Сбалансируйте важность старой и новой информации.")
        
        # Добавить воспоминания на разное время (симуляция)
        time_test_memories = [
            ("Последняя важная информация – только что изученные концепции", 0.7, "newest"),
            ("Новая информация – что вы узнали вчера", 0.7, "recent"), 
            ("Старая информация: что вы узнали на прошлой неделе", 0.7, "older"),
            ("Самая старая информация - контент давным-давно", 0.7, "oldest")
        ]
        
        print(f"\n📝 Добавляйте воспоминания из разных периодов...")
        for content, importance, age_category in time_test_memories:
            self.memory_tool.run({
                "action":"add",
                "content":content,
                "memory_type":"working",
                "importance":importance,
                "age_category":age_category,
                "timestamp_category":age_category
            })
        
        # Поиск эффектов затухания времени испытания
        print(f"\n🔍 Тест на эффект затухания во времени:")
        result = self.memory_tool.run({
            "action":"search",
            "query":"Чему научиться",
            "memory_type":"working",
            "limit":4
        })
        print("Результаты поиска (обратите внимание на влияние временных факторов на сортировку):")
        print(result)
    
    def demonstrate_automatic_cleanup(self):
        """Демонстрация механизма автоматической очистки."""
        print("\n🧹 Демонстрация механизма автоматической очистки")
        print("-" * 40)
        
        print("Автоматический механизм очистки:")
        print("• Автоматическая очистка просроченных воспоминаний.")
        print("• Очищайте память с низким приоритетом, когда емкость превышает предел.")
        print("• Поддержание производительности и оперативности системы.")
        print("• Имитирует ограниченный объем рабочей памяти")
        
        # Получите статус перед очисткой
        stats_before = self.memory_tool.run({"action":"stats"})
        print(f"\nСтатус перед очисткой: {stats_before}")
        
        # Добавьте несколько неважных воспоминаний
        print(f"\n📝 Добавьте память низкой важности...")
        for i in range(5):
            self.memory_tool.run({
                "action":"add",
                "content":f"Временная память низкой важности {i+1}",
                "memory_type":"working",
                "importance":0.1 + i * 0.05,
                "temporary":True,
                "cleanup_test":True
            })
        
        # Запустить очистку на основе важности
        print(f"\n🧹 Выполнить очистку на основе важности...")
        cleanup_result = self.memory_tool.run({
            "action":"forget",
            "strategy":"importance_based",
            "threshold":0.3
        })
        print(f"Результат очистки: {cleanup_result}")
        
        # Получить статус очистки
        stats_after = self.memory_tool.run({"action":"stats"})
        print(f"\nСтатус после очистки: {stats_after}")
    
    def demonstrate_performance_characteristics(self):
        """Демонстрация эксплуатационных характеристик"""
        print("\n⚡ Демонстрация эксплуатационных характеристик")
        print("-" * 40)
        
        print("Характеристики производительности рабочей памяти:")
        print("• Чистая память, чрезвычайно быстрый доступ")
        print("• Дисковый ввод-вывод не требуется, быстрое время отклика")
        print("• Подходит для часто используемых временных данных.")
        print("• Потеря данных после перезапуска системы (в соответствии с проектом)")
        
        # Тестирование производительности
        print(f"\n⏱️ Тест производительности:")
        
        # Добавляйте тесты партиями
        start_time = time.time()
        for i in range(20):
            self.memory_tool.run({
                "action":"add",
                "content":f"Память для тестирования производительности {i+1}",
                "memory_type":"working",
                "importance":0.5,
                "performance_test":True
            })
        add_time = time.time() - start_time
        print(f"Пакетное добавление 20 воспоминаний занимает: {add_time:.3f} секунд.")
        
        # Тест пакетного поиска
        start_time = time.time()
        for i in range(10):
            self.memory_tool.run({
                "action":"search",
                "query":f"Тестирование производительности",
                "memory_type":"working",
                "limit":3
            })
        search_time = time.time() - start_time
        print(f"Пакетный поиск 10 раз занимает: {search_time:.3f} секунд.")
        
        # Получить окончательную статистику
        final_stats = self.memory_tool.run("stats")
        print(f"\n📊 Итоговая статистика: {final_stats}")

def main():
    """основная функция"""
    print("🧠 Подробное объяснение реализации WorkMemory.")
    print("Продемонстрировать основные характеристики и механизмы реализации рабочей памяти.")
    print("=" * 60)
    
    try:
        demo = WorkingMemoryDemo()
        
        # 1. Демонстрация управления мощностью
        demo.demonstrate_capacity_management()
        
        # 2. Демонстрация стратегии гибридного поиска
        demo.demonstrate_mixed_retrieval_strategy()
        
        # 3. Демонстрация механизма распада во времени.
        demo.demonstrate_time_decay_mechanism()
        
        # 4. Демонстрация механизма автоматической очистки.
        demo.demonstrate_automatic_cleanup()
        
        # 5. Демонстрация ТТХ
        demo.demonstrate_performance_characteristics()
        
        print("\n" + "=" * 60)
        print("🎉 Демонстрация реализации WorkMemory завершена!")
        print("=" * 60)
        
        print("\n✨ Основные характеристики рабочей памяти:")
        print("1. 🧠 Ограниченная емкость — имитирует ограничения рабочей памяти человека.")
        print("2. ⚡ Высокоскоростной доступ - чистая память, быстрый отклик")
        print("3. 🔍Гибридный поиск – семантика + ключевые слова + время + важность")
        print("4. ⏰ Распад времени. Новая информация имеет приоритет, старая информация разрушается.")
        print("5. 🧹 Автоматическая очистка – механизм TTL + управление приоритетами.")
        
        print("\n🎯 Концепция дизайна:")
        print("• Временно — хранит временную информацию для текущего сеанса.")
        print("• Эффективность – быстрый доступ и возможности обработки.")
        print("• Интеллект – автоматически управляет и оптимизирует стратегии.")
        print("• Bionic – имитирует характеристики рабочей памяти человека.")
        
    except Exception as e:
        print(f"\n❌ Во время демонстрации произошла ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()