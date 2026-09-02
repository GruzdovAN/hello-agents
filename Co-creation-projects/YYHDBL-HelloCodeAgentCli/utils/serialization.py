"""Утилиты сериализации"""

import json
import pickle
from typing import Any, Union
from pathlib import Path

def serialize_object(obj: Any, format: str = "json") -> Union[str, bytes]:
    """
    Сериализует объект
    
    Args:
        obj: Объект для сериализации
        format: Формат сериализации ("json" или "pickle")
        
    Returns:
        Сериализованные данные
    """
    if format == "json":
        return json.dumps(obj, ensure_ascii=False, indent=2)
    elif format == "pickle":
        return pickle.dumps(obj)
    else:
        raise ValueError(f"Неподдерживаемый формат сериализации: {format}")

def deserialize_object(data: Union[str, bytes], format: str = "json") -> Any:
    """
    Десериализует объект
    
    Args:
        data: Сериализованные данные
        format: Формат сериализации
        
    Returns:
        Десериализованный объект
    """
    if format == "json":
        return json.loads(data)
    elif format == "pickle":
        return pickle.loads(data)
    else:
        raise ValueError(f"Неподдерживаемый формат десериализации: {format}")

def save_to_file(obj: Any, filepath: Union[str, Path], format: str = "json") -> None:
    """Сохраняет объект в файл"""
    filepath = Path(filepath)
    data = serialize_object(obj, format)
    
    mode = "w" if format == "json" else "wb"
    with open(filepath, mode) as f:
        f.write(data)

def load_from_file(filepath: Union[str, Path], format: str = "json") -> Any:
    """Загружает объект из файла"""
    filepath = Path(filepath)
    mode = "r" if format == "json" else "rb"
    
    with open(filepath, mode) as f:
        data = f.read()
    
    return deserialize_object(data, format)
