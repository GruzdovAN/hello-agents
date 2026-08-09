# Weather MCP Server

MCP-сервер запроса реальной погоды, разработанный на основе платформы HelloAgents.

## Функции

- 🌤️ Запрос погоды в режиме реального времени
- 🌍 Поддерживает 12 крупных городов Китая
- 🔄 Используйте API wttr.in (ключ не требуется)
- 🚀 На основе платформы HelloAgents.

## Установить

```bash
pip install hello-agents requests
```

## Как использовать

### Запускать напрямую

```bash
python server.py
```

### Используется в Claude Desktop

Отредактируйте `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) или `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

### Используется в HelloAgents

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool

agent = SimpleAgent(name="Помощник погоды", llm=HelloAgentsLLM())
weather_tool = MCPTool(server_command=["python", "server.py"])
agent.add_tool(weather_tool)

response = Agent.run("Какая сегодня погода в Пекине?")
```

## Инструменты API

### get_weather

Получить текущую погоду для указанного города.

**Параметры:**
- `city` (строка): название города (поддерживается китайский и английский языки).

**Пример:**```json
{
  «город»: «Пекин»
}
```

**возвращаться:**```json
{
  «город»: «Пекин»,
  "temperature": 10.0,
  "feels_like": 9.0,
  "humidity": 94,
  "condition": "Light rain",
  "wind_speed": 1.7,
  "visibility": 10.0,
  "timestamp": "2025-10-09 13:25:03"
}
```

### list_supported_cities

Список всех поддерживаемых китайских городов.

**возвращаться:**```json
{
  "города": ["Пекин", "Шанхай", "Гуанчжоу", "Шэньчжэнь", "Ханчжоу", "Чэнду", "Чунцин", "Ухань", "Сиань", "Нанкин", "Тяньцзинь", "Сучжоу"],
  "count": 12
}
```

### get_server_info

Получите информацию о сервере.

**возвращаться:**```json
{
  "name": "Weather MCP Server",
  "version": "1.0.0",
  "tools": ["get_weather", "list_supported_cities", "get_server_info"]
}
```

## Поддерживаемые города

Пекин, Шанхай, Гуанчжоу, Шэньчжэнь, Ханчжоу, Чэнду, Чунцин, Ухань, Сиань, Нанкин, Тяньцзинь, Сучжоу

Он также поддерживает использование названий городов на английском языке для запроса любого города в мире.

## Лицензия

MIT License

## автор

HelloAgents Team

