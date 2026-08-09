#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример кода 09: Углубленный анализ четырех типов памяти
Подробное отображение особенностей реализации WorkMemory, EpisodicMemory, SemanticMemory и PerceptualMemory.
"""

from dotenv import load_dotenv
load_dotenv()
import os
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from hello_agents.tools import MemoryTool

class MemoryTypesDeepDive:
    """Демонстрационный класс углубленного анализа четырех типов памяти"""
    
    def __init__(self):
        self.setup_memory_systems()
    
    def setup_memory_systems(self):
        """Настройка различных систем памяти"""
        print("🧠 Углубленный анализ четырех типов памяти")
        print("=" * 60)
        
        # Создание специализированных экземпляров инструмента памяти.
        self.working_memory_tool = MemoryTool(
            user_id="working_memory_user",
            memory_types=["working"]
        )
        
        self.episodic_memory_tool = MemoryTool(
            user_id="episodic_memory_user", 
            memory_types=["episodic"]
        )
        
        self.semantic_memory_tool = MemoryTool(
            user_id="semantic_memory_user",
            memory_types=["semantic"]
        )
        
        self.perceptual_memory_tool = MemoryTool(
            user_id="perceptual_memory_user",
            memory_types=["perceptual"]
        )
        
        print("✅ Четыре системы памяти инициализированы")
    
    def demonstrate_working_memory(self):
        """Продемонстрировать характеристики рабочей памяти."""
        print("\n💭 Углубленный анализ рабочей памяти")
        print("-" * 60)
        
        print("🔍Особенности рабочей памяти:")
        print("• ⚡ Чрезвычайно быстрый доступ (чистая память)")
        print("• 📏 Ограниченная емкость (по умолчанию 50 ячеек памяти)")
        print("• ⏰ Автоматический срок действия (механизм TTL)")
        print("• 🔄 Подходит для временного хранения информации")
        
        # Ограничение емкости демо-версии
        print(f"\n1. Демонстрация ограничения мощности:")
        print("Добавьте много временной памяти, наблюдайте за управлением емкостью...")
        
        for i in range(8):
            content = f"Временная рабочая память {i+1}: шаг задачи {i+1} в данный момент обрабатывается."
            result = self.working_memory_tool.run({"action":"add",
                                                    "content":content,
                                                    "memory_type":"working",
                                                    "importance":0.3 + (i * 0.1),
                                                    "task_step":i+1})
            print(f"  Добавить память {i+1}: {result}")
        
        # Проверить текущий статус
        stats = self.working_memory_tool.run({"action":"stats"})
        print(f"\nТекущий статус рабочей памяти: {stats}")
        
        # Продемонстрировать механизм TTL
        print(f"\n2. Демонстрация механизма TTL (время жизни):")
        
        # Добавьте немного воспоминаний с временными метками
        current_time = datetime.now()
        
        # Имитация воспоминаний в разное время
        time_memories = [
            ("Просто подумал", 0, 0.8),
            ("Задача 5 минут назад", 5, 0.6),
            ("Напоминание 10 минут назад", 10, 0.4),
            ("Заметки, сделанные давным-давно", 30, 0.2)
        ]
        
        for content, minutes_ago, importance in time_memories:
            # Здесь мы моделируем разницу во времени
            result = self.working_memory_tool.run({"action":"add",
                                                    "content":content,
                                                    "memory_type":"working",
                                                    "importance":importance,
                                                    "simulated_age_minutes":minutes_ago})
            print(f"  Добавить память: {content} (смоделировано {minutes_ago} минуты назад)")
        
        # Демо быстрого поиска
        print(f"\ n3. Демо быстрого поиска:")
        
        search_queries = ["Задача", "идея", "напоминать"]
        
        for query in search_queries:
            start_time = time.time()
            results = self.working_memory_tool.run({"action":"search",
                                                     "query":query,
                                                     "memory_type":"working",
                                                     "limit":3})
            search_time = time.time() - start_time
            print(f"  Запрос «{query}»: {search_time:.4f} секунд.")
            print(f"    Результаты: {results[:100]}...")
        
        # Демонстрационная автоматическая очистка
        print(f"\n4. Автоматический механизм очистки:")
        
        # Получите статистику перед чисткой
        before_stats = self.working_memory_tool.run({"action":"stats"})
        print(f"Перед очисткой: {before_stats}")
        
        # Запустить очистку (путем забывания неважных воспоминаний)
        forget_result = self.working_memory_tool.run({"action":"forget",
                                                       "strategy":"importance_based",
                                                       "threshold":0.4})
        print(f"Чистый результат: {forget_result}")
        
        # Получить очищенную статистику
        after_stats = self.working_memory_tool.run({"action":"stats"})
        print(f"После очистки: {after_stats}")
    
    def demonstrate_episodic_memory(self):
        """Продемонстрировать особенности эпизодической памяти."""
        print("\n📖Углубленный анализ эпизодической памяти")
        print("-" * 60)
        
        print("🔍Особенности эпизодической памяти:")
        print("• 📅 Полная запись временных рядов")
        print("• 🎭 Богатая контекстная информация")
        print("• 🔗 Поддержка построения цепочки памяти")
        print("• 💾 Постоянное хранение")
        
        # Демонстрация полной записи события
        print(f"\n1. Полная демонстрация записи события:")
        
        # Имитация полного сеанса обучения
        learning_session = [
            {
                "content": "Начните изучать машинное обучение Python",
                "context": "Обучение начинается",
                "location": "Учебная комната дома",
                "mood": "фокус",
                "importance": 0.7
            },
            {
                "content": "Изучили математические принципы линейной регрессии.",
                "context": "теоретическое исследование",
                "chapter": "Глава 3",
                "difficulty": "середина",
                "importance": 0.8
            },
            {
                "content": "Реализована первая модель линейной регрессии.",
                "context": "Практическое программирование",
                "code_lines": 45,
                "bugs_fixed": 2,
                "importance": 0.9
            },
            {
                "content": "Выполнил упражнения после занятий.",
                "context": "Практика консолидации",
                "exercises_completed": 5,
                "accuracy": 0.8,
                "importance": 0.6
            },
            {
                "content": "Подведите итоги сегодняшнего обучения",
                "context": "Краткое описание обучения",
                "key_concepts": ["линейная регрессия", "градиентный спуск", "функция потерь"],
                "importance": 0.8
            }
        ]
        
        session_id = f"learning_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for i, event in enumerate(learning_session):
            result = self.episodic_memory_tool.run({"action":"add",
                                                     "content":event["content"],
                                                     "memory_type":"episodic",
                                                     "importance":event["importance"],
                                                     "session_id":session_id,
                                                     "sequence_number":i+1,
                                                     **{k: v for k, v in event.items() if k not in ["content", "importance"]}})
            print(f"  Событие {i+1}: {result}")
        
        # Получение демонстрационного временного ряда
        print(f"\n2. Демонстрация поиска временных рядов:")
        
        # Искать в хронологическом порядке
        timeline_search = self.episodic_memory_tool.run({"action":"search",
                                                          "query":"изучать",
                                                          "memory_type":"episodic",
                                                          "limit":10})
        print(f"График обучения: {timeline_search}")
        
        # Поиск по сеансу
        session_search = self.episodic_memory_tool.run({"action":"search",
                                                         "query":"линейная регрессия",
                                                         "memory_type":"episodic",
                                                         "limit":5})
        print(f"Содержимое сеанса: {session_search}")
        
        # Демонстрируйте контекстуальное богатство
        print(f"\n3. Демонстрация контекстной информации:")
        
        # Добавьте воспоминания с богатым контекстом
        rich_context_memory = {
            "content": "Принял участие в сессии по обмену технологиями искусственного интеллекта",
            "event_type": "conference",
            "location": "Пекинский международный конференц-центр",
            "speakers": ["Профессор Чжан", "доктор Ли", "Инженер Ван"],
            "topics": ["глубокое обучение", "обработка естественного языка", "компьютерное зрение"],
            "attendees_count": 200,
            "duration_hours": 6,
            "weather": "солнечный",
            "transportation": "метро",
            "networking_contacts": 3,
            "key_insights": ["Эволюция архитектуры Transformer", "Перспектива мультимодального обучения"],
            "follow_up_actions": ["Прочтите рекомендуемые статьи", "Попробуйте новый фреймворк"],
            "satisfaction_rating": 9
        }
        
        context_result = self.episodic_memory_tool.run({"action":"add",
                                                         "content":rich_context_memory["content"],
                                                         "memory_type":"episodic",
                                                         "importance":0.9,
                                                         **{k: v for k, v in rich_context_memory.items() if k != "content"}})
        print(f"Обогатить контекстную память: {context_result}")
        
        # Демо цепочка воспоминаний
        print(f"\n4. Построение цепочки памяти:")
        
        # Создайте связанные последовательности памяти
        memory_chain = [
            ("Видел статью про GPT.", "trigger", None),
            ("Решил углубиться в архитектуру Трансформера.", "decision", "trigger"),
            ("Загрузите и прочитайте статью «Внимание – это все, что вам нужно».", "action", "decision"),
            ("Реализована упрощенная версия механизма самообслуживания.", "implementation", "action"),
            ("Прикладные знания, полученные в проектах", "application", "implementation")
        ]
        
        chain_memories = {}
        for content, chain_type, parent_type in memory_chain:
            parent_id = chain_memories.get(parent_type) if parent_type else None
            
            result = self.episodic_memory_tool.run({"action":"add",
                                                     "content":content,
                                                     "memory_type":"episodic",
                                                     "importance":0.7,
                                                     "chain_type":chain_type,
                                                     "parent_memory":parent_id,
                                                     "chain_id":"gpt_learning_chain"})
            
            # Извлечь идентификатор памяти (упрощенная обработка)
            memory_id = f"{chain_type}_memory"
            chain_memories[chain_type] = memory_id
            print(f"  Цепная память: {content} (тип: {chain_type})")
        
        # Получить всю цепочку
        chain_search = self.episodic_memory_tool.run({"action":"search",
                                                        "query":"GPT Transformer",
                                                        "memory_type":"episodic",
                                                        "limit":8})
        print(f"Поиск по цепочке памяти: {chain_search}")
    
    def demonstrate_semantic_memory(self):
        """Продемонстрировать характеристики семантической памяти."""
        print("\n🧠 Углубленный анализ семантической памяти")
        print("-" * 60)
        
        print("🔍Особенности семантической памяти:")
        print("• 🔗 Структурированное хранилище графа знаний.")
        print("• 🎯 Абстрактное представление концепций и отношений.")
        print("• 🔍 Поиск семантического сходства")
        print("• 🧮 Поддерживает рассуждения и корреляции")
        
        # Хранилище демонстрационных концепций
        print(f"\n1. Демонстрация концепции хранения знаний:")
        
        # Добавляйте различные типы концептуальных знаний
        concepts = [
            {
                "content": "Машинное обучение — это отрасль искусственного интеллекта, которая использует алгоритмы, позволяющие компьютерам изучать закономерности на основе данных.",
                "concept_type": "definition",
                "domain": "artificial_intelligence",
                "keywords": ["машинное обучение", "ИИ", "алгоритм", "данные", "модель"],
                "importance": 0.9
            },
            {
                "content": "Обучение с учителем использует размеченные данные для обучения моделей, включая задачи классификации и регрессии.",
                "concept_type": "category",
                "domain": "machine_learning",
                "parent_concept": "машинное обучение",
                "subcategories": ["Классификация", "возвращаться"],
                "importance": 0.8
            },
            {
                "content": "Градиентный спуск — это алгоритм оптимизации, который минимизирует функцию потерь путем итеративного обновления параметров.",
                "concept_type": "algorithm",
                "domain": "optimization",
                "mathematical_basis": "Исчисление",
                "applications": ["Обучение нейронной сети", "линейная регрессия"],
                "importance": 0.8
            },
            {
                "content": "Переобучение означает, что модель хорошо работает на обучающих данных, но имеет плохую способность к обобщению новых данных.",
                "concept_type": "problem",
                "domain": "machine_learning",
                "causes": ["Сложность модели слишком высока", "Недостаточно данных для обучения"],
                "solutions": ["регуляризация", "перекрестная проверка", "Остановитесь раньше"],
                "importance": 0.7
            }
        ]
        
        for concept in concepts:
            result = self.semantic_memory_tool.run({"action":"add",
                                                     "content":concept["content"],
                                                     "memory_type":"semantic",
                                                     "importance":concept["importance"],
                                                     **{k: v for k, v in concept.items() if k not in ["content", "importance"]}})
            print(f"  Хранилище концепций: {concept['concept_type']} – {result}")
        
        # Продемонстрировать реляционное рассуждение
        print(f"\n2. Демонстрация реляционных рассуждений:")
        
        # Добавьте знания об отношениях
        relationships = [
            {
                "content": "Глубокое обучение — это разновидность машинного обучения, в которой используются многослойные нейронные сети.",
                "relation_type": "is_subset_of",
                "subject": "глубокое обучение",
                "object": "машинное обучение",
                "strength": 0.9
            },
            {
                "content": "Сверточные нейронные сети особенно подходят для обработки данных изображений.",
                "relation_type": "suitable_for",
                "subject": "сверточная нейронная сеть",
                "object": "обработка изображений",
                "strength": 0.8
            },
            {
                "content": "Алгоритм обратного распространения ошибки используется для обучения нейронных сетей.",
                "relation_type": "used_for",
                "subject": "Обратное распространение ошибки",
                "object": "Обучение нейронной сети",
                "strength": 0.9
            }
        ]
        
        for relation in relationships:
            result = self.semantic_memory_tool.run({"action":"add",
                                                     "content":relation["content"],
                                                     "memory_type":"semantic",
                                                     "importance":0.8,
                                                     **{k: v for k, v in relation.items() if k != "content"}})
            print(f"  Реляционное хранилище: {relation['relation_type']} – {result}")
        
        # Демонстрация семантического поиска
        print(f"\n3. Поиск семантического сходства:")
        
        semantic_queries = [
            "Что такое искусственный интеллект?",
            "Как предотвратить переобучение модели?",
            "Методы обучения нейронных сетей",
            "Технология распознавания изображений"
        ]
        
        for query in semantic_queries:
            start_time = time.time()
            results = self.semantic_memory_tool.run({"action":"search",
                                                      "query":query,
                                                      "memory_type":"semantic",
                                                      "limit":3})
            search_time = time.time() - start_time
            print(f"  Запрос: '{query}' ({search_time:.4f} секунд)")
            print(f"    Результаты: {results[:150]}...")
        
        # Продемонстрировать построение графа знаний
        print(f"\n4. Построение графа знаний:")
        
        # Добавляйте сущности и отношения
        entities_and_relations = [
            {
                "content": "TensorFlow — это платформа глубокого обучения, разработанная Google.",
                "entity_type": "framework",
                "developer": "Google",
                "domain": "deep_learning",
                "language": "Python",
                "year": 2015
            },
            {
                "content": "PyTorch — это платформа глубокого обучения, разработанная Facebook и известная своей динамической графикой.",
                "entity_type": "framework", 
                "developer": "Facebook",
                "domain": "deep_learning",
                "feature": "dynamic_graph",
                "language": "Python"
            },
            {
                "content": "BERT — это предварительно обученная языковая модель, основанная на Transformer.",
                "entity_type": "model",
                "architecture": "Transformer",
                "task": "natural_language_processing",
                "training_method": "pre_training"
            }
        ]
        
        for item in entities_and_relations:
            result = self.semantic_memory_tool.run({"action":"add",
                                                     "content":item["content"],
                                                     "memory_type":"semantic",
                                                     "importance":0.8,
                                                     **{k: v for k, v in item.items() if k != "content"}})
            print(f"  Отношения сущностей: {item['entity_type']} – {result}")
        
        # Получить статистику семантической памяти
        semantic_stats = self.semantic_memory_tool.run({"action":"stats"})
        print(f"\nСтатистика семантической памяти: {semantic_stats}")
    
    def demonstrate_perceptual_memory(self):
        """Продемонстрировать характеристики перцептивной памяти."""
        print("\n👁️ Углубленный анализ перцептивной памяти")
        print("-" * 60)
        
        print("🔍Особенности перцептивной памяти:")
        print("• 🎨 Поддержка мультимодальных данных")
        print("• 🔄 Межмодальный поиск по сходству")
        print("• 📊 Семантическое понимание сенсорных данных")
        print("• 🎯 Генерация и поиск контента")
        
        # Память восприятия демо-текста
        print(f"\n1. Память восприятия текста:")
        
        text_perceptions = [
            {
                "content": "Это прекрасное стихотворение: Прилив весенней реки достигает уровня моря, и яркая луна на море поднимается вместе с приливом.",
                "modality": "text",
                "genre": "poetry",
                "emotion": "peaceful",
                "language": "chinese",
                "aesthetic_value": 0.9
            },
            {
                "content": "Техническая документация: интерфейс API возвращает данные в формате JSON, включая код состояния и тело ответа.",
                "modality": "text",
                "genre": "technical",
                "complexity": "medium",
                "language": "chinese",
                "practical_value": 0.8
            }
        ]
        
        for perception in text_perceptions:
            result = self.perceptual_memory_tool.run({"action":"add",
                                                       "content":perception["content"],
                                                       "memory_type":"perceptual",
                                                       "importance":0.7,
                                                       **{k: v for k, v in perception.items() if k != "content"}})
            print(f"  Восприятие текста: {восприятие['жанр']} – {результат}")
        
        # Демонстрация образной перцептивной памяти (моделирование)
        print(f"\n2. Память восприятия изображений (моделирование):")
        
        # Аналоговые данные изображения
        image_perceptions = [
            {
                "content": "Красивое фото закатного пейзажа",
                "modality": "image",
                "file_path": "/simulated/sunset.jpg",
                "scene_type": "landscape",
                "colors": ["orange", "red", "purple"],
                "objects": ["sun", "clouds", "horizon"],
                "mood": "serene",
                "quality": "high"
            },
            {
                "content": "Схема технической архитектуры, показывающая проект системы микросервисов",
                "modality": "image", 
                "file_path": "/simulated/architecture.png",
                "diagram_type": "technical",
                "components": ["API Gateway", "Services", "Database"],
                "complexity": "high",
                "purpose": "documentation"
            }
        ]
        
        for perception in image_perceptions:
            result = self.perceptual_memory_tool.run({"action":"add",
                                                       "content":perception["content"],
                                                       "memory_type":"perceptual",
                                                       "importance":0.8,
                                                       **{k: v for k, v in perception.items() if k != "content"}})
            print(f"  Восприятие изображения: {восприятие['content']} – {result}")
        
        # Демонстрация аудиоперцептивной памяти (симуляция)
        print(f"\n3. Аудиоперцептивная память (моделирование):")
        
        audio_perceptions = [
            {
                "content": "Красивое исполнение классической музыки",
                "modality": "audio",
                "file_path": "/simulated/classical.mp3",
                "genre": "classical",
                "instruments": ["piano", "violin", "cello"],
                "tempo": "andante",
                "emotion": "elegant",
                "duration_seconds": 240
            },
            {
                "content": "Записи технических конференций, на которых обсуждаются тенденции развития ИИ",
                "modality": "audio",
                "file_path": "/simulated/conference.wav",
                "content_type": "speech",
                "topic": "artificial_intelligence",
                "speakers": 3,
                "language": "chinese",
                "duration_seconds": 1800
            }
        ]
        
        for perception in audio_perceptions:
            result = self.perceptual_memory_tool.run({"action":"add",
                                                       "content":perception["content"],
                                                       "memory_type":"perceptual",
                                                       "importance":0.7,
                                                       **{k: v for k, v in perception.items() if k != "content"}})
            print(f"  Восприятие звука: {восприятие['content']} – {result}")
        
        # Демонстрация кросс-модального поиска
        print(f"\n4. Демонстрация кросс-модального поиска:")
        
        cross_modal_queries = [
            ("красивые пейзажи", "Ищу контент, связанный с визуальной красотой."),
            ("Техническая документация", "Найдите мультимодальный контент, связанный с технологиями"),
            ("музыка и искусство", "Восстановление воспоминаний, связанных с искусством"),
            ("встречи и обсуждения", "Найдите контент, связанный с общением")
        ]
        
        for query, description in cross_modal_queries:
            results = self.perceptual_memory_tool.run({"action":"search",
                                                        "query":query,
                                                        "memory_type":"perceptual",
                                                        "limit":3})
            print(f"  Кросс-модальный запрос: '{query}' ({description})")
            print(f"    Результаты: {results[:120]}...")
        
        # Продемонстрировать анализ особенностей восприятия
        print(f"\n5. Анализ перцептивных особенностей:")
        
        # Получить статистику перцептивной памяти
        perceptual_stats = self.perceptual_memory_tool.run({"action":"stats"})
        print(f"Статистика перцептивной памяти: {perceptual_stats}")
        
        # Анализ распределения различных режимов
        modality_analysis = self.perceptual_memory_tool.run({"action":"search",
                                                              "query":"Модальный анализ",
                                                              "memory_type":"perceptual",
                                                              "limit":10})
        print(f"Анализ модального распределения: {modality_anaлиз}")
    
    def demonstrate_memory_interactions(self):
        """Демонстрирует взаимодействие четырех типов памяти."""
        print("\n🔄 Интерактивная демонстрация четырех типов памяти")
        print("-" * 60)
        
        print("🔍 Режим взаимодействия с памятью:")
        print("• 🔄 Рабочая память → Эпизодическая память (закрепление важных событий)")
        print("• 📚 Эпизодическая память → Семантическая память (абстракция опыта)")
        print("• 👁️ Перцептивная память → другие воспоминания (мультимодальная интеграция информации)")
        print("• 🧠Семантическая память → рабочая память (активация знаний)")
        
        # Имитировать полный процесс обучения
        print(f"\nПолное моделирование процесса обучения:")
        
        # 1. Стадия восприятия: получение мультимодальной информации.
        print(f"\n1. Стадия восприятия – получение информации:")
        
        perceptual_input = self.perceptual_memory_tool.run({"action":"add",
                                                             "content":"Просмотрен видеоурок по глубокому обучению.",
                                                             "memory_type":"perceptual",
                                                             "importance":0.8,
                                                             "modality":"video",
                                                             "topic":"deep_learning",
                                                             "duration_minutes":45,
                                                             "quality":"high"})
        print(f"Перцептивная память: {perceptual_input}")
        
        # 2. Этап рабочей памяти: временная обработка и мышление.
        print(f"\n2. Этап рабочей памяти – временная обработка:")
        
        working_thoughts = [
            "Понять основные принципы работы сверточных нейронных сетей.",
            "Необходимо запомнить этапы расчета обратного распространения ошибки.",
            "Думая о знаниях линейной алгебры, которые я получил раньше",
            "Планируйте реализацию простой модели CNN."
        ]
        
        for thought in working_thoughts:
            result = self.working_memory_tool.run({"action":"add",
                                                    "content":thought,
                                                    "memory_type":"working",
                                                    "importance":0.6,
                                                    "processing_stage":"active_thinking"})
            print(f"  Рабочая память: {мысль[:30]}... - {результат}")
        
        # 3. Стадия эпизодической памяти: записывайте полные события обучения.
        print(f"\n3. Стадия эпизодической памяти – запись событий:")
        
        episodic_event = self.episodic_memory_tool.run({"action":"add",
                                                         "content":"Вы завершили видеоурок по глубокому обучению и поняли основные концепции CNN.",
                                                         "memory_type":"episodic",
                                                         "importance":0.9,
                                                         "event_type":"learning_session",
                                                         "duration_minutes":45,
                                                         "location":"дома",
                                                         "learning_outcome":"Понимать принципы CNN",
                                                         "next_action":"Практическое программирование"})
        print(f"Эпизодическая память: {episodic_event}")
        
        # 4. Этап семантической памяти: хранение абстрактных знаний.
        print(f"\n4. Этап семантической памяти – абстракция знаний:")
        
        semantic_knowledge = [
            {
                "content": "Сверточные нейронные сети извлекают особенности изображения через сверточные слои и подходят для задач компьютерного зрения.",
                "concept": "CNN",
                "domain": "deep_learning",
                "application": "computer_vision"
            },
            {
                "content": "Алгоритм обратного распространения ошибки вычисляет градиенты с помощью правила цепочки и используется для обновления параметров сети.",
                "concept": "backpropagation",
                "domain": "optimization",
                "mathematical_basis": "chain_rule"
            }
        ]
        
        for knowledge in semantic_knowledge:
            result = self.semantic_memory_tool.run({"action":"add",
                                                     "content":knowledge["content"],
                                                     "memory_type":"semantic",
                                                     "importance":0.8,
                                                     **{k: v for k, v in knowledge.items() if k != "content"}})
            print(f"  Семантическая память: {знание['концепция']} – {результат}")
        
        # 5. Демонстрация интеграции памяти
        print(f"\n5. Демонстрация интеграции памяти:")
        
        # От интеграции рабочей памяти к эпизодической памяти
        consolidation_result = self.working_memory_tool.run({"action":"consolidate",
                                                              "from_type":"working",
                                                              "to_type":"episodic",
                                                              "importance_threshold":0.6})
        print(f"Консолидация рабочей памяти: {consolidation_result}")
        
        # Извлечение по типам памяти
        print(f"\n6. Поиск по типам памяти:")
        
        query = "Глубокое обучение CNN"
        
        # Поиск по всем типам памяти
        memory_tools = [
            ("рабочая память", self.working_memory_tool),
            ("эпизодическая память", self.episodic_memory_tool),
            ("семантическая память", self.semantic_memory_tool),
            ("перцептивная память", self.perceptual_memory_tool)
        ]
        
        for memory_name, tool in memory_tools:
            results = tool.run({"action":"search", "query":query, "limit":2})
            print(f"  Извлечение {memory_name}: {results[:80]}...")
        
        # Получить статистику для всех систем памяти
        print(f"\n7. Общее состояние системы:")
        
        for memory_name, tool in memory_tools:
            stats = tool.run({"action":"stats"})
            print(f"  {memory_name}: {stats}")

def main():
    """основная функция"""
    print("🧠 Углубленный анализ и демонстрация четырех типов памяти.")
    print("Подробное отображение рабочей памяти, эпизодической памяти, семантической памяти, перцептивной памяти.")
    print("=" * 80)
    
    try:
        demo = MemoryTypesDeepDive()
        
        # 1. Демонстрация рабочей памяти
        demo.demonstrate_working_memory()
        
        # 2. Демонстрация эпизодической памяти
        demo.demonstrate_episodic_memory()
        
        # 3. Демонстрация семантической памяти
        demo.demonstrate_semantic_memory()
        
        # 4. Демонстрация перцептивной памяти
        demo.demonstrate_perceptual_memory()
        
        # 5. Интерактивная демонстрация памяти.
        demo.demonstrate_memory_interactions()
        
        print("\n" + "=" * 80)
        print("🎉 Завершен углубленный анализ четырех типов памяти!")
        print("=" * 80)
        
        print("\n✨ Сводная информация о характеристиках типов памяти:")
        print("1. 💭 Рабочая память – быстрое временное хранилище, ограниченная емкость, автоматическое истечение срока действия.")
        print("2. 📖 Эпизодическая память – полные записи событий, временные ряды, богатый контекст.")
        print("3. 🧠Семантическая память – хранение абстрактных знаний, концептуальных связей, смысловых рассуждений.")
        print("4. 👁️ Перцептивная память – мультимодальная поддержка, кросс-модальный поиск, перцептивное понимание.")
        
        print("\n🔄 Режим взаимодействия с памятью:")
        print("• Восприятие → Работа → Ситуация → Семантика (поток обработки информации).")
        print("• Семантика → Работа (активация и применение знаний)")
        print("• Поиск и интеграция перекрестного типа (интеллектуальное управление памятью).")
        
        print("\n💡 Расчетная стоимость:")
        print("• Имитировать когнитивные процессы человека")
        print("• Поддерживает многоуровневую обработку информации.")
        print("• Внедрить интеллектуальное управление памятью.")
        print("• Предоставлять широкие возможности поиска.")
        
    except Exception as e:
        print(f"\n❌ Во время демонстрации произошла ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()