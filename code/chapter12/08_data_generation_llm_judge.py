"""
Глава 12 Пример 8: Оценка судьи LLM

Соответствующий документ: 12.4.3 Оценка судьи LLM.

В этом примере показано, как использовать LLM Judge для оценки качества сгенерированных вопросов AIME.

Судья LLM оценивает качество вопросов по 4 измерениям:
1. Корректность. Правильны ли вопросы и ответы?
2. Ясность: ясно ли сформулирована тема?
3. Соответствие сложности: соответствует ли сложность уровню AIME.
4. Полнота. Является ли вопрос полным?
"""

import sys
import os
import json

# Добавить путь HelloAgents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "HelloAgents"))

from hello_agents import HelloAgentsLLM
from hello_agents.evaluation import LLMJudge

# 1. Подготовьте сгенерированные данные для вопросов.
generated_problems = [
    {
        "problem_id": "generated_001",
        "problem": "Find the number of positive integers $n$ such that $n^2 + 19n + 92$ is a perfect square.",
        "answer": "4",
        "solution": "Let $n^2 + 19n + 92 = m^2$ for some positive integer $m$..."
    },
    {
        "problem_id": "generated_002",
        "problem": "In triangle $ABC$, $AB = 13$, $BC = 14$, and $CA = 15$. Find the area of the triangle.",
        "answer": "84",
        "solution": "Using Heron's formula, $s = (13+14+15)/2 = 21$..."
    }
]

# 2. Создайте судью-оценщика LLM.
llm = HelloAgentsLLM(model_name="gpt-4o")
judge = LLMJudge(llm=llm)

# 3. Оцените каждый вопрос
print("="*60)
print("Оценка судьи LLM")
print("="*60)

all_scores = []

for i, problem in enumerate(generated_problems, 1):
    print(f"\nВопросы для оценки {i}/{len(generated_problems)}")
    print(f"Идентификатор вопроса: {problem['problem_id']}")
    
    # Один вопрос для оценки
    result = judge.evaluate_single(problem)
    
    # Показать результаты оценки
    print(f"\nРезультаты оценки:")
    print(f"  Правильность: {result['correctness']}/5")
    print(f"  Ясность: {result['ясность']}/5")
    print(f"  Соответствие по сложности: {result['difficulty_match']}/5")
    print(f"  Полнота: {result['completeness']}/5")
    print(f"  Средний балл: {result['average_score']:.2f}/5")
    print(f"\nКомментарии:")
    print(f"  {result['feedback']}")
    
    all_scores.append(result)

# 4. Посчитать общую статистику
print("\n" + "="*60)
print("Общая статистика")
print("="*60)

avg_correctness = sum(s['correctness'] for s in all_scores) / len(all_scores)
avg_clarity = sum(s['clarity'] for s in all_scores) / len(all_scores)
avg_difficulty = sum(s['difficulty_match'] for s in all_scores) / len(all_scores)
avg_completeness = sum(s['completeness'] for s in all_scores) / len(all_scores)
avg_overall = sum(s['average_score'] for s in all_scores) / len(all_scores)

print(f"\nСредний балл:")
print(f"  Правильность: {avg_correctness:.2f}/5")
print(f"  Ясность: {avg_clarity:.2f}/5.")
print(f"  Уровень сложности: {avg_difficulty:.2f}/5.")
print(f"  Полнота: {avg_completeness:.2f}/5")
print(f"  Общий средний показатель: {avg_overall:.2f}/5.")

# 5. Оценка качества
print(f"\nОценка качества:")
if avg_overall >= 4.0:
    print("✅ Отлично - вопросы высокого качества и их можно использовать напрямую.")
elif avg_overall >= 3.0:
    print("⚠️ Хорошее — качество вопроса приемлемое, рекомендуется проверка вручную.")
elif avg_overall >= 2.0:
    print("⚠️ Среднее. Качество вопросов среднее и требует значительного улучшения.")
else:
    print("❌ Плохое — качество вопроса плохое, его необходимо перегенерировать.")

# 6. Сохранить результаты оценки
output_file = "./evaluation_results/llm_judge_results.json"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'problems': generated_problems,
        'scores': all_scores,
        'statistics': {
            'avg_correctness': avg_correctness,
            'avg_clarity': avg_clarity,
            'avg_difficulty': avg_difficulty,
            'avg_completeness': avg_completeness,
            'avg_overall': avg_overall
        }
    }, f, indent=2, ensure_ascii=False)

print(f"\n ✅ Результаты экзамена сохранены в {output_file}")

# Пример вывода запуска:
# ============================================================
# Оценка судьи LLM
# ============================================================
# 
# Оценочные вопросы 1/2
# Идентификатор вопроса: сгенерированный_001
# 
# Результаты оценки:
#   Правильность: 5/5
#   Четкость: 4/5
#   Сложность матча: 5/5
#   Полнота: 5/5
#   Средний балл: 4,75/5
# 
# Комментарии:
#   This is an excellent AIME-level problem. The problem is well-posed,
#   the solution is correct, and the difficulty is appropriate.
# 
# Оценочные вопросы 2/2
# Идентификатор вопроса: сгенерированный_002
# 
# Результаты оценки:
#   Правильность: 5/5
#   Четкость: 5/5
#   Сложность матча: 3/5
#   Полнота: 5/5
#   Средний балл: 4,50/5
# 
# Комментарии:
#   The problem is correct and clear, but the difficulty is slightly
#   below AIME level. Consider adding more complexity.
# 
# ============================================================
# Общая статистика
# ============================================================
# 
# Средний балл:
#   Правильность: 5.00/5
#   Четкость: 4,50/5
#   Сложность матча: 4.00/5
#   Полнота: 5.00/5
#   Общий средний балл: 4,62/5
# 
# Оценка качества:
# ✅ Отлично - вопросы высокого качества и их можно использовать напрямую.
# 
# ✅ Результаты оценки сохранены в файле ./evaluation_results/llm_judge_results.json.

