"""
Пример 3: Конфигурация и использование LoRA
Продемонстрируйте, как настроить и использовать LoRA для эффективной точной настройки параметров с помощью RLTrainingTool.
"""

import sys
from pathlib import Path
import json

# Добавить путь к проекту
project_root = Path(__file__).parent.parent / "HelloAgents"
sys.path.insert(0, str(project_root))

from hello_agents.tools import RLTrainingTool


# ============================================================================
# Пример 1. Базовая конфигурация LoRA
# ============================================================================

def basic_lora_config():
    """
    Самая базовая конфигурация LoRA
    
    LoRA (Адаптация низкого ранга):
    - Тренируйте только несколько дополнительных параметров
    - Уменьшить использование видеопамяти на 60-80%
    - Увеличить скорость обучения в 2-3 раза
    - Файл модели весит всего ~10 МБ.
    """
    tool = RLTrainingTool()
    
    # Обучение SFT с использованием RLTrainingTool, поддержка LoRA
    config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/lora_basic",
        "max_samples": 100,
        "num_epochs": 1,
        
        # Конфигурация ЛоРА
        "use_lora": True,           # Включить ЛоРА
        "lora_r": 16,               # ранг ЛоРА
        "lora_alpha": 32,           # Коэффициент масштабирования (обычно 2 раза в r)
    }
    
    print("Базовая конфигурация LoRA:")
    print(f"  Модель: {config['model_name']}")
    print(f"  use_lora: {config['use_lora']}")
    print(f"  lora_r: {config['lora_r']}")
    print(f"  lora_alpha: {config['lora_alpha']}")
    print(f"  Целевые модули: ['q_proj', 'v_proj'] (по умолчанию)")
    
    # Раскомментируйте во время фактического обучения
    # result = tool.run(config)
    # print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))
    
    return config


# ============================================================================
# Пример 2: Сравнение различных рангов LoRA
# ============================================================================

def compare_lora_ranks():
    """
    Сравните конфигурации разных рангов LoRA
    
    Выбор ранга LoRA(r):
    - r=8: небольшое количество параметров, подходит для быстрых экспериментов.
    - r=16: рекомендуемое значение, обеспечивающее баланс производительности и эффективности.
    - r=32: большее количество параметров, стремление к лучшей производительности.
    """
    configs = {
        "r=8 (быстрый эксперимент)": {
            "lora_r": 8,
            "lora_alpha": 16,
            "params": "~16K"
        },
        "r=16 (рекомендуется)": {
            "lora_r": 16,
            "lora_alpha": 32,
            "params": "~32K"
        },
        "r=32 (высокая производительность)": {
            "lora_r": 32,
            "lora_alpha": 64,
            "params": "~65K"
        },
    }
    
    print("Сравнение разных рангов LoRA:")
    for name, config in configs.items():
        print(f"\n{name}:")
        print(f"  lora_r: {config['lora_r']}")
        print(f"  lora_alpha: {config['lora_alpha']}")
        print(f"  Примерное количество параметров: {config['params']}")
    
    # Пример практического обучения
    print("\nОбучающий пример (r=16):")
    print("""
    tool = RLTrainingTool()
    result = tool.run({
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "max_samples": 100,
        "num_epochs": 1,
        "use_lora": True,
        "lora_r": 16,
        "lora_alpha": 32,
    })
    """)
    
    return configs


# ============================================================================
# Пример 3: сравнение LoRA и полной тонкой настройки
# ============================================================================

def compare_lora_vs_full_finetuning():
    """
    Сравнение LoRA и полностью настроенных конфигураций
    """
    print("Сравнение LoRA и полной тонкой настройки:")
    print("\nТонкая настройка LoRA:")
    print("  Использование видеопамяти: ~4 ГБ (модель 0,5Б)")
    print("  Скорость обучения: быстрая (2-3 раза)")
    print("  Размер модели: ~10 МБ")
    print("  batch_size: 8")
    print("  use_lora: True")
    
    print("\nПолная тонкая настройка:")
    print("  Использование видеопамяти: ~14 ГБ (модель 0,5Б)")
    print("  Скорость обучения: медленная")
    print("  Размер модели: ~ 1 ГБ")
    print("  batch_size: 2")
    print("  use_lora: False")
    
    print("\nРекомендуется: используйте LoRA для точной настройки.")


# ============================================================================
# Пример 4: Пример фактической конфигурации обучения
# ============================================================================

def practical_training_configs():
    """
    Рекомендуемая конфигурация для реального обучения
    """
    tool = RLTrainingTool()
    
    # Быстрая настройка обучения
    quick_config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/quick_test",
        "max_samples": 100,
        "num_epochs": 1,
        "batch_size": 8,
        "use_lora": True,
        "lora_r": 8,
        "lora_alpha": 16,
    }
    
    # Стандартная конфигурация обучения
    standard_config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/standard",
        "max_samples": 1000,
        "num_epochs": 3,
        "batch_size": 4,
        "use_lora": True,
        "lora_r": 16,
        "lora_alpha": 32,
        "learning_rate": 5e-5,
    }
    
    # Высококачественная конфигурация обучения
    high_quality_config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/high_quality",
        "max_samples": None,  # Использовать все данные
        "num_epochs": 5,
        "batch_size": 2,
        "use_lora": True,
        "lora_r": 32,
        "lora_alpha": 64,
        "learning_rate": 3e-5,
    }
    
    print("Фактический пример конфигурации обучения:")
    print("\n1. Быстрая экспериментальная конфигурация:")
    print(f"   Количество образцов: {quick_config['max_samples']}")
    print(f"   epochs: {quick_config['num_epochs']}")
    print(f"   lora_r: {quick_config['lora_r']}")
    print(f"   batch_size: {quick_config['batch_size']}")
    
    print("\n2. Стандартная конфигурация обучения:")
    print(f"   Количество образцов: {standard_config['max_samples']}")
    print(f"   epochs: {standard_config['num_epochs']}")
    print(f"   lora_r: {standard_config['lora_r']}")
    print(f"   batch_size: {standard_config['batch_size']}")
    
    print("\n3. Качественная конфигурация обучения:")
    print(f"   Количество образцов: Все (max_samples=Нет)")
    print(f"   epochs: {high_quality_config['num_epochs']}")
    print(f"   lora_r: {high_quality_config['lora_r']}")
    print(f"   batch_size: {high_quality_config['batch_size']}")
    
    # Раскомментируйте во время фактического обучения
    # result = tool.run(quick_config)
    # print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))
    
    return quick_config, standard_config, high_quality_config


# ============================================================================
# Пример 5: Рекомендации по настройке параметров LoRA
# ============================================================================

def lora_tuning_guidelines():
    """
    Рекомендации по настройке параметров LoRA
    """
    guidelines = {
        "lora_r (ранг)": {
            "Рекомендуемое значение": 16,
            "объем": "8-32",
            "иллюстрировать": "Чем больше значение, тем лучше производительность, но при этом увеличивается количество параметров и время обучения.",
            "Выберите предложения": {
                "Быстрый эксперимент": 8,
                "Сбалансированная производительность": 16,
                "стремление к производительности": 32,
            }
        },
        "lora_alpha (коэффициент масштабирования)": {
            "Рекомендуемое значение": 32,
            "объем": "16-64",
            "иллюстрировать": "Обычно устанавливается в 2 раза lora_r",
            "формула": "lora_alpha = 2 * lora_r"
        },
        "max_samples (количество образцов)": {
            "Быстрый эксперимент": 100,
            "Стандартное обучение": 1000,
            "Полное обучение": "Нет (все данные)",
            "иллюстрировать": "Нет означает использовать все данные",
        },
    }
    
    print("Рекомендации по настройке параметров LoRA:")
    for param, info in guidelines.items():
        print(f"\n{param}:")
        for key, value in info.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    - {k}: {v}")
            else:
                print(f"  {key}: {value}")
    
    return guidelines


# ============================================================================
# основная функция
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("Пример 1. Базовая конфигурация LoRA")
    print("="*80)
    basic_lora_config()
    
    print("\n" + "="*80)
    print("Пример 2: Сравнение различных рангов LoRA")
    print("="*80)
    compare_lora_ranks()
    
    print("\n" + "="*80)
    print("Пример 3: сравнение LoRA и полной тонкой настройки")
    print("="*80)
    compare_lora_vs_full_finetuning()
    
    print("\n" + "="*80)
    print("Пример 4: Пример фактической конфигурации обучения")
    print("="*80)
    practical_training_configs()
    
    print("\n" + "="*80)
    print("Пример 5: Рекомендации по настройке параметров LoRA")
    print("="*80)
    lora_tuning_guidelines()

