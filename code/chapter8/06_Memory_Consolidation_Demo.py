#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример кода 06: Демонстрация механизма консолидации памяти
Продемонстрировать интеллектуальный процесс преобразования кратковременной памяти в долговременную.
"""

from dotenv import load_dotenv
load_dotenv()
import time
from datetime import datetime, timedelta
from hello_agents.tools import MemoryTool


class MemoryConsolidationDemo:
    """Демонстрационный класс интеграции памяти"""
    
    def __init__(self):
        self.memory_tool = MemoryTool(
            user_id="consolidation_demo_user",
            memory_types=["working", "episodic", "semantic", "perceptual"]
        )
    
    def setup_initial_memories(self):
        """Установить начальные данные памяти"""
        print("📝 Установите начальные данные памяти")
        print("=" * 50)
        
        # Добавьте рабочую память разной важности
        working_memories = [
            {
                "content": "Изучили основные принципы архитектуры Transformer.",
                "importance": 0.9,
                "topic": "deep_learning",
                "session": "study_session_1"
            },
            {
                "content": "Завершена задача по отладке кода Python.",
                "importance": 0.8,
                "topic": "programming",
                "task_type": "debugging"
            },
            {
                "content": "Участие в собраниях команды для обсуждения хода проекта.",
                "importance": 0.7,
                "topic": "teamwork",
                "meeting_type": "progress_review"
            },
            {
                "content": "Проверил прогноз погоды на сегодня",
                "importance": 0.3,
                "topic": "daily_life",
                "category": "routine"
            },
            {
                "content": "Прочтите статью о механизме внимания.",
                "importance": 0.85,
                "topic": "research",
                "paper_type": "technical"
            },
            {
                "content": "выпил чашку кофе",
                "importance": 0.2,
                "topic": "daily_life",
                "category": "routine"
            },
            {
                "content": "Решил сложную алгоритмическую задачу",
                "importance": 0.9,
                "topic": "problem_solving",
                "difficulty": "high"
            },
            {
                "content": "Организованные файлы рабочего стола",
                "importance": 0.4,
                "topic": "organization",
                "category": "maintenance"
            }
        ]
        
        print("Добавляем рабочую память:")
        for i, memory in enumerate(working_memories):
            content = memory.pop("content")
            importance = memory.pop("importance")
            
            result = self.memory_tool.run({"action":"add",
                                            "content":content,
                                            "memory_type":"working",
                                            "importance":importance,
                                            **memory})
            
            print(f"  {я+1}. {content[:40]}... (важность: {важность})")
        
        print(f"\n✅ {len(working_memories)} добавлены рабочие воспоминания.")
        
        # Показать текущий статус
        stats = self.memory_tool.run({"action":"stats"})
        print(f"\n📊 Текущая статистика памяти:\n{stats}")
    
    def demonstrate_consolidation_criteria(self):
        """Продемонстрировать интегрированные критерии и процесс проверки"""
        print("\n🎯 Демонстрация стандарта интеграции памяти")
        print("-" * 50)
        
        print("Стандарты интеграции:")
        print("• Фильтрация порогов важности.")
        print("• Сортировать по важности.")
        print("• Обработка преобразования типов")
        print("• Обновления метаданных")
        
        # Получить сводную информацию о текущей рабочей памяти
        print("\n📋 Состояние рабочей памяти перед интеграцией:")
        summary = self.memory_tool.run({"action":"summary", "limit":10})
        print(summary)
        
        # Проверьте эффект интеграции различных порогов
        thresholds = [0.5, 0.7, 0.8]
        
        for threshold in thresholds:
            print(f"\n🔍 Порог важности теста {threshold}:")
            
            # Смоделировать процесс интеграции (не фактическое выполнение, просто анализ)
            working_memories = []
            # Это должно быть взято из реальной рабочей памяти, чтобы упростить демонстрацию.
            
            print(f"  Воспоминания, подходящие для консолидации на пороге {threshold}:")
            print(f"  • Воспоминания с важностью >= {порог} будут интегрированы.")
            print(f"  • Интегрированный тип: рабочий → эпизодический.")
            print(f"  • Повышенная важность: важность × 1,1.")
    
    def demonstrate_consolidation_process(self):
        """Продемонстрировать реальный процесс интеграции"""
        print("\n🔄 Демонстрация процесса интеграции памяти")
        print("-" * 50)
        
        print("Этапы процесса интеграции:")
        print("1. Отфильтруйте воспоминания, соответствующие критериям.")
        print("2. Сортировка по важности")
        print("3. Создайте новые воспоминания")
        print("4. Типы обновлений и метаданные")
        print("5. Добавьте интеграционную разметку")
        
        # Выполните интеграцию различных порогов
        consolidation_tests = [
            (0.6, "Интеграция с низким порогом - интегрируйте больше памяти"),
            (0.8, "Высокий порог интеграции – интегрируются только самые важные воспоминания.")
        ]
        
        for threshold, description in consolidation_tests:
            print(f"\n🔄 {description} (порог: {порог}):")
            
            # Получить статус предварительной интеграции
            stats_before = self.memory_tool.run({"action":"stats"})
            print(f"Статус до интеграции: {stats_before}")
            
            # Выполнить интеграцию
            start_time = time.time()
            consolidation_result = self.memory_tool.run({"action":"consolidate",
                                                          "from_type":"working",
                                                          "to_type":"episodic",
                                                          "importance_threshold":threshold})
            consolidation_time = time.time() - start_time
            
            print(f"Результат консолидации: {consolidation_result}")
            print(f"Время консолидации: {consolidation_time:.3f} секунд.")
            
            # Получить интегрированный статус
            stats_after = self.memory_tool.run({"action":"stats"})
            print(f"Статус после интеграции: {stats_after}")
            
            # Просмотр интегрированной эпизодической памяти
            print(f"\n📚 Интегрированная эпизодическая память:")
            episodic_search = self.memory_tool.run({"action":"search",
                                                     "query":"",
                                                     "memory_type":"episodic",
                                                     "limit":5})
            print(episodic_search)
    
    def demonstrate_consolidation_metadata(self):
        """Демонстрация обработки метаданных во время интеграции"""
        print("\n📋 Демонстрация интегрированной обработки метаданных")
        print("-" * 50)
        
        print("Обработка метаданных:")
        print("• Сохранять исходные метаданные.")
        print("• Добавить интеграционную разметку.")
        print("• Рекордное время интеграции")
        print("• Сохранить исходный идентификационный номер.")
        
        # Добавьте специальную рабочую память для презентаций
        special_memory_result = self.memory_tool.run({"action":"add",
            "content":"Это специальная память, используемая для демонстрации интегрированной обработки метаданных.",
            "memory_type":"working",
            "importance":0.85,
            "special_tag":"metadata_demo",
            "original_context":"demonstration",
            "creation_purpose":"show_consolidation_metadata"
        })
        
        print(f"Добавить специальную память: {special_memory_result}")
        
        # Выполнить интеграцию
        print(f"\n🔄 Выполнить интеграцию...")
        consolidation_result = self.memory_tool.run({"action":"consolidate",
                                                       "from_type":"working",
                                                       "to_type":"episodic",
                                                       "importance_threshold":0.8})
        
        print(f"Результат консолидации: {consolidation_result}")
        
        # Поиск в объединенных воспоминаниях Просмотр метаданных
        print(f"\n🔍 Просмотр метаданных интегрированной памяти:")
        search_result = self.memory_tool.run({"action":"search",
                                                "query":"особая память",
                                                "memory_type":"episodic",
                                                "limit":1})
        print(search_result)
    
    def demonstrate_multi_type_consolidation(self):
        """Демонстрация интеграции памяти нескольких типов"""
        print("\n🔀 Демонстрация интеграции памяти нескольких типов")
        print("-" * 50)
        
        print("Несколько типов сценариев интеграции:")
        print("• работа → эпизодическая (учет стажа)")
        print("• рабочий → семантический (извлечение знаний)")
        print("• эпизодический → смысловой (обобщение опыта)")
        
        # Добавьте немного воспоминаний для разных путей интеграции
        consolidation_candidates = [
            {
                "content": "Изучил принцип алгоритма обратного распространения ошибки в глубоком обучении.",
                "memory_type": "working",
                "importance": 0.9,
                "learning_type": "concept",
                "suitable_for": "semantic"
            },
            {
                "content": "Сегодня днем ​​я посетил сессию по обмену технологиями искусственного интеллекта.",
                "memory_type": "working", 
                "importance": 0.8,
                "event_type": "meeting",
                "suitable_for": "episodic"
            },
            {
                "content": "Овладел навыками внедрения Transformer с помощью множества практик.",
                "memory_type": "episodic",
                "importance": 0.85,
                "experience_type": "skill",
                "suitable_for": "semantic"
            }
        ]
        
        print(f"\n📝 Добавьте память кандидата на интеграцию:")
        for memory in consolidation_candidates:
            content = memory.pop("content")
            memory_type = memory.pop("memory_type")
            importance = memory.pop("importance")
            suitable_for = memory.pop("suitable_for")
            
            result = self.memory_tool.run({"action":"add",
                                            "content":content,
                                            "memory_type":memory_type,
                                            "importance":importance,
                                            **memory})
            
            print(f"  • {content[:50]}... → подходит для интеграции как {suitable_for}")
        
        # Выполнять различные типы интеграций
        consolidation_paths = [
            ("working", "episodic", 0.75, "Опыт интеграции записей"),
            ("working", "semantic", 0.85, "Извлечение и интеграция знаний"),
            ("episodic", "semantic", 0.8, "Обобщение опыта и интеграция")
        ]
        
        for from_type, to_type, threshold, description in consolidation_paths:
            print(f"\n🔄 {description} ({from_type} → {to_type}):")
            
            result = self.memory_tool.run({"action":"consolidate",
                                            "from_type":from_type,
                                            "to_type":to_type,
                                            "importance_threshold":threshold})
            
            print(f"Интегрированные результаты: {result}")
    
    def demonstrate_consolidation_benefits(self):
        """Демонстрация преимуществ консолидации памяти"""
        print("\n✨ Демонстрация преимуществ консолидации памяти")
        print("-" * 50)
        
        print("Преимущества интеграции:")
        print("• Долгосрочное сохранение важной информации.")
        print("• Освободите рабочую память.")
        print("• Сформировать систему знаний")
        print("• Повышение эффективности поиска.")
        
        # Получить окончательное состояние системы памяти
        print(f"\n📊 Окончательное состояние системы памяти:")
        final_stats = self.memory_tool.run({"action":"stats"})
        print(final_stats)
        
        # Получите сводную информацию о каждом типе памяти
        print(f"\n📋 Краткое описание различных типов воспоминаний:")
        
        memory_types = ["working", "episodic", "semantic"]
        for memory_type in memory_types:
            print(f"\n{memory_type.upper()}Память:")
            type_summary = self.memory_tool.run({"action":"search",
                                                   "query":"",
                                                   "memory_type":memory_type,
                                                   "limit":3})
            print(type_summary)
        
        # Демонстрация эффекта поиска после интеграции
        print(f"\n🔍 Интегрированный тест на эффект поиска:")
        search_queries = [
            ("глубокое обучение", "Тестовый поиск перекрестного типа"),
            ("опыт обучения", "Тестирование встроенного извлечения данных из памяти"),
            ("важные понятия", "Тестирование извлечения семантической памяти")
        ]
        
        for query, description in search_queries:
            print(f"\nЗапрос: '{query}' ({description})")
            result = self.memory_tool.run({"action":"search",
                                            "query":query,
                                            "limit":3})
            print(result)

def main():
    """основная функция"""
    print("🔄 Демонстрация механизма интеграции памяти")
    print("Продемонстрировать интеллектуальный процесс преобразования кратковременной памяти в долговременную.")
    print("=" * 60)
    
    try:
        demo = MemoryConsolidationDemo()
        
        # 1. Установите исходные данные памяти.
        demo.setup_initial_memories()
        
        # 2. Демонстрация стандартов интеграции
        demo.demonstrate_consolidation_criteria()
        
        # 3. Продемонстрировать процесс интеграции
        demo.demonstrate_consolidation_process()
        
        # 4. Демонстрационная обработка метаданных
        demo.demonstrate_consolidation_metadata()
        
        # 5. Продемонстрировать многотипную интеграцию
        demo.demonstrate_multi_type_consolidation()
        
        # 6. Демонстрация преимуществ интеграции
        demo.demonstrate_consolidation_benefits()
        
        print("\n" + "=" * 60)
        print("🎉 Демонстрация механизма интеграции памяти завершена!")
        print("=" * 60)
        
        print("\n✨ Основные функции интеграции памяти:")
        print("1. 🎯 Интеллектуальная фильтрация — автоматическая фильтрация по порогам важности.")
        print("2. 🔄 Преобразование типов — гибкий механизм преобразования типов памяти.")
        print("3. 📋 Сохранение метаданных — сохраните исходную контекстную информацию нетронутой.")
        print("4. ⚡Автоматическая обработка – автоматическая интеграция без вмешательства человека.")
        print("5. 🔀 Поддержка нескольких путей — поддерживает несколько путей интеграции.")
        
        print("\n🎯 Концепция дизайна:")
        print("• Биомимикрия – имитирует процесс закрепления памяти в человеческом мозге.")
        print("• Интеллект – автоматически идентифицирует и обрабатывает важную информацию.")
        print("• Гибкость — поддержка нескольких стратегий и путей интеграции.")
        print("• Целостность — обеспечивает целостность и отслеживаемость памяти.")
        
        print("\n💡 Стоимость приложения:")
        print("• Управление знаниями – превратите временное обучение в долгосрочные знания.")
        print("• Накопление опыта – сохраните важный практический опыт")
        print("• Оптимизация системы: освободите место в кратковременной памяти.")
        print("• Интеллектуальное принятие решений – поддержка принятия решений на основе исторического опыта")
        
    except Exception as e:
        print(f"\n❌ Во время демонстрации произошла ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()