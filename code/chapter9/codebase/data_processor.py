"""
Модуль обработки данных
Для обработки и преобразования данных
"""

import pandas as pd
from typing import List, Dict, Any


def process_data(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Обработка необработанных данных и возврат DataFrame
    
    Аргументы:
        данные: исходный список данных
        
    Возврат:
        Обработанный фрейм данных
    """
    # TODO: Добавить логику проверки данных
    df = pd.DataFrame(data)
    df = clean_data(df)
    df = transform_data(df)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Очистка нулевых значений и выбросов в данных
    
    Аргументы:
        df: исходный DataFrame
        
    Возврат:
        Очищенный фрейм данных
    """
    # TODO: реализовать более сложную логику очистки
    df = df.dropna()
    df = df.drop_duplicates()
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Преобразование формата данных
    
    Аргументы:
        df: inputDataFrame
        
    Возврат:
        Преобразованный фрейм данных
    """
    # ЗАДАЧА: Добавить дополнительные правила конверсии
    df['processed_date'] = pd.to_datetime(df['date'])
    return df


def aggregate_data(df: pd.DataFrame, group_by: List[str]) -> pd.DataFrame:
    """
    Совокупные данные
    
    Аргументы:
        df: inputDataFrame
        group_by: список полей группировки
        
    Возврат:
        Агрегированный фрейм данных
    """
    return df.groupby(group_by).agg({
        'value': ['sum', 'mean', 'count']
    })


def export_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Экспортировать данные в файл
    
    Аргументы:
        df: DataFrame для экспорта.
        выходной_путь: путь к выходному файлу
    """
    # TODO: Поддержка большего количества выходных форматов
    df.to_csv(output_path, index=False)
    print(f"Data exported to {output_path}")

