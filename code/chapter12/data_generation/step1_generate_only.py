"""
Шаг 1. Создавайте только вопросы AIME

Как запустить:
python data_generate/step1_generate_only.py 30 3.0

Параметры:
- 30: количество сгенерированных вопросов.
- 3.0: Задержка между каждым поколением (секунды).
"""

import sys
from aime_generator import AIMEGenerator


def main():
    # Анализ аргументов командной строки
    num_problems = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    delay_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
    
    print("\n" + "="*80)
    print("📝 Шаг 1. Создайте вопросы AIME.")
    print("="*80)
    print(f"\nИнформация о конфигурации:")
    print(f"  – Количество созданных вопросов: {num_problems}")
    print(f"  - Задержка API: {delay_секунды} секунд/вопрос.")
    print(f"  - Генерация справочных данных: TianHongZXY/aime-1983-2025 (более 900 вопросов)")
    
    # Создать генератор
    generator = AIMEGenerator(delay_seconds=delay_seconds)
    
    # Сгенерируйте и сохраните
    generated_data_path = generator.generate_and_save(
        num_problems=num_problems,
        output_dir="data_generation/generated_data"
    )
    
    print(f"\n ✅ Шаг 1 завершен! Сгенерированные данные сохраняются в: {generated_data_path}.")
    print(f"\nСледующий шаг: запустить оценку")
    print(f"python data_generation/step2_evaluate_only.py {generated_data_path} 2024")


if __name__ == "__main__":
    main()

