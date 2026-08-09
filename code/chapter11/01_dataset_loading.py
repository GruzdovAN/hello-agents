"""
Пример 1. Загрузка и форматирование набора данных
Демонстрирует, как использовать RLTrainingTool для загрузки и просмотра наборов данных GSM8K.
"""

import sys
from pathlib import Path
import json

# Добавить путь к проекту
project_root = Path(__file__).parent.parent / "HelloAgents"
sys.path.insert(0, str(project_root))

from hello_agents.tools import RLTrainingTool


# ============================================================================
# Пример 1. Загрузка набора данных формата SFT.
# ============================================================================

def load_sft_dataset():
    """
    Загрузите набор данных GSM8K в формате SFT с помощью RLTrainingTool.

    Формат данных SFT:
    {
        "prompt": "Вопрос: ...\n\nДавайте решим это шаг за шагом:\n",
        "completion": "Шаг 1: ...\nОкончательный ответ: 42",
        "text": "Вопрос: ...\n\nДавайте решим это шаг за шагом:\nШаг 1: ...\nОкончательный ответ: 42"
    }
    """
    tool = RLTrainingTool()

    config = {
        "action": "load_dataset",
        "format": "sft",
        "split": "train",
        "max_samples": 5
    }

    print("Загрузить набор данных формата SFT...")
    result = tool.run(config)
    result_dict = json.loads(result)

    print(f"✅ Размер набора данных: {result_dict['dataset_size']}")
    print(f"📋 Столбец набора данных: {result_dict['sample_keys']}")
    print(f"\n💡 Совет: набор данных загружен и его можно использовать для обучения.")
    print(f"   Используйте action='train', чтобы начать тренировку.")

    return result_dict


# ============================================================================
# Пример 2. Загрузка набора данных формата RL
# ============================================================================

def load_rl_dataset():
    """
    Загрузите набор данных GSM8K в формате RL с помощью RLTrainingTool.

    Формат данных RL:
    {
        "prompt": "<|im_start|>пользователь\nВопрос: ...\n<|im_end|>\n<|im_start|>ассистент\n",
        "ground_truth": "42",
        "вопрос": "...",
        "full_answer": "..."
    }
    """
    tool = RLTrainingTool()

    config = {
        "action": "load_dataset",
        "format": "rl",
        "split": "train",
        "max_samples": 5,
        "model_name": "Qwen/Qwen3-0.6B"
    }

    print("Загрузка набора данных формата RL...")
    result = tool.run(config)
    result_dict = json.loads(result)

    print(f"✅ Размер набора данных: {result_dict['dataset_size']}")
    print(f"📋 Столбец набора данных: {result_dict['sample_keys']}")
    print(f"\n💡 Совет: набор данных RL загружен, включая Prompt и ground_truth.")
    print(f"   Может использоваться для обучения GRPO.")

    return result_dict


# ============================================================================
# Пример 3. Загрузка наборов данных с разными разбиениями
# ============================================================================

def load_different_splits():
    """
    Загрузка обучающего набора и тестового набора
    """
    tool = RLTrainingTool()
    
    # Загрузка обучающего набора
    train_config = {
        "action": "load_dataset",
        "format": "sft",
        "split": "train",
        "max_samples": 100
    }
    
    print("Загрузить тренировочный набор...")
    train_result = tool.run(train_config)
    train_data = json.loads(train_result)
    print(f"✅ Обучающий набор: образцы {train_data['dataset_size']}")
    
    # Загрузить тестовый набор
    test_config = {
        "action": "load_dataset",
        "format": "sft",
        "split": "test",
        "max_samples": 50
    }
    
    print("\nЗагрузить набор тестов...")
    test_result = tool.run(test_config)
    test_data = json.loads(test_result)
    print(f"✅ Тестовый набор: образец {test_data['dataset_size']}")
    
    return train_data, test_data


# ============================================================================
# Пример 4. Загрузите полный набор данных
# ============================================================================

def load_full_dataset():
    """
    Загрузить полный набор данных (max_samples=None)
    
    Набор данных GSM8K:
    - Обучающий набор: ~7500 образцов.
    - Тестовый набор: ~1300 образцов
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "load_dataset",
        "format": "sft",
        "split": "train",
        "max_samples": None  # Нет = использовать все данные
    }
    
    print("Загрузка полного обучающего набора...")
    print("⚠️ Это может занять некоторое время...")
    
    # Раскомментируйте при фактической загрузке
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f" ✅ Полный обучающий набор: {result_dict['dataset_size']} образец")
    
    print("💡 Совет: установите max_samples=None, чтобы загрузить все данные.")
    print("   Обучающий набор GSM8K содержит около 7500 выборок.")
    
    return config


# ============================================================================
# Пример 5: Сравнение форматов SFT и RL
# ============================================================================

def compare_sft_rl_formats():
    """
    Сравните различия между форматами данных SFT и RL.
    """
    tool = RLTrainingTool()

    print("="*80)
    print("Сравнение форматов данных SFT и RL")
    print("="*80)

    # Формат SFT
    sft_config = {
        "action": "load_dataset",
        "format": "sft",
        "split": "train",
        "max_samples": 1
    }

    print("\n1. Формат SFT:")
    sft_result = tool.run(sft_config)
    sft_data = json.loads(sft_result)
    print(f"   Столбец: {sft_data['sample_keys']}")
    print(f"   Цель: Контролируемая точная настройка")
    print(f"   Особенности: Содержит полную подсказку и завершение.")

    # формат RL
    rl_config = {
        "action": "load_dataset",
        "format": "rl",
        "split": "train",
        "max_samples": 1,
        "model_name": "Qwen/Qwen3-0.6B"
    }

    print("\n2. Формат РЛ:")
    rl_result = tool.run(rl_config)
    rl_data = json.loads(rl_result)
    print(f"   Столбец: {rl_data['sample_keys']}")
    print(f"   Цель: обучение с подкреплением")
    print(f"   Особенности: Содержит подсказку и ground_truth для расчета вознаграждения.")

    print("\nОсновные отличия:")
    print("  - SFT: узнайте правильные ответы напрямую")
    print("  - RL: обучение через сигналы вознаграждения, более гибкое")

    return sft_data, rl_data


# ============================================================================
# Пример 6: Статистика набора данных
# ============================================================================

def dataset_statistics():
    """
    Просмотр статистики для набора данных
    """
    tool = RLTrainingTool()

    config = {
        "action": "load_dataset",
        "format": "sft",
        "split": "train",
        "max_samples": 100
    }

    print("Загрузка набора данных...")
    result = tool.run(config)
    result_dict = json.loads(result)

    print("\nСтатистика набора данных:")
    print(f"  Общее количество образцов: {result_dict['dataset_size']}")
    print(f"  Столбец данных: {', '.join(result_dict['sample_keys'])}")
    print(f"  Набор данных: GSM8K (Математика для начальной школы 8K)")
    print(f"  Тип задания: Математическое рассуждение")

    print(f"\n💡 Совет: набор данных содержит следующие поля:")
    for key in result_dict['sample_keys']:
        print(f"  - {key}")

    return result_dict


# ============================================================================
# основная функция
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("Пример 1. Загрузка набора данных формата SFT.")
    print("="*80)
    load_sft_dataset()
    
    print("\n" + "="*80)
    print("Пример 2. Загрузка набора данных формата RL")
    print("="*80)
    load_rl_dataset()
    
    print("\n" + "="*80)
    print("Пример 3. Загрузка наборов данных с разными разбиениями")
    print("="*80)
    load_different_splits()
    
    print("\n" + "="*80)
    print("Пример 4. Загрузите полный набор данных")
    print("="*80)
    load_full_dataset()
    
    print("\n" + "="*80)
    print("Пример 5: Сравнение форматов SFT и RL")
    print("="*80)
    compare_sft_rl_formats()
    
    print("\n" + "="*80)
    print("Пример 6: Статистика набора данных")
    print("="*80)
    dataset_statistics()

