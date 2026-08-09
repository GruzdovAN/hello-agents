"""
Пример распределенного обучения

Этот сценарий демонстрирует, как использовать Accelerate для распределенного обучения.
Сам обучающий код модифицировать не нужно, достаточно запустить его через ускоренный запуск.

Как использовать:
1. Обучение на одном графическом процессоре:
   python 07_distributed_training.py

2. Обучение DDP с несколькими графическими процессорами:
   ускорить запуск --config_file ускорения_конфигураций/multi_gpu_ddp.yaml 07_distributed_training.py

3. Обучение DeepSpeed ZeRO-2:
   ускорить запуск --config_file Acceleration_configs/deepspeed_zero2.yaml 07_distributed_training.py

4. Обучение DeepSpeed ZeRO-3:
   ускорить запуск --config_file Acceleration_configs/deepspeed_zero3.yaml 07_distributed_training.py
"""

import sys
import os

# Добавьте HelloAgents в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "HelloAgents"))

from hello_agents.tools import RLTrainingTool
import json

def main():
    print("="*80)
    print("Пример распределенного обучения")
    print("="*80)
    
    # Обнаружение распределенных сред
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    
    if world_size > 1:
        print(f"\n🚀 Режим распределенного обучения")
        print(f"   - Общее количество процессов: {world_size}")
        print(f"   – Текущий процесс: {local_rank}")
        print(f"   - Распределенный бэкэнд: {os.environ.get('ACCELERATE_DISTRIBUTED_TYPE', 'MULTI_GPU')}")
    else:
        print(f"\n💻 Режим обучения с одним графическим процессором")
    
    print("="*80)
    
    # Создайте инструмент обучения
    rl_tool = RLTrainingTool()
    
    # конфигурация обучения
    # Примечание. Batch_size — это размер пакета каждого графического процессора.
    # Общий размер пакета = размер_пакета × количество графических процессоров × градиент_накопление_шагов.
    config = {
        "action": "train",
        "algorithm": "grpo",
        "model_name": "Qwen/Qwen3-0.6B",
        "output_dir": "./models/grpo_distributed",
        "max_samples": 200,  # Используйте 200 образцов
        "num_epochs": 2,
        "batch_size": 2,  # размер пакета для каждого графического процессора
        "use_lora": True,
        "use_wandb": False,
        "use_tensorboard": True,
    }
    
    # Распечатать конфигурацию только в основном процессе
    if local_rank == 0:
        print("\nКонфигурация обучения:")
        print(f"  - Модель: {config['model_name']}")
        print(f"  - Количество образцов: {config['max_samples']}")
        print(f"  - Количество эпох: {config['num_epochs']}")
        print(f"  - размер пакета для каждого графического процессора: {config['batch_size']}")
        if world_size > 1:
            total_batch = config['batch_size'] * world_size
            print(f"  -Общий размер пакета: {total_batch}")
        print("="*80)
    
    # Начать обучение
    # Код обучения вообще не нужно модифицировать!
    # Accelerate автоматически обрабатывает все детали распределенного обучения.
    result = rl_tool.run(config)
    
    # Распечатывать результаты только в основном процессе
    if local_rank == 0:
        result_data = json.loads(result)
        print("\n" + "="*80)
        print("Обучение завершено!")
        print("="*80)
        print(f"Статус: {result_data['status']}")
        print(f"Путь к модели: {result_data['output_dir']}")
        print("="*80)
        
        # Советы по производительности печати
        if world_size > 1:
            print(f"\n💡 Советы по производительности:")
            print(f"   Для обучения использовались графические процессоры {world_size}.")
            print(f"   Теоретическое ускорение: ~{world_size * 0,85:.1f}x")
            print(f"   (Фактическое ускорение зависит от затрат на связь и загрузки данных)")

if __name__ == "__main__":
    main()

