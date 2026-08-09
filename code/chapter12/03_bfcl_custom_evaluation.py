"""
Глава 12. Пример 3. Пользовательская оценка BFCL

Соответствующий документ: 12.2.5 Реализация оценки BFCL в HelloAgents – метод 3

В этом примере показано, как использовать низкоуровневые компоненты для пользовательского процесса оценки.
Подходит для сценариев, где требуется индивидуальный процесс оценки.
"""

from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.evaluation import BFCLDataset, BFCLEvaluator

# 1. Создайте агента
llm = HelloAgentsLLM()
agent = SimpleAgent(name="TestAgent", llm=llm)

# 2. Загрузите набор данных
dataset = BFCLDataset(
    bfcl_data_dir="./temp_gorilla/berkeley-function-call-leaderboard/bfcl_eval/data",
    category="simple_python"
)
data = dataset.load()

print(f"✅ {len(data)} загружены тестовые образцы")

# 3. Создайте оценщика
evaluator = BFCLEvaluator(
    dataset=dataset,
    category="simple_python"
)

# 4. Запустите оценку
results = evaluator.evaluate(
    agent=agent,
    max_samples=5  # Оцените только 5 образцов
)

# 5. Просмотр подробных результатов
print(f"\nРезультаты оценки:")
print(f"Общее количество образцов: {results['total_samples']}")
print(f"Количество правильных образцов: {results['correct_samples']}")
print(f"Точность: {results['overall_accuracy']:.2%}")

# 6. Просмотрите подробные результаты для каждого образца.
print(f"\nПодробные результаты:")
for detail in results['detailed_results']:
    print(f"Пример {detail['sample_id']}:")
    print(f"  Вопрос: {подробнее['question'][:50]}...")
    print(f"  Прогноз: {подробнее['predicted']}")
    print(f"  Правильный ответ: {подробно['ожидается']}")
    print(f"  Результат: {'Правильно', если подробно['успех'] иначе '❌ Ошибка'}")
    print()

# 7. Экспорт результатов
evaluator.export_results(
    results,
    output_file="./evaluation_results/bfcl_custom_result.json"
)

print("✅ Результаты экспортированы в ./evaluation_results/bfcl_custom_result.json.")

