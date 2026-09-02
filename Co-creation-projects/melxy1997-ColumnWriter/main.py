"""Точка входа основной программы"""

import sys
from orchestrator import ColumnWriterOrchestrator
from exporter import ColumnExporter
from config import get_settings


def main():
    """Главная функция"""
    print("\n" + "="*70)
    print("HelloAgents — система написания колонок")
    print("="*70)
    
    settings = get_settings()
    
    if len(sys.argv) > 1:
        main_topic = " ".join(sys.argv[1:])
    else:
        print("\nВведите тему колонки (Enter — тема по умолчанию):")
        main_topic = input("> ").strip()
        if not main_topic:
            main_topic = "Полное руководство по асинхронному Python"
            print(f"Тема по умолчанию: {main_topic}")
    
    print("\nВыберите режим написания:")
    print("1. ReActAgent (по умолчанию) — рассуждение, действие, инструменты + независимый ревью")
    print("2. ReflectionAgent — саморефлексия, автооптимизация (встроенный ревью)")
    mode_choice = input("> ").strip()
    use_reflection = mode_choice == "2"
    
    if not use_reflection:
        print("\nВключить независимый ревью? (после ревью — автоулучшение)")
        print("1. Включить ревью (по умолчанию) — после генерации, при низкой оценке — правки")
        print("2. Без ревью — только генерация")
        review_choice = input("> ").strip()
        if review_choice == "2":
            settings.enable_review = False
            print("▸ Ревью отключён")
        else:
            print(f"▸ Ревью включён (порог прохождения: {settings.approval_threshold} баллов)")
    
    try:
        orchestrator = ColumnWriterOrchestrator(use_reflection_mode=use_reflection)
        result = orchestrator.create_column(main_topic)
        
        from datetime import datetime
        output_dir = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ColumnExporter.export_to_files(result, output_dir)
        
        print(f"\n{'='*70}")
        print(f"▸ Статистика создания")
        print(f"{'='*70}")
        stats = result['statistics']
        print(f"Всего статей: {stats['total_articles']}")
        print(f"Всего слов: {stats['total_words']:,}")
        print(f"Среднее слов на статью: {stats['avg_words_per_article']:,}")
        
        if 'creation_stats' in result:
            creation = result['creation_stats']
            print(f"\nПроцесс создания:")
            print(f"  Генераций: {creation.get('total_generations', 0)}")
            if creation.get('total_reviews', 0) > 0:
                print(f"  Ревью: {creation.get('total_reviews', 0)}")
                print(f"  Прошли с первого раза: {creation.get('approved_first_try', 0)}")
            if creation.get('total_revisions', 0) > 0:
                print(f"  Правок: {creation.get('total_revisions', 0)}")
            if creation.get('total_rewrites', 0) > 0:
                print(f"  Переписываний: {creation.get('total_rewrites', 0)}")
        
        if 'agent_modes' in result:
            print(f"\nAgent режимы:")
            print(f"  Planner: {result['agent_modes']['planner']}")
            print(f"  Writer: {result['agent_modes']['writer']}")
            if result['agent_modes'].get('reviewer'):
                print(f"  Reviewer: {result['agent_modes']['reviewer']}")
            if result['agent_modes'].get('revision'):
                print(f"  Revision: {result['agent_modes']['revision']}")
        
        print(f"\n{'='*70}")
        print(f"▸ Колонка создана!")
        print(f"   Каталог вывода: {output_dir}")
        print(f"{'='*70}\n")
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n▸ Ошибка программы: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
