#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример кода 08: Интеграция инструментов агента
Покажите, как интегрировать MemoryTool и RAGTool в среду HelloAgents.
"""

from dotenv import load_dotenv
load_dotenv()
import time
from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import MemoryTool, RAGTool

class AgentIntegrationDemo:
    """Демонстрационный класс по интеграции инструментов агента"""
    
    def __init__(self):
        self.setup_agent()
    
    def setup_agent(self):
        """Настройка агентов и инструментов"""
        print("🤖Настройки интеграции инструментов агента")
        print("=" * 50)
        
        # Инструмент инициализации
        print("1. Инструмент инициализации...")
        self.memory_tool = MemoryTool(
            user_id="agent_integration_user",
            memory_types=["working", "episodic", "semantic", "perceptual"]
        )
        
        self.rag_tool = RAGTool(
            knowledge_base_path="./agent_integration_kb",
            rag_namespace="agent_demo"
        )
        
        print("✅ Инициализация MemoryTool и RAGTool завершена")
        
        # СоздатьАгент
        print("\n2. Создать агента...")
        self.llm = HelloAgentsLLM()
        self.agent = SimpleAgent(
            name="Интеллектуальный помощник в обучении",
            llm=self.llm,
            system_prompt="Интеллектуальный помощник со встроенной памятью и функциями RAG."
        )
        
        print("✅ Создание агента завершено")
        
        # Инструмент регистрации
        print("\n3. Инструмент регистрации...")
        self.tool_registry = ToolRegistry()
        self.tool_registry.register_tool(self.memory_tool)
        self.tool_registry.register_tool(self.rag_tool)
        self.agent.tool_registry = self.tool_registry
        
        print("✅ Регистрация инструмента завершена")
        
        # Показать статус агента
        print(f"\n📊 Статус агента:")
        print(f"  Имя: {self.agent.name}")
        print(f"  Описание: {self.agent.system_prompt}")
        print(f"  Доступные инструменты: {list(self.tool_registry._tools.keys())}")
    
    def demonstrate_tool_registry_pattern(self):
        """Режим регистрации демо-инструмента"""
        print("\n🔧 Демонстрация режима регистрации инструмента")
        print("-" * 50)
        
        print("Особенности режима регистрации инструмента:")
        print("• 🔌 Единый интерфейс инструмента.")
        print("• 📋 Централизованное управление инструментами")
        print("• 🔄 Динамическая загрузка инструментов")
        print("• 🎯 Обнаружение возможностей инструмента.")
        
        # Процесс регистрации демо-инструмента
        print(f"\n🔧 Детали регистрации инструмента:")
        
        for tool_name, tool_instance in self.tool_registry._tools.items():
            print(f"\nИнструмент: {tool_name}")
            print(f"  Тип: {тип(экземпляр_инструмента).__имя__}")
            print(f"  Описание: {tool_instance.description}")
            
            # Показаны основные функции инструмента.
            if tool_name == "memory":
                print(f"  Основные функции: управление памятью, поиск, интеграция, забывание.")
                print(f"  Тип памяти: {tool_instance.memory_types}")
            elif tool_name == "rag":
                print(f"  Основные функции: обработка документов, интеллектуальные вопросы и ответы, поиск знаний.")
                print(f"  Пространство имен: {tool_instance.rag_namespace}")
        
        # Механизм обнаружения демонстрационных инструментов
        print(f"\n🔍Обнаружение возможностей инструмента:")
        available_tools = self.tool_registry.list_tools()
        print(f"Список доступных инструментов: {available_tools}")
        
        # Получите демонстрационные инструменты
        memory_tool = self.tool_registry.get_tool("memory")
        rag_tool = self.tool_registry.get_tool("rag")
        
        print(f"\n ✅ Инструмент успешно получен:")
        print(f"  Инструмент памяти: {type(memory_tool).__name__}")
        print(f"  Инструмент RAG: {type(rag_tool).__name__}")
    
    def demonstrate_unified_interface(self):
        """Демонстрация единого шаблона интерфейса"""
        print("\n🔗 Демонстрация режима единого интерфейса")
        print("-" * 50)
        
        print("Преимущества единого интерфейса:")
        print("• 🎯 Последовательный метод вызова")
        print("• 📝 Стандартизированная передача параметров.")
        print("• 🛡️ Единая обработка ошибок.")
        print("• 🔄 Упрощенное переключение инструментов.")
        
        # Демонстрация единого интерфейса запуска
        print(f"\n🔗 Демонстрация единого интерфейса запуска:")
        
        # Операции с инструментом памяти
        print(f"\n1. Операции с инструментом памяти:")
        memory_operations = [
            ("add", {
                "content": "Изучили модель интеграции инструментов агента.",
                "memory_type": "episodic",
                "importance": 0.8,
                "topic": "agent_integration"
            }),
            ("search", {
                "query": "Интеграция агента",
                "limit": 2
            }),
            ("stats", {})
        ]
        
        for operation, params in memory_operations:
            print(f"  Операция: Memory.run('{operation}', {params})")
            result = self.memory_tool.run({"action":operation, **params})
            print(f"  Результат: {str(результат)[:100]}...")
        
        # Работа с инструментом RAG
        print(f"\n2. Работа инструмента RAG:")
        
        # Сначала добавьте немного контента
        self.rag_tool.run({"action":"add_text",
                            "text":"Интеграция инструментов агентов — это основная функция платформы HelloAgents, позволяющая агентам использовать несколько инструментов для выполнения сложных задач.",
                            "document_id":"agent_integration_guide"})
        
        rag_operations = [
            ("search", {
                "query": "Интеграция инструментов агента",
                "limit": 2
            }),
            ("ask", {
                "question": "Что такое интеграция с инструментами агента?",
                "limit": 2
            }),
            ("stats", {})
        ]
        
        for operation, params in rag_operations:
            print(f"  Операция: rag.run('{operation}', {params})")
            result = self.rag_tool.run({"action":operation, **params})
            print(f"  Результат: {str(результат)[:100]}...")
    
    def demonstrate_collaborative_workflow(self):
        """Продемонстрировать совместный рабочий процесс"""
        print("\n🤝 Демонстрация совместного рабочего процесса")
        print("-" * 50)
        
        print("Сценарий совместной работы:")
        print("• 📚 Получить новые знания → Хранение ТРЯПКИ + Запись в Память")
        print("• 🔍 Обзор процесса обучения → Восстановление памяти + дополнение RAG")
        print("• 💡 Приложение знаний → Запрос RAG + Обновление памяти")
        print("• 📊 Анализ обучения → Статистическая интеграция двух инструментов.")
        
        # Сценарий 1: Получите новые знания
        print(f"\n📚 Сценарий 1: Получение новых знаний")
        
        # Добавить учебные материалы в RAG
        learning_content = """# Шаблон проектирования: шаблон наблюдателя

## Определение
Паттерн Observer определяет отношения зависимости «один ко многим» между объектами. При изменении состояния объекта все объекты, зависящие от него, будут уведомлены и автоматически обновлены.

## Структура
- Тема: ведет список наблюдателей и предоставляет методы для регистрации и удаления наблюдателей.
- Наблюдатель: определение интерфейса обновления.
- ConcreteSubject (конкретная тема): реализует интерфейс темы.
- ConcreteObserver (конкретный наблюдатель): реализует интерфейс наблюдателя.

## Сценарии применения
- Обработка событий графического интерфейса
- Модельно-представленная архитектура
- система публикации-подписки
"""
        
        rag_result = self.rag_tool.run({"action":"add_text",
                                         "text":learning_content,
                                         "document_id":"observer_pattern"})
        print(f"Результат добавления RAG: {rag_result}")
        
        # Записывайте учебную деятельность в систему памяти.
        memory_result = self.memory_tool.run({"action":"add",
                                                "content":"Изучили определение, структуру и сценарии применения шаблона проектирования наблюдателя.",
                                                "memory_type":"episodic",
                                                "importance":0.8,
                                                "topic":"design_patterns",
                                                "pattern_type":"observer"})
        print(f"Результат записи в память: {memory_result}")
        
        # Сценарий 2: Обзор процесса обучения
        print(f"\n🔍 Сценарий 2: Обзор процесса обучения")
        
        # Получить историю обучения из системы памяти
        memory_search = self.memory_tool.run({"action":"search",
                                                "query":"Изучение шаблонов проектирования",
                                                "limit":3})
        print(f"Обзор истории обучения: {memory_search}")
        
        # Получите соответствующие дополнения к знаниям от RAG.
        rag_search = self.rag_tool.run({"action":"search",
                                         "query":"Шаблон наблюдателя",
                                         "limit":2})
        print(f"Дополнение к содержанию знаний: {rag_search}")
        
        # Сценарий 3: Применение знаний
        print(f"\n💡 Сценарий 3: Применение знаний")
        
        # Запрос методов приложения через RAG
        application_query = self.rag_tool.run({"action":"ask",
                                                "question":"Для каких сценариев подходит шаблон наблюдателя?",
                                                "limit":2})
        print(f"Запрос сценария приложения: {application_query}")
        
        # Запишите практику применения в память
        application_memory = self.memory_tool.run({"action":"add",
                                                     "content":"Запросите сценарии применения шаблона наблюдателя и подготовьтесь к его использованию в проектах с графическим интерфейсом.",
                                                     "memory_type":"working",
                                                     "importance":0.7,
                                                     "application_context":"gui_project"})
        print(f"Запись приложения: {application_memory}")
        
        # Сценарий 4: Аналитика обучения
        print(f"\n📊 Сценарий 4: Анализ обучения")
        
        # Получить статистику системы памяти
        memory_stats = self.memory_tool.run({"action":"stats"})
        print(f"Статистика памяти: {memory_stats}")
        
        # Получить статистику системы RAG
        rag_stats = self.rag_tool.run({"action":"stats"})
        print(f"Статистика базы знаний: {rag_stats}")
        
        # Создание резюме исследования
        learning_summary = self.memory_tool.run({"action":"summary", "limit":5})
        print(f"Сводка обучения: {learning_summary}")
    
    def demonstrate_agent_orchestration(self):
        """Демонстрация возможностей оркестрации агента"""
        print("\n🎭Демонстрация возможностей оркестрации агентов")
        print("-" * 50)
        
        print("Возможности оркестрации агентов:")
        print("• 🧠 Умный выбор инструмента")
        print("• 🔄 Вызов цепочки инструментов")
        print("• 📊 Комплексный анализ результатов")
        print("• 🎯 Целенаправленное исполнение")
        
        # Оркестровка инструментов для моделирования сложных задач
        print(f"\n🎭 Пример постановки сложной задачи:")
        print(f"Задача: создать план обучения машинному обучению.")
        
        # Шаг 1. Получите структуру знаний о машинном обучении от RAG.
        print(f"\nШаг 1: Получите структуру знаний")
        
        # Добавьте знания в области машинного обучения
        ml_content = """# Путь обучения машинному обучению

## Базовый этап
1. Основы математики: линейная алгебра, вероятность и статистика, исчисление.
2. Основы программирования: Python, NumPy, Pandas.
3. Концепции машинного обучения: обучение с учителем, обучение без учителя, обучение с подкреплением.

## Продвинутый этап
1. Реализация алгоритма: реализация классических алгоритмов с нуля.
2. Глубокое обучение: нейронная сеть, CNN, RNN, Трансформер.
3. Практический проект: проект сквозного машинного обучения.

## Продвинутый этап
1. Оптимизация модели: настройка гиперпараметров, сжатие модели.
2. Развертывание и эксплуатация: развертывание модели, мониторинг и обновление.
3. Передовые технологии: новейшие статьи, проекты с открытым исходным кодом.
"""
        
        self.rag_tool.run({"action":"add_text",
                            "text":ml_content,
                            "document_id":"ml_learning_path"})
        
        knowledge_structure = self.rag_tool.run({"action":"ask",
                                                  "question":"Каков путь обучения машинному обучению?",
                                                  "limit":3})
        print(f"Структура знаний: {knowledge_structure[:200]}...")
        
        # Шаг 2: Запишите план обучения в систему памяти.
        print(f"\nШаг 2: Запишите план обучения")
        
        plan_memory = self.memory_tool.run({"action":"add",
                                             "content":"Разработан план обучения машинному обучению, включающий три этапа: базовый, продвинутый и продвинутый.",
                                             "memory_type":"episodic",
                                             "importance":0.9,
                                             "plan_type":"learning",
                                             "subject":"machine_learning"})
        print(f"Запись плана: {plan_memory}")
        
        # Шаг 3. Извлеките соответствующий опыт обучения
        print(f"\nШаг 3. Извлеките обучающий опыт")
        
        experience_search = self.memory_tool.run({"action":"search",
                                                    "query":"План обучения Опыт обучения",
                                                    "limit":3})
        print(f"Связанный опыт: {experience_search}")
        
        # Шаг 4. Интегрируйте для получения окончательных рекомендаций
        print(f"\nШаг 4. Создайте окончательные рекомендации.")
        
        final_advice = self.rag_tool.run({"action":"ask",
                                            "question":"Как разработать эффективный план обучения машинному обучению?",
                                            "limit":4})
        print(f"Последний совет: {final_advice[:300]}...")
        
        # Запишите процесс оркестровки
        orchestration_memory = self.memory_tool.run({"action":"add",
                                                       "content":"Выполнил сложные задачи по составлению плана обучения, используя совместную оркестровку RAG и Memory.",
                                                       "memory_type":"working",
                                                       "importance":0.8,
                                                       "task_type":"orchestration"})
        print(f"\nЗапись оркестрации: {orchestration_memory}")
    
    def demonstrate_performance_analysis(self):
        """Демонстрационный анализ производительности"""
        print("\n📊Демонстрация анализа производительности")
        print("-" * 50)
        
        print("Показатели анализа эффективности:")
        print("• ⏱️ Время отклика инструмента")
        print("• 🔄 Накладные расходы на переключение инструментов")
        print("• 💾 Использование памяти")
        print("• 🎯 Эффективность выполнения задач")
        
        # Тестирование производительности
        print(f"\n📊Тест производительности:")
        
        # Тестирование производительности одного инструмента
        print(f"\n1. Производительность одного инструмента:")
        
        # Производительность инструмента памяти
        start_time = time.time()
        for i in range(5):
            self.memory_tool.run({"action":"add",
                                   "content":f"Память для тестирования производительности {i+1}",
                                   "memory_type":"working",
                                   "importance":0.5})
        memory_time = time.time() - start_time
        print(f"Инструмент памяти – 5 операций добавления: {memory_time:.3f} секунд.")
        
        # Производительность инструмента RAG
        start_time = time.time()
        for i in range(3):
            self.rag_tool.run({"action":"search",
                                "query":f"Тестовый запрос {i+1}",
                                "limit":2})
        rag_time = time.time() - start_time
        print(f"Инструмент RAG — 3 операции поиска: {rag_time:.3f} секунд.")
        
        # Тестирование производительности совместной работы
        print(f"\n2. Результативность сотрудничества:")
        
        start_time = time.time()
        
        # Имитируйте совместный рабочий процесс
        self.rag_tool.run({"action":"add_text",
                            "text":"Это документ о проверке производительности.",
                            "document_id":"perf_test"})
        
        self.memory_tool.run({"action":"add",
                                "content":"Проведено тестирование производительности",
                                "memory_type":"working",
                                "importance":0.6})
        
        rag_result = self.rag_tool.run({"action":"search",
                                         "query":"Тестирование производительности",
                                         "limit":1})
        
        memory_result = self.memory_tool.run({"action":"search",
                                                "query":"Тестирование производительности",
                                                "limit":1})
        
        collaborative_time = time.time() - start_time
        print(f"Совместный рабочий процесс: {collaborative_time:.3f} секунд.")
        
        # Сводка анализа производительности
        print(f"\n📈 Сводка анализа производительности:")
        print(f"Средний отклик инструмента памяти: {memory_time/5:.3f} секунд/операция.")
        print(f"Средний отклик инструмента RAG: {rag_time/3:.3f} секунд/операция")
        print(f"Эффективность совместной работы: {collaborative_time:.3f} секунд/процесс.")
        
        # Получить окончательную статистику
        final_memory_stats = self.memory_tool.run({"action":"stats"})
        final_rag_stats = self.rag_tool.run({"action":"stats"})
        
        print(f"\n📊 Окончательный статус системы:")
        print(f"Система памяти: {final_memory_stats}")
        print(f"Система RAG: {final_rag_stats}")

def main():
    """основная функция"""
    print("🤖Демонстрация интеграции инструментов агента")
    print("Покажите, как интегрировать MemoryTool и RAGTool в среду HelloAgents.")
    print("=" * 70)
    
    try:
        demo = AgentIntegrationDemo()
        
        # 1. Демонстрация режима регистрации инструмента.
        demo.demonstrate_tool_registry_pattern()
        
        # 2. Демонстрация режима единого интерфейса
        demo.demonstrate_unified_interface()
        
        # 3. Демонстрация совместного рабочего процесса
        demo.demonstrate_collaborative_workflow()
        
        # 4. Демонстрация возможностей оркестровки агентов.
        demo.demonstrate_agent_orchestration()
        
        # 5. Демонстрация анализа производительности
        demo.demonstrate_performance_analysis()
        
        print("\n" + "=" * 70)
        print("🎉 Демонстрация интеграции инструментов агента завершена!")
        print("=" * 70)
        
        print("\n✨Основные функции интеграции агентов:")
        print("1. 🔧 Режим регистрации инструментов — единое управление и обнаружение инструментов.")
        print("2. 🔗 Единый дизайн интерфейса — единый метод вызова инструментов.")
        print("3. 🤝 Совместный рабочий процесс — интеллектуальное сотрудничество между инструментами.")
        print("4. 🎭 Возможности интеллектуальной оркестрации — автоматическая декомпозиция сложных задач.")
        print("5. 📊Анализ мониторинга производительности – комплексная оценка производительности")
        
        print("\n🎯 Преимущества дизайна:")
        print("• Модульность — инструменты разрабатываются независимо и могут гибко комбинироваться.")
        print("• Расширяемость — поддерживает динамическое добавление новых инструментов.")
        print("• Высокая сплоченность: каждый инструмент ориентирован на конкретную функциональность.")
        print("• Низкая связанность — минимальные зависимости между инструментами.")
        
        print("\n💡 Стоимость приложения:")
        print("• Умный помощник. Создайте многофункционального умного помощника.")
        print("• Управление знаниями – система управления знаниями на уровне предприятия.")
        print("• Платформа обучения – персонализированная система поддержки обучения.")
        print("• Поддержка принятия решений – принятие решений на основе знаний и опыта.")
        
    except Exception as e:
        print(f"\n❌ Во время демонстрации произошла ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()