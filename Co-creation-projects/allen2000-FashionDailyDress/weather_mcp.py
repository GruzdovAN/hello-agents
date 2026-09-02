"""
Пример пользовательского MCP-сервера

Простой MCP-сервер для запроса погодной информации.
Демонстрирует создание собственного MCP-сервера.

Запуск:
    python my_mcp_server.py

Или как MCP-сервер, вызываемый клиентом:
    MCPClient(["python", "weather_mcp.py"])
"""
from fastmcp import FastMCP
from weather import Weather
# Создание экземпляра MCP-сервера
mcp = FastMCP("WeatherServer")


# ==================== Инструменты погоды ====================

@mcp.tool()
def query_wearher(city_name: str):
    """
    Запрос погоды

    Args:
        city_name: название города

    Returns:
        погодная информация
    """
    weather = Weather()
    # Запрос подробной погоды (формат словаря)
    weather_details = weather.get_weather_details(city_name)
    
    # При успешном запросе — подробные данные
    if "error" not in weather_details:
        return weather_details
    else:
        # При ошибке — отформатированная строка
        return weather.get_weather(city_name)

@mcp.tool()
def get_weather_details(city_name: str):
    """
    Получить подробные погодные данные (структурированный формат)

    Args:
        city_name: название города

    Returns:
        словарь с подробными погодными данными
    """
    weather = Weather()
    return weather.get_weather_details(city_name)

@mcp.resource("info://capabilities")
def get_capabilities() -> str:
    """
    Получить список возможностей сервера

    Returns:
        текстовое описание списка возможностей
    """
    capabilities = """
Список возможностей сервера:

Возможности запроса погоды:
- query_weather: получить погоду для указанного города (структурированные данные)
- get_weather_details: получить подробные погодные данные (формат словаря)
"""
    return capabilities.strip()


# ==================== Шаблоны промптов ====================

@mcp.prompt()
def weather_helper() -> str:
    """
    Промпт для запроса погодной информации

    Returns:
        шаблон промпта
    """
    return """Вы помощник по запросу погоды. Вы можете использовать следующие инструменты:
- query_weather(city_name): получить погоду для указанного города

Выберите подходящий инструмент в зависимости от вопроса пользователя."""


# ==================== Главная программа ====================

if __name__ == "__main__":
    # Запуск MCP-сервера
    # FastMCP автоматически обрабатывает stdio-транспорт
    mcp.run()
