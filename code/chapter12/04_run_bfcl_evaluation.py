"""
Глава 12: Сценарий оценки BFCL в один клик

Этот сценарий обеспечивает полный процесс оценки BFCL:
1. Автоматическая проверка и подготовка данных BFCL.
2. Запустите оценку HelloAgents.
3. Экспортируйте результаты в формат BFCL.
4. Позвоните в официальный инструмент оценки BFCL.
5. Представление результатов оценки

Как использовать:
    примеры Python/04_run_bfcl_evaluation.py

Дополнительные параметры:
    --category: категория оценки (по умолчанию: simple_python)
    --samples: количество выборок (по умолчанию: 5, установлено значение 0 для представления всех)
    --model-name: имя модели (по умолчанию: HelloAgents)
"""

import sys
import subprocess
from pathlib import Path
import argparse
import json

# Добавить путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.evaluation import BFCLDataset, BFCLEvaluator


# Слово системной подсказки для вызова функции
FUNCTION_CALLING_SYSTEM_PROMPT = """Вы профессиональный помощник по вызову функций.

Ваша задача — сгенерировать правильный вызов функции на основе вопроса пользователя и предоставленного определения функции.

Требования к выходному формату:
1. Он должен быть в чистом формате JSON, не добавляйте пояснительного текста.
2. Используйте формат массива JSON: [{"name": "Имя функции", "arguments": {"Имя параметра": "Значение параметра"}}]
3. Если вам нужно вызвать несколько функций, добавьте в массив несколько объектов.
4. Если нет необходимости вызывать функцию, верните пустой массив: []

Пример:
Вопрос пользователя: Узнать погоду в Пекине
Доступные функции: get_weather(city: str)
Правильный вывод: [{"name": "get_weather", "arguments": {"city": "Beijing"}}]

Примечание:
- Выводите только JSON, не добавляйте дополнительный текст, например «Хорошо», «Я вам помогу» и т. д.
- Значения параметров должны соответствовать типу, определенному функцией.
- Имена параметров должны быть точно такими же, как определение функции.
"""


def check_bfcl_data(bfcl_data_dir: Path) -> bool:
    """Проверьте, существуют ли данные BFCL"""
    if not bfcl_data_dir.exists():
        print(f"\n❌ Каталог данных BFCL не существует: {bfcl_data_dir}")
        print(f"\nСначала клонируйте репозиторий BFCL:")
        print(f"   git clone --depth 1 https://github.com/ShishirPatil/gorilla.git temp_gorilla")
        return False
    return True


def run_evaluation(category: str, max_samples: int, model_name: str) -> dict:
    """Запустите оценку HelloAgents"""
    print("\n" + "="*60)
    print("Шаг 1. Запустите оценку HelloAgents.")
    print("="*60)
    
    # Каталог данных BFCL
    bfcl_data_dir = project_root / "temp_gorilla" / "berkeley-function-call-leaderboard" / "bfcl_eval" / "data"
    
    # Проверить данные
    if not check_bfcl_data(bfcl_data_dir):
        return None
    
    # Загрузить набор данных
    print(f"\n📚 Загрузка набора данных BFCL...")
    dataset = BFCLDataset(bfcl_data_dir=str(bfcl_data_dir), category=category)

    # Создать агента
    print(f"\n🤖 Создать агента...")
    llm = HelloAgentsLLM()
    agent = SimpleAgent(
        name=model_name,
        llm=llm,
        system_prompt=FUNCTION_CALLING_SYSTEM_PROMPT,
        enable_tool_calling=False
    )
    print(f"   Агент: {model_name}")
    print(f"   LLM: {llm.provider}")

    # Создать оценщика
    evaluator = BFCLEvaluator(dataset=dataset, category=category)

    # Запустите оценку (передайте параметр max_samples)
    print(f"\n🔄 Начинаем оценивать...")
    if max_samples > 0:
        print(f"   Количество образцов: {max_samples}")
        results = evaluator.evaluate(agent, max_samples=max_samples)
    else:
        print(f"   Размер выборки: Все")
        results = evaluator.evaluate(agent, max_samples=None)
    
    # Показать результаты
    print(f"\n📊 Результаты оценки:")
    print(f"   Точность: {results['overall_accuracy']:.2%}")
    print(f"   Правильный номер: {results['correct_samples']}/{results['total_samples']}")
    
    return results


def export_bfcl_format(results: dict, category: str, model_name: str) -> Path:
    """Экспорт результатов в формате BFCL"""
    print("\n" + "="*60)
    print("Шаг 2. Экспортируйте результаты в формат BFCL.")
    print("="*60)
    
    # Выходной каталог
    output_dir = project_root / "evaluation_results" / "bfcl_official"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # выходной файл
    output_file = output_dir / f"BFCL_v4_{category}_result.json"
    
    # Создать оценщик (для экспорта)
    bfcl_data_dir = project_root / "temp_gorilla" / "berkeley-function-call-leaderboard" / "bfcl_eval" / "data"
    dataset = BFCLDataset(bfcl_data_dir=str(bfcl_data_dir), category=category)
    evaluator = BFCLEvaluator(dataset=dataset, category=category)
    
    # Экспорт
    evaluator.export_to_bfcl_format(results, output_file)
    
    return output_file


def copy_to_bfcl_result_dir(source_file: Path, model_name: str, category: str) -> Path:
    """Скопируйте файлы результатов в каталог результатов BFCL."""
    print("\n" + "="*60)
    print("Шаг 3. Подготовьтесь к официальной оценке BFCL.")
    print("="*60)
    
    # Каталог результатов BFCL
    # Примечание. BFCL заменит «/» в названии модели на «_».
    safe_model_name = model_name.replace("/", "_")
    result_dir = project_root / "result" / safe_model_name
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # объектный файл
    target_file = result_dir / f"BFCL_v4_{category}_result.json"
    
    # Копировать файлы
    import shutil
    shutil.copy(source_file, target_file)
    
    print(f"\n ✅ Файл результатов был скопирован в:")
    print(f"   {target_file}")
    
    return target_file


def run_bfcl_official_eval(model_name: str, category: str) -> bool:
    """Запустите официальную оценку BFCL"""
    print("\n" + "="*60)
    print("Шаг 4. Проведите официальную оценку BFCL.")
    print("="*60)
    
    try:
        # Установить переменные среды
        import os
        os.environ['PYTHONUTF8'] = '1'
        
        # Запустите оценку BFCL
        cmd = [
            "bfcl", "evaluate",
            "--model", model_name,
            "--test-category", category,
            "--partial-eval"
        ]
        
        print(f"\n🔄 Выполните команду: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # показать вывод
        if result.stdout:
            print(result.stdout)
        
        if result.returncode != 0:
            print(f"\n❌ Оценка BFCL не удалась:")
            if result.stderr:
                print(result.stderr)
            return False
        
        return True
        
    except FileNotFoundError:
        print("\n❌ команда bfcl не найдена")
        print("   Пожалуйста, сначала установите: pip install bfcl-eval")
        return False
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении оценки BFCL: {e}")
        return False


def show_results(model_name: str, category: str):
    """Показать результаты оценки"""
    print("\n" + "="*60)
    print("Шаг 5: Представление результатов оценки")
    print("="*60)
    
    # CSV-файл
    csv_file = project_root / "score" / "data_non_live.csv"
    
    if csv_file.exists():
        print(f"\n📊 Сводка результатов оценки:")
        with open(csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    else:
        print(f"\n⚠️ Файл результатов оценки не найден: {csv_file}")
    
    # Подробный файл оценок
    safe_model_name = model_name.replace("/", "_")
    score_file = project_root / "score" / safe_model_name / "non_live" / f"BFCL_v4_{category}_score.json"
    
    if score_file.exists():
        print(f"\n📝 Подробный файл оценок:")
        print(f"   {score_file}")
        
        # Точность чтения и отображения
        with open(score_file, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            summary = json.loads(first_line)
            print(f"\n🎯 Окончательный результат:")
            print(f"   Точность: {summary['accuracy']:.2%}")
            print(f"   Правильный номер: {summary['correct_count']}/{summary['total_count']}")


def main():
    """основная функция"""
    parser = argparse.ArgumentParser(description="Сценарий оценки BFCL в один клик")
    parser.add_argument("--category", default="simple_python", help="Категория оценки")
    parser.add_argument("--samples", type=int, default=5, help="Размер выборки (0 означает все)")
    parser.add_argument("--model-name", default="Qwen/Qwen3-8B",
                       help="Название модели (должна быть модель, поддерживаемая BFCL, для просмотра запустите «модели bfcl»)")
    
    args = parser.parse_args()
    
    print("="*60)
    print("Сценарий оценки BFCL в один клик")
    print("="*60)
    print(f"\nКонфигурация:")
    print(f"   Категория оценки: {args.category}")
    print(f"   Количество выборок: {args.samples, если args.samples > 0, иначе 'все'}")
    print(f"   Название модели: {args.model_name}")
    
    # Шаг 1. Запустите оценку
    results = run_evaluation(args.category, args.samples, args.model_name)
    if not results:
        return
    
    # Шаг 2. Экспортируйте формат BFCL.
    output_file = export_bfcl_format(results, args.category, args.model_name)
    
    # Шаг 3. Скопируйте в каталог результатов BFCL.
    copy_to_bfcl_result_dir(output_file, args.model_name, args.category)
    
    # Шаг 4. Проведите официальную оценку BFCL.
    if not run_bfcl_official_eval(args.model_name, args.category):
        print("\n⚠️ Официальная оценка BFCL не удалась, но оценка HelloAgents завершена.")
        return
    
    # Шаг 5. Покажите результаты
    show_results(args.model_name, args.category)
    
    print("\n" + "="*60)
    print("✅Оценка завершена!")
    print("="*60)


if __name__ == "__main__":
    main()

