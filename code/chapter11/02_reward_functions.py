"""
Пример 2: Разработка и использование функции вознаграждения
Демонстрирует, как использовать RLTrainingTool для создания и тестирования функций вознаграждения.
"""

import sys
from pathlib import Path
import json

# Добавить путь к проекту
project_root = Path(__file__).parent.parent / "HelloAgents"
sys.path.insert(0, str(project_root))

from hello_agents.tools import RLTrainingTool


# ============================================================================
# Пример 1. Создание функции вознаграждения за точность
# ============================================================================

def create_accuracy_reward():
    """
    Создайте функцию вознаграждения за точность
    
    Правила вознаграждения:
    - Правильный ответ: 1,0.
    - Ошибка ответа: 0.0
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "create_reward",
        "reward_type": "accuracy"
    }
    
    print("Создайте функцию вознаграждения за точность...")
    result = tool.run(config)
    result_dict = json.loads(result)
    
    print(f"✅ Тип функции вознаграждения: {result_dict['reward_type']}")
    print(f"📋 Описание: {result_dict['description']}")
    
    return result_dict


# ============================================================================
# Пример 2. Создание функции вознаграждения за штраф за длину
# ============================================================================

def create_length_penalty_reward():
    """
    Создайте функцию вознаграждения за штраф за длину
    
    Правила вознаграждения:
    - Базовая награда (точность)
    - минус штраф за длину (поощряет краткость)
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "create_reward",
        "reward_type": "length_penalty",
        "penalty_weight": 0.001,  # Штраф 0,001 за токен
        "max_length": 512
    }
    
    print("Создайте функцию вознаграждения за штраф за длину...")
    result = tool.run(config)
    result_dict = json.loads(result)
    
    print(f"✅ Тип функции вознаграждения: {result_dict['reward_type']}")
    print(f"📋 Вес штрафа: {result_dict.get('penalty_weight', 0.001)}")
    print(f"📋 Максимальная длина: {result_dict.get('max_length', 512)}")
    
    return result_dict


# ============================================================================
# Пример 3: Создание функции вознаграждения за шаг
# ============================================================================

def create_step_reward():
    """
    Создать функцию вознаграждения за шаг
    
    Правила вознаграждения:
    - Базовая награда (точность)
    - Добавьте награды за шаги (поощряйте детальное рассуждение)
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "create_reward",
        "reward_type": "step",
        "step_bonus": 0.1,  # Дополнительная награда 0,1 за каждый шаг
        "max_steps": 10
    }
    
    print("Создать функцию вознаграждения за шаг...")
    result = tool.run(config)
    result_dict = json.loads(result)
    
    print(f"✅ Тип функции вознаграждения: {result_dict['reward_type']}")
    print(f"📋 Награда за шаг: {result_dict.get('step_bonus', 0.1)}")
    print(f"📋 Максимальное количество шагов: {result_dict.get('max_steps', 10)}")
    
    return result_dict


# ============================================================================
# Пример 4: Тестирование функции вознаграждения
# ============================================================================

def test_reward_function():
    """
    Расчет функций вознаграждения за тест
    
    Протестируйте напрямую, используя MathRewardFunction.
    """
    from hello_agents.rl import MathRewardFunction
    
    reward_fn = MathRewardFunction(tolerance=1e-4)
    
    # тестовый образец
    test_cases = [
        {
            "completion": "Let me calculate: 2+2=4. Final Answer: 4",
            "ground_truth": "4",
            "expected": 1.0
        },
        {
            "completion": "I think 2+2=5. Final Answer: 5",
            "ground_truth": "4",
            "expected": 0.0
        },
        {
            "completion": "The answer is 4",
            "ground_truth": "4",
            "expected": 1.0
        },
        {
            "completion": "2+2 equals four. #### 4",
            "ground_truth": "4",
            "expected": 1.0
        }
    ]
    
    print("Тестовая функция вознаграждения:")
    print("-" * 80)
    
    for i, case in enumerate(test_cases, 1):
        # Рассчитать вознаграждение
        rewards = reward_fn(
            completions=[case["completion"]],
            ground_truth=[case["ground_truth"]]
        )
        reward = rewards[0]
        
        print(f"\nТест {i}:")
        print(f"  Генерирует: {case['completion'][:50]}...")
        print(f"  Истинное значение: {case['ground_truth']}")
        print(f"  Награда: {reward:.2f} (Ожидание: {case['expected']:.2f})")
        print(f"  {'Правильно', если абс(вознаграждение - случай['ожидаемый']) < 0,01, иначе '❌ Ошибка'}")
    
    return test_cases


# ============================================================================
# Пример 5: Тест извлечения ответов
# ============================================================================

def test_answer_extraction():
    """
    Функция извлечения тестового ответа
    """
    from hello_agents.rl import MathRewardFunction
    
    reward_fn = MathRewardFunction()
    
    test_texts = [
        "Final Answer: 42",
        "The answer is 3.14",
        "#### 100",
        "So the result is 2.5",
        "Let me think... the answer should be 7",
        "42"
    ]
    
    print("Тест на извлечение ответов:")
    print("-" * 80)
    
    for text in test_texts:
        answer = reward_fn.extract_answer(text)
        print(f"\nТекст: {текст}")
        print(f"Извлечение: {ответ, если ответ еще '(не найден)'}")
    
    return test_texts


# ============================================================================
# Пример 6: Тест сравнения ответов
# ============================================================================

def test_answer_comparison():
    """
    Функция сравнения ответов на тесты
    """
    from hello_agents.rl import MathRewardFunction
    
    reward_fn = MathRewardFunction(tolerance=0.01)
    
    test_pairs = [
        ("42", "42", True),
        ("3.14", "3.14159", False),  # вне толерантности
        ("3.14", "3.141", True),     # в пределах допуска
        ("100", "100.0", True),
        ("2.5", "3.0", False),
        ("7", "7.00", True)
    ]
    
    print("Сравнительный тест ответов:")
    print("-" * 80)
    
    for pred, truth, expected in test_pairs:
        is_correct = reward_fn.compare_answers(pred, truth)
        print(f"\nПрогноз: {pred}, истина: {truth}")
        print(f"Результат: {'правильно', если ожидается, иначе 'ошибка'} (Ожидание: {'правильно', если ожидается, иначе 'ошибка'})")
        print(f"{' ✅ пройдено', если is_correct == ожидается, иначе '❌ не удалось'}")
    
    return test_pairs


# ============================================================================
# Пример 7: Сравнение различных функций вознаграждения
# ============================================================================

def compare_reward_functions():
    """
    Сравните эффекты различных функций вознаграждения
    """
    from hello_agents.rl import (
        create_accuracy_reward,
        create_length_penalty_reward,
        create_step_reward
    )

    # Создавайте различные функции вознаграждения
    accuracy_fn = create_accuracy_reward()
    base_fn = create_accuracy_reward()  # Базовая функция вознаграждения
    length_fn = create_length_penalty_reward(base_fn, penalty_weight=0.001)
    step_fn = create_step_reward(base_fn, step_bonus=0.1)
    
    # тестовый образец
    test_cases = [
        {
            "completion": "4",
            "ground_truth": "4",
            "desc": "краткий правильный ответ"
        },
        {
            "completion": "Step 1: 2+2=4\nFinal Answer: 4",
            "ground_truth": "4",
            "desc": "Правильный ответ с указанием шагов"
        },
        {
            "completion": "Let me think... " * 20 + "Final Answer: 4",
            "ground_truth": "4",
            "desc": "длинный правильный ответ"
        }
    ]
    
    print("Сравнение функции вознаграждения:")
    print("=" * 80)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nТест {i}: {case['desc']}")
        print(f"Длина: {len(case['completion'])} символов")
        
        # Рассчитать различные вознаграждения
        acc_reward = accuracy_fn([case["completion"]], ground_truth=[case["ground_truth"]])[0]
        len_reward = length_fn([case["completion"]], ground_truth=[case["ground_truth"]])[0]
        step_reward = step_fn([case["completion"]], ground_truth=[case["ground_truth"]])[0]
        
        print(f"  Награда за точность: {acc_reward:.4f}")
        print(f"  Награда за штраф за длину: {len_reward:.4f}")
        print(f"  Награда за шаг: {step_reward:.4f}")
    
    print("\nВывод:")
    print("  - Бонус за точность: сосредоточьтесь только на правильности ответа.")
    print("  - Штраф за длину: поощряйте краткие ответы.")
    print("  - Награды за этапы: поощряйте детальное рассуждение.")
    
    return test_cases


# ============================================================================
# основная функция
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("Пример 1. Создание функции вознаграждения за точность")
    print("="*80)
    create_accuracy_reward()
    
    print("\n" + "="*80)
    print("Пример 2. Создание функции вознаграждения за штраф за длину")
    print("="*80)
    create_length_penalty_reward()
    
    print("\n" + "="*80)
    print("Пример 3: Создание функции вознаграждения за шаг")
    print("="*80)
    create_step_reward()
    
    print("\n" + "="*80)
    print("Пример 4: Тестирование функции вознаграждения")
    print("="*80)
    test_reward_function()
    
    print("\n" + "="*80)
    print("Пример 5: Тест извлечения ответов")
    print("="*80)
    test_answer_extraction()
    
    print("\n" + "="*80)
    print("Пример 6: Тест сравнения ответов")
    print("="*80)
    test_answer_comparison()
    
    print("\n" + "="*80)
    print("Пример 7: Сравнение различных функций вознаграждения")
    print("="*80)
    compare_reward_functions()

