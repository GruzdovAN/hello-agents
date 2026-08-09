"""
Функциональный модуль инструмента
Обеспечить часто используемые вспомогательные функции
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Загрузить файл конфигурации
    
    Аргументы:
        config_path: путь к файлу конфигурации
        
    Возврат:
        Словарь конфигурации
    """
    # TODO: поддержка нескольких форматов файлов конфигурации.
    with open(config_path, 'r') as f:
        return json.load(f)


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Сохраняем конфигурацию в файл
    
    Аргументы:
        config: словарь конфигурации
        config_path: путь к файлу конфигурации
    """
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def get_timestamp() -> str:
    """
    Получить текущую временную метку
    
    Возврат:
        Строка временной метки в формате ISO
    """
    return datetime.now().isoformat()


def ensure_dir(directory: str) -> None:
    """
    Убедитесь, что каталог существует, создайте его, если он не существует.
    
    Аргументы:
        каталог: путь к каталогу
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def format_size(size_bytes: int) -> str:
    """
    Размер файла формата
    
    Аргументы:
        size_bytes: количество байтов
        
    Возврат:
        Форматированная строка размера
    """
    # ЗАДАЧА: Оптимизировать логику форматирования
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def validate_email(email: str) -> bool:
    """
    Проверьте формат адреса электронной почты
    
    Аргументы:
        электронная почта: адрес электронной почты
        
    Возврат:
        Это действительно?
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

