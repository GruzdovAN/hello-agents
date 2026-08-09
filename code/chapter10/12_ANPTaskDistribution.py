from hello_agents.protocols import ANPDiscovery, register_service
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools.builtin import ANPTool
import random
from dotenv import load_dotenv

load_dotenv()
llm = HelloAgentsLLM()

# 1. Создайте центр обнаружения сервисов.
discovery = ANPDiscovery()

# 2. Зарегистрируйте несколько вычислительных узлов.
for i in range(10):
    register_service(
        discovery=discovery,
        service_id=f"compute_node_{i}",
        service_name=f"Вычислительный узел {i}",
        service_type="compute",
        capabilities=["data_processing", "ml_training"],
        endpoint=f"http://node{i}:8000",
        metadata={
            "load": random.uniform(0.1, 0.9),
            "cpu_cores": random.choice([4, 8, 16]),
            "memory_gb": random.choice([16, 32, 64]),
            "gpu": random.choice([True, False])
        }
    )

print(f"✅ Зарегистрированы {len(discovery.list_all_services())} вычислительных узлов.")

# 3. Создайте агент планирования задач.
scheduler = SimpleAgent(
    name="планировщик задач",
    llm=llm,
    system_prompt="""Вы — интеллектуальный планировщик задач, ответственный за:
1. Анализ требований задачи
2. Выберите наиболее подходящий вычислительный узел.
3. Ставьте задачи

При выборе узла учитывайте такие факторы, как нагрузка, количество ядер ЦП, память и графический процессор.

При использовании инструмента service_discovery необходимо указать параметр действия:
- Просмотреть все узлы: {"action": "discover_services", "service_type": "compute"}
- Получить сетевую статистику: {"action": "get_stats"}"""
)

# Добавить инструмент ANP
anp_tool = ANPTool(
    name="service_discovery",
    description="Инструмент обнаружения сервисов для поиска и выбора вычислительных узлов",
    discovery=discovery
)
scheduler.add_tool(anp_tool)

# 4. Интеллектуальное распределение задач
def assign_task(task_description):
    print(f"\nЗадача: {task_description}")
    print("=" * 50)

    # Позвольте агенту разумно выбирать узлы
    response = scheduler.run(f"""
Пожалуйста, выберите наиболее подходящий вычислительный узел для следующих задач:
{task_description}

Шаги:
1. Используйте инструмент service_discovery для просмотра всех доступных вычислительных узлов (service_type="compute").
2. Анализ характеристик каждого узла (нагрузка, количество ядер ЦП, памяти, графического процессора и т. д.)
3. Выберите наиболее подходящий узел в зависимости от требований задачи.
4. Объясните причины своего выбора

Пожалуйста, прямо укажите идентификатор узла и причину вашего окончательного выбора.
    """)

    print(response)
    print("=" * 50)

# Тестируйте разные типы задач
assign_task("Для обучения большой модели глубокого обучения требуется поддержка графического процессора.")
assign_task("Обработка больших объемов текстовых данных требует большого объема памяти.")
assign_task("Выполнение облегченных задач анализа данных")