#!/usr/bin/env python3
"""Тестовый сервер MCP запроса погоды"""

import asyncio
import json
import os
from hello_agents.protocols import MCPClient


async def test_weather_server():
    server_script = os.path.join(os.path.dirname(__file__), "14_weather_mcp_server.py")
    client = MCPClient(["python", server_script])

    try:
        async with client:
            # Тест 1. Получите информацию о сервере
            info = json.loads(await client.call_tool("get_server_info", {}))
            print(f"Сервер: {info['name']} v{info['version']}")

            # Тест 2. Список поддерживаемых городов.
            cities = json.loads(await client.call_tool("list_supported_cities", {}))
            print(f"Поддерживаемые города: {cities['count']}")

            # Тест 3: Проверьте погоду в Пекине
            weather = json.loads(await client.call_tool("get_weather", {"city": "Пекин"}))
            if "error" not in weather:
                print(f"\nПогода в Пекине: {weather['temperature']}°C, {weather['condition']}")

            # Тест 4: Проверьте погоду в Шэньчжэне
            weather = json.loads(await client.call_tool("get_weather", {"city": "Шэньчжэнь"}))
            if "error" not in weather:
                print(f"Погода в Шэньчжэне: {weather['temperature']}°C, {weather['condition']}")

            print("\n✅ Все тесты пройдены!")

    except Exception as e:
        print(f"❌ Тест не пройден: {e}")


if __name__ == "__main__":
    asyncio.run(test_weather_server())