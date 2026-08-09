"""
Пример 5: Полный процесс обучения GRPO

Демонстрирует, как использовать RLTrainingTool для обучения с подкреплением GRPO.
"""

import sys
from pathlib import Path
import json

# Добавить путь к проекту
project_root = Path(__file__).parent.parent / "HelloAgents"
sys.path.insert(0, str(project_root))

from hello_agents.tools import RLTrainingTool


# ============================================================================
# Пример 1: Простейшее обучение GRPO
# ============================================================================

def minimal_grpo_training():
    """
    Простейший пример обучения GRPO
    
    Просто позвоните в RLTrainingTool
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "grpo",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/grpo_minimal",
        "max_samples": 10,
        "num_epochs": 1,
    }
    
    print("Простейшее обучение ГРПО:")
    print(f"  Модель: {config['model_name']}")
    print(f"  Количество образцов: {config['max_samples']}")
    print(f"  Количество эпох обучения: {config['num_epochs']}")
    
    # Раскомментируйте во время фактического обучения
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n© Обучение завершено! Модель сохранена в папке: {result_dict['output_dir']}")
    
    return config


# ============================================================================
# Пример 2. Стандартная конфигурация обучения GRPO
# ============================================================================

def standard_grpo_training():
    """
    Стандартная конфигурация обучения GRPO
    
    Обучение GRPO обычно проводится на основе модели SFT.
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "grpo",
        
        # Конфигурация модели — вы можете использовать обученную модель SFT.
        "model_name": "Qwen/Qwen3-0.6B",  # или "./output/sft_standard"
        "output_dir": "./output/grpo_standard",
        
        # Конфигурация данных
        "max_samples": 500,  # GRPO обычно использует меньше образцов.
        
        # конфигурация обучения
        "num_epochs": 3,
        "batch_size": 2,  # GRPO требует больше видеопамяти
        "learning_rate": 1e-5,  # В 10 раз меньше, чем SFT; примечание: 5e-5 может привести к краху стратегии на небольших моделях, при необходимости скорректируйте до 1e-6.
        
        # Конфигурация ЛоРА
        "use_lora": True,
        "lora_r": 16,
        "lora_alpha": 32,
    }
    
    print("Стандартная конфигурация обучения GRPO:")
    print(f"  Модель: {config['model_name']}")
    print(f"  Количество образцов: {config['max_samples']}")
    print(f"  Количество эпох обучения: {config['num_epochs']}")
    print(f"  batch_size: {config['batch_size']}")
    print(f"  Learning_rate: {config['learning_rate']} (меньше, чем SFT)")
    
    # Раскомментируйте во время фактического обучения
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n© Обучение GRPO завершено!")
    
    return config


# ============================================================================
# Пример 3: Обучение полному набору данных
# ============================================================================

def full_dataset_training():
    """
    Обучение GRPO с использованием полного набора данных
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "grpo",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/grpo_full",
        
        # Использовать все данные
        "max_samples": None,  # Нет = использовать все данные
        
        "num_epochs": 3,
        "batch_size": 2,
        "learning_rate": 1e-5,
        "use_lora": True,
        "lora_r": 16,
        "lora_alpha": 32,
    }
    
    print("Полное обучение GRPO по наборам данных:")
    print(f"  Модель: {config['model_name']}")
    print(f"  Количество образцов: Все (max_samples=Нет)")
    print(f"  Количество эпох обучения: {config['num_epochs']}")
    print(f"  Примерное количество образцов: ~7500 (обучающий набор GSM8K)")
    
    # Раскомментируйте во время фактического обучения
    # result = tool.run(config)
    
    return config


# ============================================================================
# Пример 4: Полный процесс SFT + GRPO
# ============================================================================

def complete_sft_grpo_pipeline():
    """
    Полный процесс обучения SFT + GRPO
    
    Шаги:
    1. Обучение SFT – изучите базовый формат
    2. Обучение GRPO – оптимизация способностей к рассуждению.
    """
    tool = RLTrainingTool()
    
    # Шаг 1: Обучение SFT
    print("Шаг 1: Обучение SFT")
    sft_config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/pipeline_sft",
        "max_samples": 1000,
        "num_epochs": 3,
        "batch_size": 4,
        "use_lora": True,
    }
    
    print(f"  Модель: {sft_config['model_name']}")
    print(f"  Количество образцов: {sft_config['max_samples']}")
    
    # Раскомментируйте во время фактического обучения
    # sft_result = tool.run(sft_config)
    # print(f"Обучение SFT завершено: {sft_config['output_dir']}")
    
    # Шаг 2: Обучение GRPO
    print("\nШаг 2: Обучение GRPO")
    grpo_config = {
        "action": "train",
        "algorithm": "grpo",
        "model_name": "./output/pipeline_sft",  # Использовать модель SFT
        "output_dir": "./output/pipeline_grpo",
        "max_samples": 500,
        "num_epochs": 3,
        "batch_size": 2,
        "learning_rate": 1e-5,
        "use_lora": True,
    }
    
    print(f"  Базовая модель: {grpo_config['model_name']}")
    print(f"  Количество образцов: {grpo_config['max_samples']}")
    
    # Раскомментируйте во время фактического обучения
    # grpo_result = tool.run(grpo_config)
    # print(f" ✅ Обучение GRPO завершено: {grpo_config['output_dir']}")
    
    print("\n💡 Для вывода рекомендуется использовать модель GRPO.")
    
    return sft_config, grpo_config


# ============================================================================
# Пример 5: Использование различных функций вознаграждения
# ============================================================================

def using_different_rewards():
    """
    GRPO по умолчанию использует функцию вознаграждения за точность.
    
    Поведение можно изменить, создав собственную функцию вознаграждения.
    """
    print("Функция вознаграждения GRPO:")
    print("\nФункция вознаграждения по умолчанию: награда за точность")
    print("  - Правильный ответ: 1,0.")
    print("  - Ошибка ответа: 0.0")
    
    print("\nДругие доступные функции вознаграждения:")
    print("  1. Бонус за длину: поощряйте краткие ответы.")
    print("  2. Награды за этапы: поощряйте детальное рассуждение.")
    print("  3. Индивидуальные награды: настраиваются в соответствии с потребностями.")
    
    print("\nПример создания функции вознаграждения:")
    tool = RLTrainingTool()
    
    # Создайте функцию вознаграждения за точность
    accuracy_config = {
        "action": "create_reward",
        "reward_type": "accuracy"
    }
    print("\n1. Бонус к точности:")
    print(f"   Конфигурация: {accuracy_config}")
    
    # Создайте функцию вознаграждения за штраф за длину
    length_config = {
        "action": "create_reward",
        "reward_type": "length_penalty",
        "penalty_weight": 0.001
    }
    print("\n2. Награда за штраф за длину:")
    print(f"   Конфигурация: {length_config}")
    
    # Создать функцию вознаграждения за шаг
    step_config = {
        "action": "create_reward",
        "reward_type": "step",
        "step_bonus": 0.1
    }
    print("\n3. Награды за этапы:")
    print(f"   Конфигурация: {step_config}")
    
    return accuracy_config, length_config, step_config


# ============================================================================
# Пример 6: Фактический пример обучения
# ============================================================================

def practical_training_example():
    """
    Фактический пример обучения — можно запустить напрямую
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "grpo",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/grpo_practical",
        
        # Быстрое тестирование с использованием меньшего количества образцов
        "max_samples": 50,
        "num_epochs": 1,
        "batch_size": 2,
        "learning_rate": 1e-5,
        
        # Использование ЛоРА
        "use_lora": True,
        "lora_r": 16,
        "lora_alpha": 32,
    }
    
    print("Пример практического обучения:")
    print(f"  Модель: {config['model_name']}")
    print(f"  Количество образцов: {config['max_samples']}")
    print(f"  Количество эпох обучения: {config['num_epochs']}")
    print(f"  Выходной каталог: {config['output_dir']}")
    
    print("\n💡 Совет: раскомментируйте ниже, чтобы начать обучение.")
    print("# result = tool.run(config)")
    print("# result_dict = json.loads(result)")
    print("# print(f' ✅ Обучение завершено! Модель сохранена в: {result_dict[\"output_dir\"]}')")
    
    # Раскомментируйте во время фактического обучения
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n© Обучение завершено!")
    # print(f"📁 Модель сохранена в: {result_dict['output_dir']}")
    
    return config


# ============================================================================
# основная функция
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("Пример 1: Простейшее обучение GRPO")
    print("="*80)
    minimal_grpo_training()
    
    print("\n" + "="*80)
    print("Пример 2. Стандартная конфигурация обучения GRPO")
    print("="*80)
    standard_grpo_training()
    
    print("\n" + "="*80)
    print("Пример 3: Обучение полному набору данных")
    print("="*80)
    full_dataset_training()
    
    print("\n" + "="*80)
    print("Пример 4: Полный процесс SFT + GRPO")
    print("="*80)
    complete_sft_grpo_pipeline()
    
    print("\n" + "="*80)
    print("Пример 5: Использование различных функций вознаграждения")
    print("="*80)
    using_different_rewards()
    
    print("\n" + "="*80)
    print("Пример 6: Фактический пример обучения")
    print("="*80)
    practical_training_example()

