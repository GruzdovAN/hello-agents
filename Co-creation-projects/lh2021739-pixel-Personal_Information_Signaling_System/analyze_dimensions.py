"""
Главный скрипт анализа измерений — извлечение измерений из отчётов и корректировка themes
Объединяет загрузку отчётов, извлечение измерений, анализ и рекомендации по themes
"""

import sys
import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Кодировка консоли UTF-8 (Windows)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import dimension_analysis as da
import extract_dimensions as ed
import manage_themes as mt


def load_themes(themes_file: Path) -> List[str]:
    """Загрузка themes"""
    return mt.load_themes(themes_file)


def save_themes(themes_file: Path, themes: List[str]):
    """Сохранение themes"""
    return mt.save_themes(themes_file, themes)


def apply_theme_suggestions(suggestions: Dict[str, List[Dict]], themes: List[str], themes_file: Path, selected_indices: Dict[str, List[int]]) -> List[str]:
    """Применение выбранных пользователем рекомендаций по themes
    
    Args:
        suggestions: Словарь рекомендаций
        themes: Текущий список themes
        themes_file: Путь к файлу themes
        selected_indices: Выбранные пользователем номера: {'add': [1, 3], 'remove': [2]}
    """
    updated_themes = themes.copy()
    
    # Добавление (нумерация с 1)
    add_suggestions = suggestions.get('add', [])
    for idx in selected_indices.get('add', []):
        if 1 <= idx <= len(add_suggestions):
            sug = add_suggestions[idx - 1]  # Преобразование в 0-based индекс
            theme = sug.get('theme')
            if theme and theme not in updated_themes:
                updated_themes.append(theme)
                print(f"✅ Добавлен theme: {theme}")
    
    # Удаление (нумерация с 1)
    remove_suggestions = suggestions.get('remove', [])
    for idx in selected_indices.get('remove', []):
        if 1 <= idx <= len(remove_suggestions):
            sug = remove_suggestions[idx - 1]  # Преобразование в 0-based индекс
            theme = sug.get('theme')
            if theme and theme in updated_themes:
                updated_themes.remove(theme)
                print(f"✅ Удалён theme: {theme}")
    
    # Сохранение
    if updated_themes != themes:
        save_themes(themes_file, updated_themes)
        return updated_themes
    
    return themes


def present_theme_suggestions(suggestions: Dict[str, List[Dict]]):
    """Вывод рекомендаций по themes"""
    print("\n" + "=" * 70)
    print("📋 Рекомендации по корректировке themes")
    print("=" * 70)
    
    all_count = sum(len(v) for k, v in suggestions.items() if k != 'theme_match_analysis')
    if all_count == 0:
        print("✅ Рекомендаций по themes нет")
        return
    
    # Вывод рекомендаций на добавление
    if suggestions.get('add'):
        print("\n【Рекомендации: добавить theme】")
        for i, sug in enumerate(suggestions['add'], 1):
            print(f"  {i}. {sug['theme']}")
            print(f"     Причина: {sug['reason']}")
            print(f"     Частота: {sug.get('frequency', 0)*100:.1f}%")
    
    # Вывод рекомендаций на удаление
    if suggestions.get('remove'):
        print("\n【Рекомендации: удалить theme】")
        for i, sug in enumerate(suggestions['remove'], 1):
            print(f"  {i}. {sug['theme']}")
            print(f"     Причина: {sug['reason']}")
            print(f"     Доля совпадений: {sug.get('match_rate', 0)*100:.1f}%")
    
    print("\n" + "=" * 70)


def get_batch_user_confirmation(add_suggestions: List[Dict], remove_suggestions: List[Dict]) -> Dict[str, List[int]]:
    """Пакетный запрос подтверждения у пользователя
    
    Args:
        add_suggestions: Список рекомендаций на добавление
        remove_suggestions: Список рекомендаций на удаление
    
    Returns:
        Dict с ключами 'add' и 'remove' — номера, выбранные пользователем (с 1)
    """
    selected = {'add': [], 'remove': []}
    
    # Подтверждение добавления
    if add_suggestions:
        print("\n" + "=" * 70)
        print("📥 Подтверждение добавления theme")
        print("=" * 70)
        print("Введите номера theme для добавления (через запятую или пробел: 1,3,5 или 1 3 5)")
        print("Пустой ввод — ничего не добавлять")
        
        while True:
            user_input = input("Номера для добавления: ").strip()
            if not user_input:
                break
            
            # Разбор ввода (запятая или пробел)
            try:
                # Разделение по запятой
                if ',' in user_input:
                    numbers = [int(x.strip()) for x in user_input.split(',') if x.strip()]
                else:
                    # Разделение по пробелу
                    numbers = [int(x.strip()) for x in user_input.split() if x.strip()]
                
                # Проверка диапазона номеров
                valid_numbers = [n for n in numbers if 1 <= n <= len(add_suggestions)]
                if len(valid_numbers) != len(numbers):
                    invalid = [n for n in numbers if n < 1 or n > len(add_suggestions)]
                    print(f"⚠️  Номер {invalid} вне диапазона (1-{len(add_suggestions)}), пропущено")
                
                selected['add'] = valid_numbers
                break
            except ValueError:
                print("⚠️  Неверный формат, введите номера (через запятую или пробел)")
    
    # Подтверждение удаления
    if remove_suggestions:
        print("\n" + "=" * 70)
        print("📤 Подтверждение удаления theme")
        print("=" * 70)
        print("Введите номера theme для удаления (через запятую или пробел: 1,2 или 1 2)")
        print("Пустой ввод — ничего не удалять")
        
        while True:
            user_input = input("Номера для удаления: ").strip()
            if not user_input:
                break
            
            # Разбор ввода (запятая или пробел)
            try:
                # Разделение по запятой
                if ',' in user_input:
                    numbers = [int(x.strip()) for x in user_input.split(',') if x.strip()]
                else:
                    # Разделение по пробелу
                    numbers = [int(x.strip()) for x in user_input.split() if x.strip()]
                
                # Проверка диапазона номеров
                valid_numbers = [n for n in numbers if 1 <= n <= len(remove_suggestions)]
                if len(valid_numbers) != len(numbers):
                    invalid = [n for n in numbers if n < 1 or n > len(remove_suggestions)]
                    print(f"⚠️  Номер {invalid} вне диапазона (1-{len(remove_suggestions)}), пропущено")
                
                selected['remove'] = valid_numbers
                break
            except ValueError:
                print("⚠️  Неверный формат, введите номера (через запятую или пробел)")
    
    return selected


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Инструмент анализа измерений — извлечение из отчётов и корректировка themes")
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Повторное извлечение измерений из отчётов"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Интерактивный режим: показ рекомендаций и запрос подтверждения"
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=None,
        help="Корневой каталог (по умолчанию — каталог скрипта)"
    )
    args = parser.parse_args()
    
    # Определение корневого каталога
    if args.base_dir:
        base_dir = Path(args.base_dir)
    else:
        base_dir = Path(__file__).parent
    
    print("=" * 70)
    print("Инструмент анализа измерений — извлечение из отчётов и корректировка themes")
    print("=" * 70)
    
    # 1. Загрузка или извлечение измерений
    print("\n📊 Обработка результатов извлечения измерений...")
    
    extraction_results = []
    
    if args.extract:
        # Повторное извлечение измерений
        print("🔄 Извлечение измерений из файлов отчётов...")
        llm = ed.init_llm()
        if not llm:
            print("❌ LLM не инициализирован, извлечение невозможно")
            return
        
        # Загрузка themes как ориентира
        themes_file = base_dir / "themes.yaml"
        existing_themes = mt.load_themes(themes_file)
        
        extraction_results = ed.batch_extract_dimensions(base_dir, report_type=None, llm=llm, existing_themes=existing_themes)
        print(f"✅ Из отчётов извлечено {len(extraction_results)} результатов извлечения измерений")
    else:
        # Загрузка сохранённых результатов
        extraction_results = ed.load_extraction_results(base_dir)
        print(f"✅ Загружено {len(extraction_results)} результатов извлечения")
        
        if len(extraction_results) == 0:
            print("⚠️  Результаты не найдены, используйте --extract для повторного извлечения")
            print("💡 Подсказка: python extract_dimensions.py — извлечение измерений")
    
    if len(extraction_results) == 0:
        print("❌ Нет результатов извлечения, анализ невозможен")
        return
    
    # 2. Загрузка themes
    themes_file = base_dir / "themes.yaml"
    themes = load_themes(themes_file)
    
    if not themes:
        print("⚠️  Themes не заданы, сначала настройте themes")
        print("💡 Подсказка: python manage_themes.py — управление themes")
        # Продолжаем с пустым списком для генерации рекомендаций на добавление
    
    print(f"📋 Текущие themes: {themes}")
    
    # 3. Статистика измерений
    dim_stats = da.count_dimension_frequency_from_extractions(extraction_results)
    print(f"\n📈 Статистика измерений: найдено {len(dim_stats)} уникальных измерений")
    if dim_stats:
        print("   Частота измерений (Top 5):")
        sorted_dims = sorted(dim_stats.items(), key=lambda x: x[1]['frequency'], reverse=True)[:5]
        for dim, stats in sorted_dims:
            print(f"   - {dim}: {stats['frequency']}раз ({stats['frequency_rate']*100:.1f}%)")
    
    # 4. Генерация рекомендаций по themes
    print("\n💡 Генерация рекомендаций по themes...")
    suggestions = da.generate_theme_suggestions(extraction_results, themes)
    
    total_suggestions = len(suggestions.get('add', [])) + len(suggestions.get('remove', []))
    print(f"✅ Сгенерировано {total_suggestions} рекомендаций по themes")
    
    # 5. Формирование отчёта анализа
    today = datetime.now().strftime("%Y-%m-%d")
    
    analysis_report = {
        "analysis_date": today,
        "total_extractions": len(extraction_results),
        "dimension_statistics": dim_stats,
        "current_themes": themes,
        "theme_suggestions": {
            "add": suggestions.get('add', []),
            "remove": suggestions.get('remove', [])
        },
        "theme_match_analysis": suggestions.get('theme_match_analysis', {})
    }
    
    # 6. Сохранение отчёта анализа
    analysis_dir = base_dir / "archive" / "dimension_analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    analysis_file = analysis_dir / f"{today}_analysis.json"
    
    try:
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Отчёт анализа сохранён в: {analysis_file}")
    except Exception as e:
        print(f"❌ Ошибка сохранения отчёта анализа: {e}")
    
    # 7. Интерактивный режим: показ рекомендаций и запрос подтверждения
    if args.interactive and total_suggestions > 0:
        present_theme_suggestions(suggestions)
        
        # Пакетный запрос подтверждения у пользователя
        add_suggestions = suggestions.get('add', [])
        remove_suggestions = suggestions.get('remove', [])
        selected_indices = get_batch_user_confirmation(add_suggestions, remove_suggestions)
        
        # Применение выбранных рекомендаций
        updated_themes = apply_theme_suggestions(suggestions, themes, themes_file, selected_indices)
        
        if updated_themes != themes:
            print(f"\n✅ Themes обновлены: {updated_themes}")
        else:
            print("\n✅ Изменения не применены")
    elif total_suggestions > 0:
        # Неинтерактивный режим — только вывод рекомендаций
        present_theme_suggestions(suggestions)
        print("\n💡 Подсказка: --interactive — просмотр и обработка рекомендаций")
    
    print("\n✅ Анализ завершён！")


if __name__ == "__main__":
    main()
