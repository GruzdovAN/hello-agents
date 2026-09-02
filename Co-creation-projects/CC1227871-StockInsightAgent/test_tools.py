"""Быстрая проверка: проверьте каждую функцию инструмента индивидуально"""
from tools import get_realtime_quote, get_historical_data, get_financial_data, calc_indicators, get_news

if __name__ == "__main__":
    print("=" * 60)
print("Тест 1: Котировки в реальном времени")
    print("=" * 60)
    print(get_realtime_quote("600519"))

    print("\n" + "=" * 60)
print("Тест 2: Историческая K-линия")
    print("=" * 60)
    print(get_historical_data("600519|daily|10"))

    print("\n" + "=" * 60)
print("Тест 3: Технические индикаторы")
    print("=" * 60)
    print(calc_indicators("600519|daily|60"))

    print("\n" + "=" * 60)
print("Тест 4: Финансовые данные")
    print("=" * 60)
    print(get_financial_data("600519"))

    print("\n" + "=" * 60)
print("Тест 5: Новости")
    print("=" * 60)
    print(get_news("600519"))

print("\nВсе тестирование инструмента завершено!")
