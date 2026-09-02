# data_exploration.py
import os
import numpy as np
import pandas as pd
from hello_agents import ToolRegistry

# Загрузка набора данных
work_path = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(f"{work_path}/../data/shopping_behavior_updated.csv")

def get_basic_metadata(input: str) -> dict:
    """Получение базовых метаданных"""
    metadata = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "memory_usage": df.memory_usage(deep=True).sum()
    }
    return metadata

def assess_data_quality(input: str) -> dict:
    """Комплексная оценка качества данных"""
    quality_report = {
        "completeness": {},
        "consistency": {},
        "validity": {},
        "anomalies": {}
    }

    for col in df.columns:
        # Полнота
        missing_rate = df[col].isna().mean()
        quality_report["completeness"][col] = {
            "missing_rate": missing_rate,
            "level": "high" if missing_rate < 0.05 else "medium" if missing_rate < 0.2 else "low"
        }

        # Валидность (на основе типа данных)
        if pd.api.types.is_numeric_dtype(df[col]):
            # Проверка числовых значений
            quality_report["anomalies"][col] = {
                "min": float(df[col].min()),
                "max": float(df[col].max())
            }
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            # Проверка временных значений
            future_dates = df[col] > pd.Timestamp.now()
            quality_report["validity"][col] = {
                "future_dates_count": future_dates.sum(),
                "date_range": [df[col].min().strftime('%Y-%m-%d'),
                              df[col].max().strftime('%Y-%m-%d')]
            }

    return quality_report

def get_statistical_summary(input: str) -> dict:
    """Сводка основной статистики по данным"""
    summary = {}

    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        summary[col] = {
            "basic": {
                "count": int(series.count()),
                "mean": float(series.mean()),
                "std": float(series.std()),
                "min": float(series.min()),
                "25%": float(series.quantile(0.25)),
                "50%": float(series.quantile(0.50)),
                "75%": float(series.quantile(0.75)),
                "max": float(series.max())
            },
            "advanced": {
                "skewness": float(series.skew()),
                "kurtosis": float(series.kurtosis()),
                "cv": float(series.std() / series.mean()) if series.mean() != 0 else None,
                "zeros_count": int((series == 0).sum()),
                "negative_count": int((series < 0).sum())
            }
        }

    return summary

def create_data_exploration_registry():
    """Создание реестра инструментов разведки данных"""
    registry = ToolRegistry()

    # Регистрация функции получения базовых метаданных
    registry.register_function(
        name="get_basic_metadata",
        description="Получение базовых метаданных: размер, имена столбцов, типы данных и использование памяти",
        func=get_basic_metadata
    )

    # Регистрация функции оценки качества данных
    registry.register_function(
        name="assess_data_quality",
        description="Комплексная оценка качества данных: полнота, согласованность, валидность и обнаружение аномалий",
        func=assess_data_quality
    )

    # Регистрация функции статистической сводки
    registry.register_function(
        name="get_statistical_summary",
        description="Получение основной статистической сводки по числовым столбцам, включая базовые и расширенные показатели",
        func=get_statistical_summary
    )

    return registry

if __name__ == "__main__":
    registry = create_data_exploration_registry()
    result = registry.execute_tool("get_basic_metadata", input_text=None)
    print(result)
