"""
Пример 4: Полный процесс обучения SFT

Демонстрирует, как использовать RLTrainingTool для контролируемой точной настройки SFT.
"""

import sys
from pathlib import Path
import json

# Добавить путь к проекту
project_root = Path(__file__).parent.parent / "HelloAgents"
sys.path.insert(0, str(project_root))

from hello_agents.tools import RLTrainingTool


# ============================================================================
# Пример 1: Простейшее обучение SFT
# ============================================================================

def minimal_sft_training():
    """
    Простейший пример обучения SFT
    
    Просто позвоните в RLTrainingTool
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/sft_minimal",
        "max_samples": 10,
        "num_epochs": 1,
    }
    
    print("Простейшее обучение SFT:")
    print(f"  Модель: {config['model_name']}")
    print(f"  Количество образцов: {config['max_samples']}")
    print(f"  Количество эпох обучения: {config['num_epochs']}")
    
    # Раскомментируйте во время фактического обучения
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n© Обучение завершено! Модель сохранена в папке: {result_dict['output_dir']}")
    
    return config


# ============================================================================
# Пример 2: Стандартная конфигурация обучения SFT
# ============================================================================

def standard_sft_training():
    """
    Стандартная конфигурация обучения SFT
    
    Содержит:
    - Эффективная точная настройка параметров LoRA
    - Разумные параметры обучения
    - Использовать часть набора данных
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "sft",
        
        # Конфигурация модели
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/sft_standard",
        
        # Конфигурация данных
        "max_samples": 1000,  # Используйте 1000 образцов
        
        # конфигурация обучения
        "num_epochs": 3,
        "batch_size": 4,
        "learning_rate": 5e-5,
        
        # Конфигурация ЛоРА
        "use_lora": True,
        "lora_r": 16,
        "lora_alpha": 32,
    }
    
    print("Стандартная конфигурация обучения SFT:")
    print(f"  Модель: {config['model_name']}")
    print(f"  Количество образцов: {config['max_samples']}")
    print(f"  Количество эпох обучения: {config['num_epochs']}")
    print(f"  batch_size: {config['batch_size']}")
    print(f"  learning_rate: {config['learning_rate']}")
    print(f"  Ранг LoRA: {config['lora_r']}")
    
    # Раскомментируйте во время фактического обучения
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n© Обучение завершено!")
    # print(f"📁 Модель сохранена в: {result_dict['output_dir']}")
    
    return config


# ============================================================================
# Пример 3: Обучение полному набору данных
# ============================================================================

def full_dataset_training():
    """
    Тренируйтесь, используя полный набор данных
    
    max_samples=None означает использование всех данных
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/sft_full",
        
        # Использовать все данные
        "max_samples": None,  # Нет = использовать все данные
        
        "num_epochs": 3,
        "batch_size": 4,
        "learning_rate": 5e-5,
        "use_lora": True,
        "lora_r": 16,
        "lora_alpha": 32,
    }
    
    print("Полное обучение набору данных:")
    print(f"  Модель: {config['model_name']}")
    print(f"  Количество образцов: Все (max_samples=Нет)")
    print(f"  Количество эпох обучения: {config['num_epochs']}")
    print(f"  Примерное количество образцов: ~7500 (обучающий набор GSM8K)")
    
    # Раскомментируйте во время фактического обучения
    # result = tool.run(config)
    # result_dict = json.loads(result)
    # print(f"\n© Обучение завершено!")
    
    return config


# ============================================================================
# Пример 4: Сравнение различных скоростей обучения
# ============================================================================

def compare_learning_rates():
    """
    Сравните эффект обучения при различных скоростях обучения
    
    Часто используемые темпы обучения:
    - 1e-5: Консервативный, подходит для тонкой настройки и без того хорошей модели.
    - 5e-5: рекомендуется, сочетает скорость обучения и стабильность.
    - 1e-4: Радикальный, подходит для быстрых экспериментов.
    """
    learning_rates = {
        "Консервативный (1e-5)": 1e-5,
        "Рекомендуется (5e-5)": 5e-5,
        "Радикал (1e-4)": 1e-4,
    }
    
    print("Сравнение различных скоростей обучения:")
    for name, lr in learning_rates.items():
        print(f"\n{name}:")
        print(f"  learning_rate: {lr}")
        print(f"  Применимые сценарии: ", end="")
        if lr == 1e-5:
            print("Модель уже хороша, просто требуется доработка.")
        elif lr == 5e-5:
            print("Стандартное обучение, рекомендуется")
        else:
            print("Быстрый эксперимент (возможно, нестабильный)")
    
    # Пример обучения
    print("\nПример обучения (рекомендуемая скорость обучения):")
    tool = RLTrainingTool()
    config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "max_samples": 1000,
        "num_epochs": 3,
        "learning_rate": 5e-5,
        "use_lora": True,
    }
    print(f"  learning_rate: {config['learning_rate']}")
    
    # result = tool.run(config)
    
    return learning_rates


# ============================================================================
# Пример 5: Настройка оптимизации видеопамяти
# ============================================================================

def memory_optimized_training():
    """
    Конфигурация оптимизации видеопамяти
    
    Подходит для ситуаций, когда видеопамять ограничена:
    - Используйте ЛоРА
    - Уменьшить размер партии
    - Используйте меньший ранг LoRA.
    """
    tool = RLTrainingTool()
    
    config = {
        "action": "train",
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/sft_memory_opt",
        
        # Оптимизация видеопамяти
        "max_samples": 1000,
        "num_epochs": 3,
        "batch_size": 1,  # Минимальный размер партии
        "learning_rate": 5e-5,
        
        # Конфигурация ЛоРА
        "use_lora": True,
        "lora_r": 8,  # Используйте меньший ранг
        "lora_alpha": 16,
    }
    
    print("Конфигурация оптимизации памяти:")
    print(f"  пакетный_размер: {config['batch_size']} (минимум)")
    print(f"  lora_r: {config['lora_r']} (меньше)")
    print(f"  use_lora: {config['use_lora']}")
    print(f"  Примерное использование видеопамяти: ~3-4 ГБ")
    
    # Раскомментируйте во время фактического обучения
    # result = tool.run(config)
    
    return config


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
        "algorithm": "sft",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./output/sft_practical",
        
        # Быстрое тестирование с использованием меньшего количества образцов
        "max_samples": 100,
        "num_epochs": 1,
        "batch_size": 4,
        "learning_rate": 5e-5,
        
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
    print("Пример 1: Простейшее обучение SFT")
    print("="*80)
    minimal_sft_training()
    
    print("\n" + "="*80)
    print("Пример 2: Стандартная конфигурация обучения SFT")
    print("="*80)
    standard_sft_training()
    
    print("\n" + "="*80)
    print("Пример 3: Обучение полному набору данных")
    print("="*80)
    full_dataset_training()
    
    print("\n" + "="*80)
    print("Пример 4: Сравнение различных скоростей обучения")
    print("="*80)
    compare_learning_rates()
    
    print("\n" + "="*80)
    print("Пример 5: Настройка оптимизации видеопамяти")
    print("="*80)
    memory_optimized_training()
    
    print("\n" + "="*80)
    print("Пример 6: Фактический пример обучения")
    print("="*80)
    practical_training_example()

