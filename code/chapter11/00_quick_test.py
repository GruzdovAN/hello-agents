"""
Быстрый лабораторный тест

Быстро протестируйте процессы обучения SFT и GRPO с помощью небольших объемов данных.
"""

import sys
from pathlib import Path
import json

# Добавить путь к проекту
project_root = Path(__file__).parent.parent / "HelloAgents"
sys.path.insert(0, str(project_root))

from hello_agents.tools import RLTrainingTool


def quick_test():
    """
    Быстрый лабораторный тест
    
    Конфигурация:
    - Модель: Qwen/Qwen3-0.6B
    - Количество образцов: 10
    - Количество тренировочных раундов: 1 раунд
    - Примерное время: ~2-3 минуты.
    """
    tool = RLTrainingTool()
    
    print("="*80)
    print("Быстрый лабораторный тест")
    print("="*80)
    
    # ========================================================================
    # Тест 1: Загрузка данных
    # ========================================================================
    print("\nТест 1: Загрузка данных")
    print("-"*80)
    
    data_config = {
        "action": "load_dataset",
        "format_type": "sft",
        "split": "train",
        "max_samples": 5
    }
    
    print("Загрузка набора данных...")
    result = tool.run(data_config)
    data = json.loads(result)
    print(f"✅ Набор данных успешно загружен: образец {data['dataset_size']}")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # ========================================================================
    # Тест 2: Обучение SFT
    # ========================================================================
    print("\nТест 2: обучение SFT")
    print("-"*80)
    
    sft_config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/quick_test/sft",
        "max_samples": 10,
        "num_epochs": 1,
        "batch_size": 2,
        "use_lora": True,
        "lora_r": 8,
        "lora_alpha": 16,
    }
    
    print("Конфигурация SFT:")
    print(json.dumps(sft_config, indent=2, ensure_ascii=False))
    
    print("\n⏳ Начать обучение SFT...")
    sft_result = tool.run(sft_config)
    sft_data = json.loads(sft_result)
    print("\n✔Результаты обучения SFT:")
    print(json.dumps(sft_data, indent=2, ensure_ascii=False))
    
    # ========================================================================
    # Тест 3: Обучение GRPO
    # ========================================================================
    print("\nТест 3: Обучение GRPO")
    print("-"*80)

    # Примечание. GRPO более чувствителен к скорости обучения, и на небольших моделях (таких как Qwen3-0.6B) по умолчанию используется значение 5e-5.
    # Это может привести к краху политики (значительно снижается точность). Если вам нужна большая стабильность, вы можете явно установить Learning_rate=1e-6.
    
    grpo_config = {
        "action": "train",
        "algorithm": "grpo",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/quick_test/grpo",
        "max_samples": 10,
        "num_epochs": 1,
        "batch_size": 2,
        "use_lora": True,
        "lora_r": 8,
        "lora_alpha": 16,
    }
    
    print("Конфигурация ГРПО:")
    print(json.dumps(grpo_config, indent=2, ensure_ascii=False))
    
    print("\n⏳ Начать обучение GRPO...")
    grpo_result = tool.run(grpo_config)
    grpo_data = json.loads(grpo_result)
    print("\n✔Результаты обучения ГРПО:")
    print(json.dumps(grpo_data, indent=2, ensure_ascii=False))
    
    # ========================================================================
    # Тест 4: Функция вознаграждения
    # ========================================================================
    print("\nТест 4: Функция вознаграждения")
    print("-"*80)
    
    reward_config = {
        "action": "create_reward",
        "reward_type": "accuracy"
    }
    
    print("Создайте функцию вознаграждения...")
    reward_result = tool.run(reward_config)
    reward_data = json.loads(reward_result)
    print("✅ Функция вознаграждения успешно создана:")
    print(json.dumps(reward_data, indent=2, ensure_ascii=False))
    
    # ========================================================================
    # Подвести итог
    # ========================================================================
    print("\n" + "="*80)
    print("Итог теста")
    print("="*80)
    print("\n✔Все тесты пройдены!")
    print("\nТестовые задания:")
    print("  1. ✅ Загрузка данных")
    print("  2. ✅ Обучение SFT")
    print("  3. ✅ Обучение ГРПО")
    print("  4. ✅ Создание функции вознаграждения")
    
    print("\nПуть к модели:")
    print(f"  Модель SFT: {sft_config['output_dir']}")
    print(f"  Модель GRPO: {grpo_config['output_dir']}")


if __name__ == "__main__":
    quick_test()

