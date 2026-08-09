import asyncio
from hello_agents.protocols import MCPClient

async def connect_to_server():
    # Способ 1. Подключитесь к серверу файловой системы, предоставленному сообществом.
    # npx автоматически загрузит и запустит пакет @modelcontextprotocol/server-filesystem.
    client = MCPClient([
        "npx", "-y",
        "@modelcontextprotocol/server-filesystem",
        "."  # Укажите корневой каталог
    ])

    # Используйте async, чтобы убедиться, что соединение закрывается правильно.
    async with client:
        # Используйте клиент здесь
        tools = await client.list_tools()
        print(f"Доступные инструменты: {[t['name'] для t в инструментах]}")

    # Способ 2. Подключитесь к пользовательскому серверу Python MCP.
    client = MCPClient(["python", "my_mcp_server.py"])
    async with client:
        # Используйте клиент...
        pass

# Запустите асинхронную функцию
asyncio.run(connect_to_server())


async def discover_tools():
    client = MCPClient(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

    async with client:
        # Получите все доступные инструменты
        tools = await client.list_tools()

        print(f"Сервер предоставляет инструменты {len(tools)}:")
        for tool in tools:
            print(f"\nИмя инструмента: {инструмент['name']}")
            print(f"Описание: {tool.get('description', 'Нет описания')}")

            # Распечатать информацию о параметрах
            if 'inputSchema' in tool:
                schema = tool['inputSchema']
                if 'properties' in schema:
                    print("параметр:")
                    for param_name, param_info in schema['properties'].items():
                        param_type = param_info.get('type', 'any')
                        param_desc = param_info.get('description', '')
                        print(f"  - {param_name} ({param_type}): {param_desc}")

asyncio.run(discover_tools())

# Пример вывода:
# Сервер предоставляет 5 инструментов:
#
# Имя инструмента: read_file
# Описание: Чтение содержимого файла.
# параметр:
#   - путь (строка): путь к файлу
#
# Имя инструмента: write_file
# Описание: Запись содержимого файла.
# параметр:
#   - путь (строка): путь к файлу
#   - content (строка): содержимое файла


async def use_tools():
    client = MCPClient(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

    async with client:
        # прочитать файл
        result = await client.call_tool("read_file", {"path": "my_README.md"})
        print(f"Содержимое файла:\n{результат}")

        # список каталогов
        result = await client.call_tool("list_directory", {"path": "."})
        print(f"Текущий файл каталога: {result}")

        # записать файл
        result = await client.call_tool("write_file", {
            "path": "output.txt",
            "content": "Hello from MCP!"
        })
        print(f"Написать результат: {result}")

asyncio.run(use_tools())

async def safe_tool_call():
    client = MCPClient(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

    async with client:
        try:
            # Попытка прочитать файл, который может не существовать
            result = await client.call_tool("read_file", {"path": "nonexistent.txt"})
            print(result)
        except Exception as e:
            print(f"Не удалось вызвать инструмент: {e}")
            # Возможность повторить попытку, использовать значения по умолчанию или сообщить пользователю об ошибках.

asyncio.run(safe_tool_call())
