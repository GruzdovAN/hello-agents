"""
Модуль анализа измерений — V1 (упрощённая версия)
Сбор данных измерений, анализ, генерация рекомендаций и взаимодействие с пользователем
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import defaultdict

# Кодировка консоли UTF-8 (Windows)
# Перенаправление только при запуске как скрипт
if sys.platform == 'win32' and __name__ == "__main__":
    import io
    if not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# ==================== Сбор данных ====================

def collect_daily_records(archive_dir: Path) -> List[Dict]:
    """Чтение всех ежедневных JSON из archive/youtube/"""
    records = []
    if not archive_dir.exists():
        return records
    
    for json_file in archive_dir.glob("*.json"):
        if json_file.name.endswith("_research.json"):
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'dimensions' not in data:
                    data['dimensions'] = []
                records.append(data)
        except Exception as e:
            print(f"⚠️  Ошибка чтения файла {json_file.name}: {e}")
    
    return records


def collect_weekly_records(weekly_dir: Path) -> List[Dict]:
    """Чтение еженедельных JSON из каталога"""
    records = []
    if not weekly_dir.exists():
        return records
    
    for json_file in weekly_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'dimensions' not in data:
                    data['dimensions'] = []
                records.append(data)
        except Exception as e:
            print(f"⚠️  Ошибка чтения еженедельного файла {json_file.name}: {e}")
    
    return records


def collect_monthly_records(monthly_dir: Path) -> List[Dict]:
    """Чтение ежемесячных JSON из каталога"""
    records = []
    if not monthly_dir.exists():
        return records
    
    for json_file in monthly_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'dimensions' not in data:
                    data['dimensions'] = []
                records.append(data)
        except Exception as e:
            print(f"⚠️  Ошибка чтения ежемесячного файла {json_file.name}: {e}")
    
    return records


def load_all_records(base_dir: Path) -> Dict[str, List[Dict]]:
    """Загрузка записей всех типов"""
    archive_dir = base_dir / "archive" / "youtube"
    weekly_dir = base_dir / "archive" / "weekly"
    monthly_dir = base_dir / "archive" / "monthly"
    
    return {
        "daily": collect_daily_records(archive_dir),
        "weekly": collect_weekly_records(weekly_dir),
        "monthly": collect_monthly_records(monthly_dir)
    }


# ==================== Анализ измерений ====================

def parse_date(date_str: str) -> Optional[datetime]:
    """Разбор строки даты в datetime"""
    try:
        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def count_dimension_frequency(records: List[Dict]) -> Dict[str, Dict]:
    """Частота появления каждого измерения"""
    dimension_stats = defaultdict(lambda: {
        'frequency': 0,
        'dates': [],
        'first_seen': None,
        'last_seen': None
    })
    
    total_records = len(records)
    
    for record in records:
        date_str = record.get('date', '')
        dimensions = record.get('dimensions', [])
        
        if not dimensions:
            continue
        
        record_date = parse_date(date_str)
        
        for dim in dimensions:
            if dim:
                dimension_stats[dim]['frequency'] += 1
                if record_date:
                    dimension_stats[dim]['dates'].append(record_date)
                    if dimension_stats[dim]['first_seen'] is None or record_date < dimension_stats[dim]['first_seen']:
                        dimension_stats[dim]['first_seen'] = record_date
                    if dimension_stats[dim]['last_seen'] is None or record_date > dimension_stats[dim]['last_seen']:
                        dimension_stats[dim]['last_seen'] = record_date
    
    result = {}
    for dim, stats in dimension_stats.items():
        result[dim] = {
            'frequency': stats['frequency'],
            'frequency_rate': stats['frequency'] / total_records if total_records > 0 else 0.0,
            'first_seen': stats['first_seen'].strftime("%Y-%m-%d") if stats['first_seen'] else None,
            'last_seen': stats['last_seen'].strftime("%Y-%m-%d") if stats['last_seen'] else None,
            'dates': [d.strftime("%Y-%m-%d") for d in stats['dates']]
        }
    
    return result


def find_missing_dimensions(records: List[Dict], candidate_dimensions: List[str], days_threshold: int = 30) -> List[str]:
    """Измерения, не появлявшиеся более N дней"""
    now = datetime.now()
    missing = []
    
    for dim in candidate_dimensions:
        last_seen = None
        for record in records:
            dimensions = record.get('dimensions', [])
            if dim in dimensions:
                date_str = record.get('date', '')
                record_date = parse_date(date_str)
                if record_date and (last_seen is None or record_date > last_seen):
                    last_seen = record_date
        
        if last_seen is None:
            missing.append(dim)
        else:
            days_diff = (now - last_seen).days
            if days_diff > days_threshold:
                missing.append(dim)
    
    return missing


# ==================== Приоритеты ====================

def calculate_dimension_priority(records: List[Dict]) -> Dict[str, float]:
    """Приоритет измерения (только по частоте появления)"""
    stats = count_dimension_frequency(records)
    priorities = {}
    
    for dim, dim_stats in stats.items():
        priorities[dim] = dim_stats['frequency_rate']
    
    return priorities


# ==================== Генерация рекомендаций ====================

def suggest_add_dimensions(records: List[Dict], candidate_dimensions: List[str], threshold_days: int = 30) -> List[Dict]:
    """Рекомендация добавить отсутствующие важные измерения"""
    missing = find_missing_dimensions(records, candidate_dimensions, threshold_days)
    suggestions = []
    
    for dim in missing:
        stats = count_dimension_frequency(records)
        suggested_priority = stats.get(dim, {}).get('frequency_rate', 0.5)
        
        suggestions.append({
            "suggestion_id": f"add_{dim}_{datetime.now().strftime('%Y%m%d')}",
            "type": "add",
            "dimension": dim,
            "reason": f"Не появлялось в записях {threshold_days} дней, но есть в списке кандидатов",
            "recommendation": "Рекомендуется добавить это измерение",
            "suggested_priority": round(suggested_priority, 2)
        })
    
    return suggestions


def suggest_remove_dimensions(records: List[Dict], active_dimensions: List[str], threshold_days: int = 60) -> List[Dict]:
    """Рекомендация удалить давно не появлявшиеся измерения"""
    stats = count_dimension_frequency(records)
    suggestions = []
    
    now = datetime.now()
    
    for dim in active_dimensions:
        dim_stat = stats.get(dim, {})
        last_seen_str = dim_stat.get('last_seen')
        
        if not last_seen_str:
            suggestions.append({
                "suggestion_id": f"remove_{dim}_{datetime.now().strftime('%Y%m%d')}",
                "type": "remove",
                "dimension": dim,
                "reason": "Никогда не появлялось в записях",
                "recommendation": "Рекомендуется удалить это измерение"
            })
        else:
            last_seen = parse_date(last_seen_str)
            if last_seen:
                days_diff = (now - last_seen).days
                if days_diff > threshold_days:
                    suggestions.append({
                        "suggestion_id": f"remove_{dim}_{datetime.now().strftime('%Y%m%d')}",
                        "type": "remove",
                        "dimension": dim,
                        "reason": f"Не появлялось в записях {days_diff} дней",
                        "recommendation": "Рекомендуется удалить это измерение"
                    })
    
    return suggestions


def suggest_priority_adjustment(records: List[Dict], dimension_config: Dict) -> List[Dict]:
    """Рекомендация повысить приоритет часто появляющихся измерений"""
    stats = count_dimension_frequency(records)
    suggestions = []
    
    active_dimensions = dimension_config.get('active_dimensions', [])
    
    for dim_info in active_dimensions:
        dim_name = dim_info.get('name')
        current_priority = dim_info.get('priority', 0.0)
        dim_stat = stats.get(dim_name, {})
        frequency_rate = dim_stat.get('frequency_rate', 0.0)
        
        if frequency_rate > 0.7 and current_priority < frequency_rate:
            suggestions.append({
                "suggestion_id": f"priority_{dim_name}_{datetime.now().strftime('%Y%m%d')}",
                "type": "priority_adjustment",
                "dimension": dim_name,
                "reason": f"Недавняя частота {frequency_rate*100:.1f}%, текущий приоритет {current_priority:.2f}",
                "current_priority": current_priority,
                "suggested_priority": round(frequency_rate, 2),
                "recommendation": "Рекомендуется повысить приоритет этого измерения"
            })
    
    return suggestions


def generate_all_suggestions(records: List[Dict], dimension_config: Dict) -> Dict[str, List[Dict]]:
    """Сводный отчёт по всем рекомендациям"""
    active_dimensions = [d['name'] for d in dimension_config.get('active_dimensions', [])]
    candidate_dimensions = dimension_config.get('candidate_dimensions', [])
    
    add_suggestions = suggest_add_dimensions(records, candidate_dimensions, threshold_days=30)
    remove_suggestions = suggest_remove_dimensions(records, active_dimensions, threshold_days=60)
    priority_suggestions = suggest_priority_adjustment(records, dimension_config)
    
    return {
        "add": add_suggestions,
        "remove": remove_suggestions,
        "priority_adjustment": priority_suggestions
    }


# ==================== Сопоставление измерений и themes ====================

def count_dimension_frequency_from_extractions(extraction_results: List[Dict]) -> Dict[str, Dict]:
    """Частота измерений из результатов извлечения"""
    dimension_stats = defaultdict(lambda: {
        'frequency': 0,
        'dates': [],
        'first_seen': None,
        'last_seen': None
    })
    
    total_extractions = len(extraction_results)
    
    for result in extraction_results:
        dimensions = result.get('dimensions', [])
        extraction_date_str = result.get('extraction_date', result.get('report_date', ''))
        extraction_date = parse_date(extraction_date_str.split('T')[0])
        
        for dim in dimensions:
            if dim:
                dimension_stats[dim]['frequency'] += 1
                if extraction_date:
                    dimension_stats[dim]['dates'].append(extraction_date)
                    if dimension_stats[dim]['first_seen'] is None or extraction_date < dimension_stats[dim]['first_seen']:
                        dimension_stats[dim]['first_seen'] = extraction_date
                    if dimension_stats[dim]['last_seen'] is None or extraction_date > dimension_stats[dim]['last_seen']:
                        dimension_stats[dim]['last_seen'] = extraction_date
    
    result = {}
    for dim, stats in dimension_stats.items():
        result[dim] = {
            'frequency': stats['frequency'],
            'frequency_rate': stats['frequency'] / total_extractions if total_extractions > 0 else 0.0,
            'first_seen': stats['first_seen'].strftime("%Y-%m-%d") if stats['first_seen'] else None,
            'last_seen': stats['last_seen'].strftime("%Y-%m-%d") if stats['last_seen'] else None,
        }
    
    return result


def analyze_theme_dimension_match(themes: List[str], extraction_results: List[Dict], days_window: int = 30) -> Dict[str, Dict]:
    """Степень совпадения themes с измерениями"""
    now = datetime.now()
    
    recent_results = []
    for result in extraction_results:
        extraction_date_str = result.get('extraction_date', result.get('report_date', ''))
        extraction_date = parse_date(extraction_date_str.split('T')[0])
        if extraction_date:
            days_diff = (now - extraction_date).days
            if days_diff <= days_window:
                recent_results.append(result)
    
    theme_match = {}
    
    for theme in themes:
        match_count = 0
        total_count = len(recent_results)
        
        for result in recent_results:
            dimensions = result.get('dimensions', [])
            if theme in dimensions:
                match_count += 1
        
        match_rate = match_count / total_count if total_count > 0 else 0.0
        
        last_match_date = None
        for result in recent_results:
            dimensions = result.get('dimensions', [])
            if theme in dimensions:
                extraction_date_str = result.get('extraction_date', result.get('report_date', ''))
                extraction_date = parse_date(extraction_date_str.split('T')[0])
                if extraction_date:
                    if last_match_date is None or extraction_date > last_match_date:
                        last_match_date = extraction_date
        
        theme_match[theme] = {
            'match_rate': match_rate,
            'match_count': match_count,
            'total_count': total_count,
            'last_match_date': last_match_date.strftime("%Y-%m-%d") if last_match_date else None,
            'days_without_match': (now - last_match_date).days if last_match_date else days_window
        }
    
    return theme_match


def suggest_add_themes(dim_stats: Dict[str, Dict], themes: List[str], threshold_frequency: float = 0.5, min_recent_count: int = 3, days_window: int = 30) -> List[Dict]:
    """Рекомендация добавить themes (есть в измерениях, нет в themes)"""
    suggestions = []
    now = datetime.now()
    
    for dim, stats in dim_stats.items():
        if dim not in themes:
            frequency_rate = stats.get('frequency_rate', 0.0)
            last_seen_str = stats.get('last_seen')
            
            recent_count = 0
            if last_seen_str:
                last_seen = parse_date(last_seen_str)
                if last_seen:
                    days_diff = (now - last_seen).days
                    if days_diff <= days_window:
                        recent_count = int(frequency_rate * (days_window / 7))
            
            if frequency_rate >= threshold_frequency and recent_count >= min_recent_count:
                suggestions.append({
                    "suggestion_id": f"add_theme_{dim}_{datetime.now().strftime('%Y%m%d')}",
                    "type": "add_theme",
                    "theme": dim,
                    "reason": f"Измерение '{dim}': частота {frequency_rate*100:.1f}%, за {days_window} дней — {recent_count} раз",
                    "source_dimensions": [dim],
                    "frequency": frequency_rate,
                    "recent_count": recent_count
                })
    
    return suggestions


def suggest_remove_themes(theme_match: Dict[str, Dict], threshold_frequency: float = 0.1, min_days: int = 60) -> List[Dict]:
    """Рекомендация удалить themes (долго не совпадают с измерениями)"""
    suggestions = []
    
    for theme, match_info in theme_match.items():
        match_rate = match_info.get('match_rate', 0.0)
        days_without_match = match_info.get('days_without_match', 0)
        
        if match_rate < threshold_frequency and days_without_match >= min_days:
            suggestions.append({
                "suggestion_id": f"remove_theme_{theme}_{datetime.now().strftime('%Y%m%d')}",
                "type": "remove_theme",
                "theme": theme,
                "reason": f"За {min_days} дней '{theme}' совпал с измерениями в {match_rate*100:.1f}% случаев, без совпадений {days_without_match} дней",
                "match_rate": match_rate,
                "days_without_match": days_without_match
            })
    
    return suggestions


def generate_theme_suggestions(extraction_results: List[Dict], themes: List[str]) -> Dict[str, List[Dict]]:
    """Рекомендации по корректировке themes"""
    dim_stats = count_dimension_frequency_from_extractions(extraction_results)
    theme_match = analyze_theme_dimension_match(themes, extraction_results, days_window=30)
    
    add_suggestions = suggest_add_themes(dim_stats, themes, threshold_frequency=0.5, min_recent_count=3, days_window=30)
    remove_suggestions = suggest_remove_themes(theme_match, threshold_frequency=0.1, min_days=60)
    
    return {
        "add": add_suggestions,
        "remove": remove_suggestions,
        "theme_match_analysis": theme_match
    }


# ==================== Управление конфигурацией ====================

def load_dimension_config(config_file: Path) -> Dict:
    """Загрузка конфигурации измерений"""
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Ошибка загрузки конфигурации: {e}")
    
    return {
        "active_dimensions": [],
        "candidate_dimensions": [],
        "removed_dimensions": []
    }


def save_dimension_config(config_file: Path, config: Dict):
    """Сохранение конфигурации измерений"""
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_dimension_history(history_file: Path) -> List[Dict]:
    """Загрузка истории измерений"""
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('history', [])
        except Exception as e:
            print(f"⚠️  Ошибка загрузки истории: {e}")
    
    return []


def save_dimension_history(history_file: Path, history: List[Dict]):
    """Сохранение истории измерений"""
    history_file.parent.mkdir(parents=True, exist_ok=True)
    data = {"history": history}
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def record_dimension_event(event_type: str, dimension: str, timestamp: str = None, metadata: Dict = None) -> Dict:
    """Запись события измерения (ADD/REMOVE/PRIORITY_CHANGE)"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d")
    
    event = {
        "date": timestamp,
        "event": event_type,
        "dimension": dimension
    }
    
    if metadata:
        event.update(metadata)
    
    return event


# ==================== Взаимодействие с пользователем ====================

def present_suggestions(suggestions: Dict[str, List[Dict]]) -> None:
    """Вывод рекомендаций пользователю (текст)"""
    print("\n" + "=" * 70)
    print("📋 Рекомендации по корректировке измерений")
    print("=" * 70)
    
    all_count = sum(len(v) for v in suggestions.values())
    if all_count == 0:
        print("✅ Рекомендаций нет")
        return
    
    if suggestions.get('add'):
        print("\n【Добавить измерение】")
        for i, sug in enumerate(suggestions['add'], 1):
            print(f"  {i}. {sug['dimension']}")
            print(f"     Причина: {sug['reason']}")
            print(f"     Рекомендуемый приоритет: {sug['suggested_priority']}")
    
    if suggestions.get('remove'):
        print("\n【Удалить измерение】")
        for i, sug in enumerate(suggestions['remove'], 1):
            print(f"  {i}. {sug['dimension']}")
            print(f"     Причина: {sug['reason']}")
    
    if suggestions.get('priority_adjustment'):
        print("\n【Корректировка приоритета】")
        for i, sug in enumerate(suggestions['priority_adjustment'], 1):
            print(f"  {i}. {sug['dimension']}")
            print(f"     Причина: {sug['reason']}")
            print(f"     Текущий приоритет: {sug['current_priority']:.2f} → рекомендуется: {sug['suggested_priority']:.2f}")
    
    print("\n" + "=" * 70)


def get_user_confirmation(suggestion: Dict) -> str:
    """Подтверждение пользователя (принять/отклонить)"""
    print(f"\nРекомендация: {suggestion['recommendation']}")
    print(f"Измерение: {suggestion['dimension']}")
    print(f"Причина: {suggestion['reason']}")
    
    while True:
        user_input = input("Принять (y) / отклонить (n): ").strip().lower()
если user_input в ['y', 'да', 'Да', 'Принять']:
            return 'accepted'
elif user_input в ['n', 'нет', 'нет', 'отклонить']:
            return 'rejected'
        else:
            print("⚠️  Введите y или n")


def format_history_text(history: List[Dict]) -> str:
    """Форматирование истории в текст"""
    if not history:
        return "История пуста"
    
    lines = ["История эволюции измерений:"]
    lines.append("-" * 70)
    
    for event in history:
        date = event.get('date', '')
        event_type = event.get('event', '')
        dimension = event.get('dimension', '')
        
        if event_type == "ADD":
            info = "добавлено измерение"
        elif event_type == "REMOVE":
            info = "удалено измерение"
        elif event_type == "PRIORITY_CHANGE":
            old_priority = event.get('old_priority', '')
            new_priority = event.get('new_priority', '')
            info = f"изменение приоритета: {old_priority} → {new_priority}"
        else:
            info = event_type
        
        lines.append(f"{date} | {event_type} | {dimension} | {info}")
    
    return "\n".join(lines)
