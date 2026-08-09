"""
Пример 7: Оценка модели

Демонстрирует, как использовать RLTrainingTool для оценки обученной модели.
"""

import sys
from pathlib import Path
import json

# Добавить путь к проекту
project_root = Path(__file__).parent.parent / "HelloAgents"
sys.path.insert(0, str(project_root))

from hello_agents.tools import RLTrainingTool


# ============================================================================
# Пример 1: Оценка модели SFT
# ============================================================================

def evaluate_sft_model():
    """
    Оцените обученную модель SFT
    
    Оцените точность модели с помощью тестового набора
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "evaluate",
        "model_path": "./output/quick_test/sft",
        "max_samples": 50  # Используйте 50 тестовых образцов
    }
    
    print("Оцените модель SFT:")
    print(f"  Путь к модели: {config['model_path']}")
    print(f"  Количество тестовых образцов: {config['max_samples']}")
    
    # Раскомментируйте при фактической оценке
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n✅ Оценка завершена!")
    # print(f" точность: {result_dict['accuracy']}")
    # print(f" Среднее вознаграждение: {result_dict['average_reward']}")
    
    print("\n💡 Совет: раскомментируйте, чтобы запустить оценку.")
    
    return config


# ============================================================================
# Пример 2: Оценка модели GRPO
# ============================================================================

def evaluate_grpo_model():
    """
    Оцените модель после обучения GRPO
    
    Сравните производительность модели GRPO и модели SFT.
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "evaluate",
        "model_path": "./output/quick_test/grpo",
        "max_samples": 50
    }
    
    print("Оцените модель GRPO:")
    print(f"  Путь к модели: {config['model_path']}")
    print(f"  Количество тестовых образцов: {config['max_samples']}")
    
    # Раскомментируйте при фактической оценке
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n✅ Оценка завершена!")
    # print(f" точность: {result_dict['accuracy']}")
    # print(f" Среднее вознаграждение: {result_dict['average_reward']}")
    
    print("\n💡 Совет: раскомментируйте, чтобы запустить оценку.")
    
    return config


# ============================================================================
# Пример 3: Сравнение моделей SFT и GRPO
# ============================================================================

def compare_sft_grpo():
    """
    Сравнение производительности моделей SFT и GRPO
    
    Оцените обе модели на одном тестовом наборе.
    """
    tool = RLTrainingTool()
    
    print("="*80)
    print("Сравнение моделей SFT и GRPO")
    print("="*80)
    
    # Оценка моделей SFT
    print("\n1. Оценить модель SFT...")
    sft_config = {
        "action": "evaluate",
        "model_path": "./output/quick_test/sft",
        "max_samples": 100
    }
    
    # Раскомментируйте при фактической оценке
    # sft_result = tool.run(sft_config)
    # sft_data = json.loads(sft_result)
    # print(f" Точность SFT: {sft_data['accuracy']}")
    
    # Оцените модель GRPO
    print("\n2. Оцените модель GRPO...")
    grpo_config = {
        "action": "evaluate",
        "model_path": "./output/quick_test/grpo",
        "max_samples": 100
    }
    
    # Раскомментируйте при фактической оценке
    # grpo_result = tool.run(grpo_config)
    # grpo_data = json.loads(grpo_result)
    # print(f" Точность GRPO: {grpo_data['accuracy']}")
    
    # Сравнить результаты
    print("\nРезультаты сравнения:")
    print("  Модель SFT: изучение основных форматов и шагов вывода")
    print("  Модель GRPO: оптимизация возможностей рассуждения посредством обучения с подкреплением")
    print("  Ожидается: точность модели GRPO > точность модели SFT.")
    
    print("\n💡 Совет: раскомментируйте, чтобы запустить фактическую оценку.")
    
    return sft_config, grpo_config


# ============================================================================
# Пример 4: Оценка базовой модели
# ============================================================================

def evaluate_baseline():
    """
    Оцените базовую модель (исходную необученную модель)
    
    Используется для сравнения эффектов тренировок.
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "evaluate",
        "model_path": "Qwen/Qwen3-0.6B",  # оригинальная модель
        "max_samples": 50
    }
    
    print("Оцените базовую модель:")
    print(f"  Модель: {config['model_path']}")
    print(f"  Количество тестовых образцов: {config['max_samples']}")
    
    # Раскомментируйте при фактической оценке
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n✅ Оценка завершена!")
    # print(f"Базовая точность: {result_dict['accuracy']}")
    
    print("\n💡 Совет: базовые модели обычно имеют меньшую точность.")
    print("   Обученная модель должна значительно превосходить базовую.")
    
    return config


# ============================================================================
# Пример 5: Полный процесс оценки
# ============================================================================

def complete_evaluation():
    """
    Полный процесс оценки
    
    Оцените три модели: базовую, SFT и GRPO.
    """
    tool = RLTrainingTool()
    
    models = {
        "базовая модель": "Qwen/Qwen3-0.6B",
        "Модель SFT": "./output/quick_test/sft",
        "Модель ГРПО": "./output/quick_test/grpo"
    }
    
    print("="*80)
    print("Полный процесс оценки")
    print("="*80)
    
    results = {}
    
    for name, model_path in models.items():
        print(f"\nОценить {имя}...")
        print(f"  Путь: {model_path}")
        
        config = {
            "action": "evaluate",
            "model_path": model_path,
            "max_samples": 100
        }
        
        # Раскомментируйте при фактической оценке
        # result = tool.run(config)
        # result_dict = json.loads(result)
        # results[name] = result_dict
        # print(f" точность: {result_dict['accuracy']}")
    
    print("\n" + "="*80)
    print("Резюме оценки")
    print("="*80)
    
    # Раскомментируйте при фактической оценке
    # for name, result in results.items():
    #     print(f"{name}: {result['accuracy']}")
    
    print("\nОжидаемые результаты:")
    print("  Базовая модель < модель SFT < модель GRPO")
    print("  Это показывает, что обучение с подкреплением эффективно повышает производительность модели.")
    
    print("\n💡 Совет: раскомментируйте, чтобы запустить полную оценку.")
    
    return models


# ============================================================================
# Пример 6: Пример практической оценки
# ============================================================================

def practical_evaluation():
    """
    Пример практической оценки – готовность к работе
    
    Оцените модель, обученную с помощью fast_test
    """
    tool = RLTrainingTool()
    
    print("="*80)
    print("Примеры практической оценки")
    print("="*80)
    
    # Проверьте, существует ли модель
    import os
    sft_path = "./output/quick_test/sft"
    grpo_path = "./output/quick_test/grpo"
    
    if not os.path.exists(sft_path):
        print(f"\n❌ Модель SFT не существует: {sft_path}")
        print("   Пожалуйста, сначала запустите 00_quick_test.py, чтобы обучить модель.")
        return None
    
    if not os.path.exists(grpo_path):
        print(f"\n❌Модель GRPO не существует: {grpo_path}")
        print("   Пожалуйста, сначала запустите 00_quick_test.py, чтобы обучить модель.")
        return None
    
    print("\n✅ Файл модели существует, начните оценку...")
    
    # Оценка моделей SFT
    print("\n1. Оценить модель SFT...")
    sft_config = {
        "action": "evaluate",
        "model_path": sft_path,
        "max_samples": 20  # Быстрое тестирование с использованием меньшего количества образцов
    }
    
    print("💡 Совет: раскомментируйте ниже, чтобы начать оценку.")
    print("# sft_result = tool.run(sft_config)")
    print("# sft_data = json.loads(sft_result)")
    print("# print(f'SFT точность: {sft_data[\"accuracy\"]}')")
    
    # Оцените модель GRPO
    print("\n2. Оцените модель GRPO...")
    grpo_config = {
        "action": "evaluate",
        "model_path": grpo_path,
        "max_samples": 20
    }
    
    print("💡 Совет: раскомментируйте ниже, чтобы начать оценку.")
    print("# grpo_result = tool.run(grpo_config)")
    print("# grpo_data = json.loads(grpo_result)")
    print("# print(f'Точность GRPO: {grpo_data[\"accuracy\"]}')")
    
    # Раскомментируйте при фактической оценке
    # sft_result = tool.run(sft_config)
    # sft_data = json.loads(sft_result)
    # print(f"\n ✅ Оценка SFT завершена: {sft_data['accuracy']}")
    
    # grpo_result = tool.run(grpo_config)
    # grpo_data = json.loads(grpo_result)
    # print(f" ✅ Оценка GRPO завершена: {grpo_data['accuracy']}")
    
    return sft_config, grpo_config


# ============================================================================
# основная функция
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("Пример 1: Оценка модели SFT")
    print("="*80)
    evaluate_sft_model()
    
    print("\n" + "="*80)
    print("Пример 2: Оценка модели GRPO")
    print("="*80)
    evaluate_grpo_model()
    
    print("\n" + "="*80)
    print("Пример 3: Сравнение моделей SFT и GRPO")
    print("="*80)
    compare_sft_grpo()
    
    print("\n" + "="*80)
    print("Пример 4: Оценка базовой модели")
    print("="*80)
    evaluate_baseline()
    
    print("\n" + "="*80)
    print("Пример 5: Полный процесс оценки")
    print("="*80)
    complete_evaluation()
    
    print("\n" + "="*80)
    print("Пример 6: Пример практической оценки")
    print("="*80)
    practical_evaluation()

