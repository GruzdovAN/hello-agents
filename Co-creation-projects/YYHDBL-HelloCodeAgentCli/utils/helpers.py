"""Вспомогательные утилиты"""

import importlib
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

def format_time(timestamp: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Форматирует время
    
    Args:
        timestamp: Метка времени; по умолчанию — текущее время
        format_str: Строка формата
        
    Returns:
        Отформатированная строка времени
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime(format_str)

def validate_config(config: Dict[str, Any], required_keys: list) -> bool:
    """
    Проверяет, что конфигурация содержит обязательные ключи
    
    Args:
        config: Словарь конфигурации
        required_keys: Список обязательных ключей
        
    Returns:
        True, если проверка пройдена
    """
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"В конфигурации отсутствуют обязательные ключи: {missing_keys}")
    return True

def safe_import(module_name: str, class_name: Optional[str] = None) -> Any:
    """
    Безопасно импортирует модуль или класс
    
    Args:
        module_name: Имя модуля
        class_name: Имя класса (необязательно)
        
    Returns:
        Импортированный модуль или класс
    """
    try:
        module = importlib.import_module(module_name)
        if class_name:
            return getattr(module, class_name)
        return module
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Не удалось импортировать {module_name}.{class_name or ''}: {e}")

def ensure_dir(path: Path) -> Path:
    """Гарантирует существование каталога"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_project_root() -> Path:
    """Возвращает корень проекта"""
    return Path(__file__).parent.parent.parent

def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Глубоко объединяет два словаря"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
