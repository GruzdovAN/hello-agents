"""
Полный процесс обучения Agentic RL (обновленная версия)
Комплексный пример от подготовки данных до развертывания модели

Обновления:
1. Исправлена проблема с разбором JSON.
2. Добавлена конфигурация мониторинга обучения (wandb/tensorboard).
3. Поддержка подробного вывода журнала.
"""

import sys
import os

# Добавьте HelloAgents в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "HelloAgents"))

from hello_agents.tools import RLTrainingTool
import json
from datetime import datetime

class AgenticRLPipeline:
    """Конвейер обучения агентов RL"""
    
    def __init__(self, config_path="config.json"):
        """
        Инициализировать конвейер обучения
        
        Аргументы:
            config_path: путь к файлу конфигурации
        """
        self.rl_tool = RLTrainingTool()
        self.config = self.load_config(config_path)
        self.results = {}
        
    def load_config(self, config_path):
        """Загрузить файл конфигурации"""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def log(self, message):
        """регистрация"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def stage1_prepare_data(self):
        """Этап 1: Подготовка данных"""
        self.log("=" * 50)
        self.log("Этап 1: Подготовка данных")
        self.log("=" * 50)
        
        # Загрузите и проверьте набор данных
        result = self.rl_tool.run({
            "action": "load_dataset",
            "format": "sft",
            "max_samples": self.config["data"]["max_samples"],
        })
        
        # Анализ результатов JSON
        dataset_info = json.loads(result)

        self.log(f"✓ Загрузка набора данных завершена")
        self.log(f"  - Количество образцов: {dataset_info['dataset_size']}")
        self.log(f"  – Формат: {dataset_info['format']}")
        self.log(f"  - Столбец данных: {', '.join(dataset_info['sample_keys'])}")
        
        self.results["data"] = dataset_info
        
        return dataset_info
    
    def stage2_sft_training(self):
        """Этап 2: Обучение SFT"""
        self.log("\n" + "=" * 50)
        self.log("Этап 2: Обучение SFT")
        self.log("=" * 50)
        
        sft_config = self.config["sft"]
        
        result = self.rl_tool.run({
            "action": "train",
            "algorithm": "sft",
            "model_name": self.config["model"]["base_model"],
            "output_dir": sft_config["output_dir"],
            "max_samples": self.config["data"]["max_samples"],
            "num_epochs": sft_config["num_epochs"],
            "batch_size": sft_config["batch_size"],
            "use_lora": True,
            # Конфигурация мониторинга обучения
            "use_wandb": self.config.get("monitoring", {}).get("use_wandb", False),
            "use_tensorboard": self.config.get("monitoring", {}).get("use_tensorboard", True),
            "wandb_project": self.config.get("monitoring", {}).get("wandb_project", None),
        })
        
        # Анализ результатов JSON
        result_data = json.loads(result)
        
        self.log(f"✓ Обучение SFT завершено")
        self.log(f"  – Путь к модели: {result_data['output_dir']}")
        self.log(f"  – Статус: {result_data['status']}")
        
        self.results["sft_training"] = result_data
        
        return result_data["output_dir"]
    
    def stage3_sft_evaluation(self, model_path):
        """Этап 3: Оценка SFT"""
        self.log("\n" + "=" * 50)
        self.log("Этап 3: Оценка SFT")
        self.log("=" * 50)
        
        result = self.rl_tool.run({
            "action": "evaluate",
            "model_path": model_path,
            "max_samples": self.config["eval"]["max_samples"],
            "use_lora": True,
        })
        eval_data = json.loads(result)

        self.log(f"✓ Оценка SFT завершена")
        self.log(f"  - Точность: {eval_data['accuracy']}")
        self.log(f"  - Средняя награда: {eval_data['average_reward']}")

        self.results["sft_evaluation"] = eval_data

        return eval_data
    
    def stage4_grpo_training(self, sft_model_path):
        """Этап 4: Обучение GRPO"""
        self.log("\n" + "=" * 50)
        self.log("Этап 4: Обучение GRPO")
        self.log("=" * 50)
        
        grpo_config = self.config["grpo"]
        
        result = self.rl_tool.run({
            "action": "train",
            "algorithm": "grpo",
            "model_name": sft_model_path,
            "output_dir": grpo_config["output_dir"],
            "max_samples": self.config["data"]["max_samples"],
            "num_epochs": grpo_config["num_epochs"],
            "batch_size": grpo_config["batch_size"],
            "use_lora": True,
            # Конфигурация мониторинга обучения
            "use_wandb": self.config.get("monitoring", {}).get("use_wandb", False),
            "use_tensorboard": self.config.get("monitoring", {}).get("use_tensorboard", True),
            "wandb_project": self.config.get("monitoring", {}).get("wandb_project", None),
        })
        
        # Анализ результатов JSON
        result_data = json.loads(result)
        
        self.log(f"✓ Завершено обучение GRPO")
        self.log(f"  – Путь к модели: {result_data['output_dir']}")
        self.log(f"  – Статус: {result_data['status']}")
        
        self.results["grpo_training"] = result_data
        
        return result_data["output_dir"]
    
    def stage5_grpo_evaluation(self, model_path):
        """Этап 5: Оценка GRPO"""
        self.log("\n" + "=" * 50)
        self.log("Этап 5: Оценка GRPO")
        self.log("=" * 50)
        
        result = self.rl_tool.run({
            "action": "evaluate",
            "model_path": model_path,
            "max_samples": self.config["eval"]["max_samples"],
            "use_lora": True,
        })
        eval_data = json.loads(result)

        self.log(f"✓ Оценка GRPO завершена")
        self.log(f"  - Точность: {eval_data['accuracy']}")
        self.log(f"  - Средняя награда: {eval_data['average_reward']}")

        self.results["grpo_evaluation"] = eval_data

        return eval_data
    
    def stage6_save_results(self):
        """Этап 6: Сохранить результаты"""
        self.log("\n" + "=" * 50)
        self.log("Этап 6: Сохранить результаты")
        self.log("=" * 50)
        
        # Сохраняйте результаты тренировок
        results_path = "training_results.json"
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.log(f"✓ Результаты сохраняются в: {results_path}")
    
    def run(self):
        """Запустите полный процесс"""
        try:
            # Этап 1: Подготовка данных
            self.stage1_prepare_data()
            
            # Этап 2: Обучение SFT
            sft_model_path = self.stage2_sft_training()
            
            # Этап 3: Оценка SFT
            self.stage3_sft_evaluation(sft_model_path)
            
            # Этап 4: Обучение GRPO
            grpo_model_path = self.stage4_grpo_training(sft_model_path)
            
            # Этап 5: Оценка GRPO
            self.stage5_grpo_evaluation(grpo_model_path)
            
            # Этап 6: Сохранить результаты
            self.stage6_save_results()
            
            self.log("\n" + "=" * 50)
            self.log("✓ Процесс обучения завершен!")
            self.log("=" * 50)
            
        except Exception as e:
            self.log(f"\n✗ Обучение не удалось: {str(e)}")
            raise

# Пример использования
if __name__ == "__main__":
    # Создать файл конфигурации
    config = {
        "model": {
            "base_model": "Qwen/Qwen3-0.6B"
        },
        "data": {
            "max_samples": 100  # Быстрый тест со 100 образцами
        },
        "sft": {
            "output_dir": "./models/sft_model",
            "num_epochs": 2,
            "batch_size": 4,
        },
        "grpo": {
            "output_dir": "./models/grpo_model",
            "num_epochs": 2,
            "batch_size": 2,
        },
        "eval": {
            "max_samples": 20,
            "sft_accuracy_threshold": 0.40
        },
        "monitoring": {
            "use_wandb": False,  # Использовать ли Wandb
            "use_tensorboard": True,  # Использовать ли TensorBoard
            "wandb_project": "agentic-rl-pipeline"  # Название проекта Wandb
        }
    }
    
    # Сохранить конфигурацию
    with open("config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    # Запустите тренировочный процесс
    pipeline = AgenticRLPipeline("config.json")
    pipeline.run()

