"""
Коллекция инструментов протокола

Интерфейсы на основе протоколов:
- MCP Tool: библиотека fastmcp, подключение и вызов MCP-сервера
- A2A Tool: официальная библиотека a2a для связи между агентами (нужна установка a2a)
- ANP Tool: концептуальная реализация обнаружения сервисов и управления сетью
"""

from typing import Dict, Any, List, Optional
from ..base import Tool, ToolParameter
import os

# todo: изменено xc
import gc
import asyncio
import sys
if sys.platform == "win32":
    # Windows 10+: SelectorEventLoop вместо ProactorEventLoop,
    # избегает блокировки GetQueuedCompletionStatus
    if sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )
        

# Таблица переменных окружения MCP-серверов
# для автоопределения нужных переменных
MCP_SERVER_ENV_MAP = {
    "server-github": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "server-slack": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
    "server-google-drive": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"],
    "server-postgres": ["POSTGRES_CONNECTION_STRING"],
    "server-sqlite": [],  # переменные окружения не нужны
    "server-filesystem": [],  # переменные окружения не нужны
}


class MCPTool(Tool):
    """Инструмент MCP (Model Context Protocol)

    Подключение к MCP-серверу и вызов его инструментов, ресурсов и промптов.
    
    Возможности:
    - Список инструментов сервера
    - Вызов инструментов сервера
    - Чтение ресурсов сервера
    - Получение шаблонов промптов

    Примеры:
        >>> from hello_agents.tools.builtin import MCPTool
        >>>
        >>> # Способ 1: встроенный демо-сервер
        >>> tool = MCPTool()  # автоматически создаёт встроенный сервер
        >>> result = tool.run({"action": "list_tools"})
        >>>
        >>> # Способ 2: подключение к внешнему MCP-серверу
        >>> tool = MCPTool(server_command=["python", "examples/mcp_example.py"])
        >>> result = tool.run({"action": "list_tools"})
        >>>
        >>> # Способ 3: пользовательский сервер FastMCP
        >>> from fastmcp import FastMCP
        >>> server = FastMCP("MyServer")
        >>> tool = MCPTool(server=server)

    Примечание: используется библиотека fastmcp из зависимостей
    """
    
    def __init__(self,
                 name: str = "mcp",
                 description: Optional[str] = None,
                 server_command: Optional[List[str]] = None,
                 server_args: Optional[List[str]] = None,
                 server: Optional[Any] = None,
                 auto_expand: bool = True,
                 env: Optional[Dict[str, str]] = None,
                 env_keys: Optional[List[str]] = None):
        """
        Инициализация инструмента MCP

        Args:
            name: имя инструмента (по умолчанию "mcp", для разных серверов — разные имена)
            description: описание инструмента (опционально)
            server_command: команда запуска сервера (например ["python", "server.py"])
            server_args: список аргументов сервера
            server: экземпляр FastMCP (опционально, для in-memory транспорта)
            auto_expand: автоматически разворачивать в отдельные инструменты (по умолчанию True)
            env: словарь переменных окружения (наивысший приоритет)
            env_keys: список ключей для загрузки из системного окружения

        Приоритет переменных окружения (от высокого к низкому):
            1. Параметр env, переданный напрямую
            2. Переменные из env_keys
            3. Автоопределение по server_command

        Если все параметры пусты, создаётся встроенный демо-сервер

        Примеры:
            >>> # Способ 1: прямая передача env (наивысший приоритет)
            >>> github_tool = MCPTool(
            ...     name="github",
            ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"],
            ...     env={"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"}
            ... )
            >>>
            >>> # Способ 2: загрузка env_keys из .env
            >>> github_tool = MCPTool(
            ...     name="github",
            ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"],
            ...     env_keys=["GITHUB_PERSONAL_ACCESS_TOKEN"]
            ... )
            >>>
            >>> # Способ 3: автоопределение (проще всего, рекомендуется)
            >>> github_tool = MCPTool(
            ...     name="github",
            ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
            ...     # автозагрузка GITHUB_PERSONAL_ACCESS_TOKEN из окружения
            ... )
        """
        self.server_command = server_command
        self.server_args = server_args or []
        self.server = server
        self._client = None
        self._available_tools = []
        self.auto_expand = auto_expand
        self.prefix = f"{name}_" if auto_expand else ""

        # Обработка env (приоритет: env > env_keys > автоопределение)
        self.env = self._prepare_env(env, env_keys, server_command)

        # Если сервер не указан — встроенный демо-сервер
        if not server_command and not server:
            self.server = self._create_builtin_server()

        # Автообнаружение инструментов
        self._discover_tools()

        # Описание по умолчанию или автогенерация
        if description is None:
            description = self._generate_description()

        super().__init__(
            name=name,
            description=description
        )

    def _prepare_env(self,
                     env: Optional[Dict[str, str]],
                     env_keys: Optional[List[str]],
                     server_command: Optional[List[str]]) -> Dict[str, str]:
        """
        Подготовка переменных окружения

        Приоритет: env > env_keys > автоопределение

        Args:
            env: словарь env, переданный напрямую
            env_keys: ключи для загрузки из системного окружения
            server_command: команда сервера (для автоопределения)

        Returns:
            объединённый словарь переменных окружения
        """
        result_env = {}

        # 1. Автоопределение (низший приоритет)
        if server_command:
            # Извлечь имя сервера из команды
            server_name = None
            for part in server_command:
                if "server-" in part:
                    # Извлечь "server-github" из "@modelcontextprotocol/server-github"
                    server_name = part.split("/")[-1] if "/" in part else part
                    break

            # Поиск в таблице сопоставления
            if server_name and server_name in MCP_SERVER_ENV_MAP:
                auto_keys = MCP_SERVER_ENV_MAP[server_name]
                for key in auto_keys:
                    value = os.getenv(key)
                    if value:
                        result_env[key] = value
                        print(f"🔑 Автозагрузка переменной окружения: {key}")

        # 2. Переменные из env_keys (средний приоритет)
        if env_keys:
            for key in env_keys:
                value = os.getenv(key)
                if value:
                    result_env[key] = value
                    print(f"🔑 Загрузка переменной из env_keys: {key}")
                else:
                    print(f"⚠️  Предупреждение: переменная окружения {key} не задана")

        # 3. Прямой env (наивысший приоритет)
        if env:
            result_env.update(env)
            for key in env.keys():
                print(f"🔑 Используется напрямую переданная переменная: {key}")

        return result_env

    def _create_builtin_server(self):
        """Создать встроенный демо-сервер"""
        try:
            from fastmcp import FastMCP

            server = FastMCP("HelloAgents-BuiltinServer")

            @server.tool()
            def add(a: float, b: float) -> float:
                """Калькулятор сложения"""
                return a + b

            @server.tool()
            def subtract(a: float, b: float) -> float:
                """Калькулятор вычитания"""
                return a - b

            @server.tool()
            def multiply(a: float, b: float) -> float:
                """Калькулятор умножения"""
                return a * b

            @server.tool()
            def divide(a: float, b: float) -> float:
                """Калькулятор деления"""
                if b == 0:
                    raise ValueError("Делитель не может быть нулём")
                return a / b

            @server.tool()
            def greet(name: str = "World") -> str:
                """Приветствие"""
                return f"Hello, {name}! Добро пожаловать в инструмент HelloAgents MCP!"

            @server.tool()
            def get_system_info() -> dict:
                """Получить системную информацию"""
                import platform
                import sys
                return {
                    "platform": platform.system(),
                    "python_version": sys.version,
                    "server_name": "HelloAgents-BuiltinServer",
                    "tools_count": 6
                }

            return server

        except ImportError:
            raise ImportError(
                "Для встроенного MCP-сервера нужна fastmcp. Установите: pip install fastmcp"
            )

    def _discover_tools(self):
        """Обнаружить все инструменты MCP-сервера"""
        try:
            from hello_agents.protocols.mcp.client import MCPClient
            import asyncio

            async def discover():
                client_source = self.server if self.server else self.server_command
                async with MCPClient(client_source, self.server_args, env=self.env) as client:
                    tools = await client.list_tools()
                    return tools

            # Асинхронное обнаружение
            try:
                loop = asyncio.get_running_loop()
                # При существующем цикле — в новом потоке
                import concurrent.futures
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(discover())
                    finally:
                        new_loop.close()

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    self._available_tools = future.result()
            except RuntimeError:
                # Нет активного цикла событий
                self._available_tools = asyncio.run(discover())

        except Exception as e:
            # Сбой обнаружения не блокирует инициализацию
            self._available_tools = []

    def _generate_description(self) -> str:
        """Сгенерировать расширенное описание инструмента"""
        if not self._available_tools:
            return "Подключение к MCP-серверу: вызов инструментов, чтение ресурсов и промптов. Встроенный и внешний сервер."

        if self.auto_expand:
            # Режим развёртывания: краткое описание
            return f"MCP-сервер с {len(self._available_tools)} инструментами. Они автоматически разворачиваются в отдельные инструменты для агента."
        else:
            # Без развёртывания: подробное описание
            desc_parts = [
                f"MCP-сервер, {len(self._available_tools)} инструментов:"
            ]

            # Перечислить все инструменты
            for tool in self._available_tools:
                tool_name = tool.get('name', 'unknown')
                tool_desc = tool.get('description', 'без описания')
                # Упростить описание — первая фраза
                short_desc = tool_desc.split('.')[0] if tool_desc else 'без описания'
                desc_parts.append(f"  • {tool_name}: {short_desc}")

            # Формат вызова
            desc_parts.append("\nФормат вызова: параметры в JSON")
            desc_parts.append('{"action": "call_tool", "tool_name": "имя_инструмента", "arguments": {...}}')

            # Пример
            if self._available_tools:
                first_tool = self._available_tools[0]
                tool_name = first_tool.get('name', 'example')
                desc_parts.append(f'\nПримеры:{{"action": "call_tool", "tool_name": "{tool_name}", "arguments": {{...}}}}')

            return "\n".join(desc_parts)

    def get_expanded_tools(self) -> List['Tool']:  # type: ignore
        """
        Получить список развёрнутых инструментов

        Каждый инструмент MCP оборачивается в отдельный Tool

        Returns:
            список объектов Tool
        """
        if not self.auto_expand:
            return []

        from .mcp_wrapper_tool import MCPWrappedTool

        expanded_tools = []
        for tool_info in self._available_tools:
            wrapped_tool = MCPWrappedTool(
                mcp_tool=self,
                tool_info=tool_info,
                prefix=self.prefix
            )
            expanded_tools.append(wrapped_tool)

        return expanded_tools

    def run(self, parameters: Dict[str, Any]) -> str:
        """
        Выполнить операцию MCP

        Args:
            parameters: словарь с параметрами
                - action: тип операции (list_tools, call_tool, list_resources, read_resource, list_prompts, get_prompt)
                  без action, но с tool_name — автоматически call_tool
                - tool_name: имя инструмента (для call_tool)
                - arguments: аргументы (для call_tool)
                - uri: URI ресурса (для read_resource)
                - prompt_name: имя промпта (для get_prompt)
                - prompt_arguments: аргументы промпта (опционально)

        Returns:
            результат операции
        """
        from hello_agents.protocols.mcp.client import MCPClient

        timeout = getattr(self, 'timeout', 10)

        # Автовывод action: при tool_name без action — call_tool
        action = parameters.get("action", "").lower()
        if not action and "tool_name" in parameters:
            action = "call_tool"
            parameters["action"] = action

        if not action:
            return "Ошибка: укажите action или tool_name"
        
        try:
            # Асинхронный клиент
            import asyncio
            from hello_agents.protocols.mcp.client import MCPClient

            async def run_mcp_operation():
                # Способ создания клиента по конфигурации
                if self.server:
                    # Встроенный сервер (in-memory)
                    client_source = self.server
                else:
                    # Внешний сервер по команде
                    client_source = self.server_command

                async with MCPClient(client_source, self.server_args, env=self.env) as client:
                    if action == "list_tools":
                        tools = await client.list_tools()
                        if not tools:
                            return "Доступные инструменты не найдены"
                        result = f"Найдено {len(tools)} инструментов:\n"
                        for tool in tools:
                            result += f"- {tool['name']}: {tool['description']}\n"
                        return result

                    elif action == "call_tool":
                        tool_name = parameters.get("tool_name")
                        arguments = parameters.get("arguments", {})
                        if not tool_name:
                            return "Ошибка: укажите tool_name"
                        
                        # todo: изменено xc
                        result = await asyncio.wait_for(client.call_tool(tool_name, arguments), timeout=timeout)
                        # result = await client.call_tool(tool_name, arguments)
                        return f"Результат инструмента '{tool_name}':\n{result}"

                    elif action == "list_resources":
                        resources = await client.list_resources()
                        if not resources:
                            return "Доступные ресурсы не найдены"
                        result = f"Найдено {len(resources)} ресурсов:\n"
                        for resource in resources:
                            result += f"- {resource['uri']}: {resource['name']}\n"
                        return result

                    elif action == "read_resource":
                        uri = parameters.get("uri")
                        if not uri:
                            return "Ошибка: укажите uri"
                        content = await client.read_resource(uri)
                        return f"Содержимое ресурса '{uri}':\n{content}"

                    elif action == "list_prompts":
                        prompts = await client.list_prompts()
                        if not prompts:
                            return "Доступные промпты не найдены"
                        result = f"Найдено {len(prompts)} промптов:\n"
                        for prompt in prompts:
                            result += f"- {prompt['name']}: {prompt['description']}\n"
                        return result

                    elif action == "get_prompt":
                        prompt_name = parameters.get("prompt_name")
                        prompt_arguments = parameters.get("prompt_arguments", {})
                        if not prompt_name:
                            return "Ошибка: укажите prompt_name"
                        messages = await client.get_prompt(prompt_name, prompt_arguments)
                        result = f"Промпт '{prompt_name}':\n"
                        for msg in messages:
                            result += f"[{msg['role']}] {msg['content']}\n"
                        return result

                    else:
                        return f"Ошибка: неподдерживаемая операция '{action}'"

            # Асинхронное выполнение
            try:
                # Проверка активного цикла событий
                try:
                    loop = asyncio.get_running_loop()
                    # При активном цикле — новый цикл в отдельном потоке
                    import concurrent.futures
                    import threading

                    def run_in_thread():
                        # Новый цикл событий в потоке
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(run_mcp_operation())
                        finally:
                            # todo: изменено xc
                            # Ключевая очистка 1: отмена оставшихся задач
                            pending = asyncio.all_tasks(new_loop)
                            for task in pending:
                                task.cancel()
                            if pending:
                                new_loop.run_until_complete(
                                    asyncio.gather(*pending, return_exceptions=True)
                                )

                            new_loop.close()

                    # todo: изменено xc
                    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                    try:
                        future = executor.submit(run_in_thread)
                        # Ключевая очистка 2: таймаут против блокировки
                        return future.result(timeout=timeout)
                    finally:
                        # Ключевая очистка 3: закрытие пула без ожидания потоков
                        executor.shutdown(wait=False, cancel_futures=True)

                except RuntimeError:
                    # Нет активного цикла событий — прямой запуск
                    return asyncio.run(run_mcp_operation())
            except Exception as e:
                return f"Ошибка асинхронной операции: {str(e)}"
            finally:
                # todo: изменено xc
                # Ключевая очистка 4: сбор незакрытых дескрипторов
                gc.collect()

        except Exception as e:
            return f"Ошибка операции MCP: {str(e)}"
    
    def get_parameters(self) -> List[ToolParameter]:
        """Получить определение параметров инструмента"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Тип операции: list_tools, call_tool, list_resources, read_resource, list_prompts, get_prompt",
                required=True
            ),
            ToolParameter(
                name="tool_name",
                type="string",
                description="Имя инструмента (для call_tool)",
                required=False
            ),
            ToolParameter(
                name="arguments",
                type="object",
                description="Аргументы инструмента (для call_tool)",
                required=False
            ),
            ToolParameter(
                name="uri",
                type="string",
                description="URI ресурса (для read_resource)",
                required=False
            ),
            ToolParameter(
                name="prompt_name",
                type="string",
                description="Имя промпта (для get_prompt)",
                required=False
            ),
            ToolParameter(
                name="prompt_arguments",
                type="object",
                description="Аргументы промпта (для get_prompt, опционально)",
                required=False
            )
        ]


class A2ATool(Tool):
    """Инструмент A2A (Agent-to-Agent Protocol)

    Подключение к A2A-агенту и обмен сообщениями.
    
    Возможности:
    - Вопрос агенту
    - Информация об агенте
    - Пользовательское сообщение

    Примеры:
        >>> from hello_agents.tools.builtin import A2ATool
        >>> # Подключение к A2A-агенту (имя по умолчанию)
        >>> tool = A2ATool(agent_url="http://localhost:5000")
        >>> # Подключение с пользовательским именем и описанием
        >>> tool = A2ATool(
        ...     agent_url="http://localhost:5000",
        ...     name="tech_expert",
        ...     description="Технический эксперт для технических вопросов"
        ... )
        >>> # Вопрос
        >>> result = tool.run({"action": "ask", "question": "вычисли 2+2"})
        >>> # Получить информацию
        >>> result = tool.run({"action": "get_info"})
    
    Нужна официальная библиотека a2a-sdk: pip install a2a-sdk
    Документация: docs/chapter10/A2A_GUIDE.md
    Репозиторий: https://github.com/a2aproject/a2a-python
    """
    
    def __init__(self, agent_url: str, name: str = "a2a", description: str = None):
        """
        Инициализация инструмента A2A

        Args:
            agent_url: Agent URL
            name: имя инструмента (опционально, по умолчанию "a2a")
            description: описание (опционально)
        """
        if description is None:
            description = "Подключение к A2A-агенту: вопросы и информация. Нужна a2a-sdk."

        super().__init__(
            name=name,
            description=description
        )
        self.agent_url = agent_url
        
    def run(self, parameters: Dict[str, Any]) -> str:
        """
        Выполнить операцию A2A
        
        Args:
            parameters: словарь с параметрами
                - action: тип операции (ask, get_info)
                - question: текст вопроса (для ask)
        
        Returns:
            результат операции
        """
        try:
            from hello_agents.protocols.a2a.implementation import A2AClient, A2A_AVAILABLE
            if not A2A_AVAILABLE:
                return ("Ошибка: нужна библиотека a2a-sdk\n"
                       "Установка: pip install a2a-sdk\n"
                       "Документация: docs/chapter10/A2A_GUIDE.md\n"
                       "Репозиторий: https://github.com/a2aproject/a2a-python")
        except ImportError:
            return ("Ошибка: не удалось импортировать модуль A2A\n"
                   "Установка: pip install a2a-sdk\n"
                   "Документация: docs/chapter10/A2A_GUIDE.md\n"
                   "Репозиторий: https://github.com/a2aproject/a2a-python")

        action = parameters.get("action", "").lower()
        
        if not action:
            return "Ошибка: укажите action"
        
        try:
            client = A2AClient(self.agent_url)
            
            if action == "ask":
                question = parameters.get("question")
                if not question:
                    return "Ошибка: укажите question"
                response = client.ask(question)
                return f"Ответ агента:\n{response}"
                
            elif action == "get_info":
                info = client.get_info()
                result = "Информация об агенте:\n"
                for key, value in info.items():
                    result += f"- {key}: {value}\n"
                return result
                
            else:
                return f"Ошибка: неподдерживаемая операция '{action}'"
                
        except Exception as e:
            return f"Ошибка операции A2A: {str(e)}"
    
    def get_parameters(self) -> List[ToolParameter]:
        """Получить определение параметров инструмента"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Тип: ask (вопрос), get_info (информация)",
                required=True
            ),
            ToolParameter(
                name="question",
                type="string",
                description="Текст вопроса (для ask)",
                required=False
            )
        ]


class ANPTool(Tool):
    """Инструмент ANP (Agent Network Protocol)

    Управление сетью агентов: обнаружение сервисов, узлы и маршрутизация.
    Концептуальная реализация для демонстрации идей управления сетью агентов.
    
    Возможности:
    - Регистрация и обнаружение сервисов
    - Добавление и управление узлами
    - Маршрутизация сообщений
    - Статистика сети

    Примеры:
        >>> from hello_agents.tools.builtin import ANPTool
        >>> tool = ANPTool()
        >>> # Регистрация сервиса
        >>> result = tool.run({
        ...     "action": "register_service",
        ...     "service_id": "calc-1",
        ...     "service_type": "calculator",
        ...     "endpoint": "http://localhost:5001"
        ... })
        >>> # Обнаружение сервисов
        >>> result = tool.run({
        ...     "action": "discover_services",
        ...     "service_type": "calculator"
        ... })
        >>> # Добавление узла
        >>> result = tool.run({
        ...     "action": "add_node",
        ...     "node_id": "agent-1",
        ...     "endpoint": "http://localhost:5001"
        ... })
    
    Концептуальная реализация, дополнительные зависимости не нужны
    Документация: docs/chapter10/ANP_CONCEPTS.md
    """
    
    def __init__(self, name: str = "anp", description: str = None, discovery=None, network=None):
        """Инициализация инструмента ANP

        Args:
            name: имя инструмента
            description: описание инструмента
            discovery: экземпляр ANPDiscovery (опционально)
            network: экземпляр ANPNetwork (опционально)
        """
        if description is None:
            description = "Управление сетью агентов: сервисы, узлы, маршрутизация. Концептуальная реализация."

        super().__init__(
            name=name,
            description=description
        )
        from hello_agents.protocols.anp.implementation import ANPDiscovery, ANPNetwork
        self._discovery = discovery if discovery is not None else ANPDiscovery()
        self._network = network if network is not None else ANPNetwork()
        
    def run(self, parameters: Dict[str, Any]) -> str:
        """
        Выполнить операцию ANP
        
        Args:
            parameters: словарь с параметрами
                - action: тип операции (register_service, discover_services, add_node, route_message, get_stats)
                - service_id, service_type, endpoint: данные сервиса (register_service)
                - node_id, endpoint: данные узла (add_node)
                - from_node, to_node, message: маршрут (route_message)
        
        Returns:
            результат операции
        """
        from hello_agents.protocols.anp.implementation import ServiceInfo

        action = parameters.get("action", "").lower()
        
        if not action:
            return "Ошибка: укажите action"
        
        try:
            if action == "register_service":
                service_id = parameters.get("service_id")
                service_type = parameters.get("service_type")
                endpoint = parameters.get("endpoint")
                metadata = parameters.get("metadata", {})
                
                if not all([service_id, service_type, endpoint]):
                    return "Ошибка: укажите service_id, service_type и endpoint"
                
                service = ServiceInfo(service_id, service_type, endpoint, metadata)
                self._discovery.register_service(service)
                return f"✅ Сервис '{service_id}' зарегистрирован"

            elif action == "unregister_service":
                service_id = parameters.get("service_id")
                if not service_id:
                    return "Ошибка: укажите service_id"

                # Метод unregister_service из ANPDiscovery
                success = self._discovery.unregister_service(service_id)

                if success:
                    return f"✅ Сервис '{service_id}' удалён из реестра"
                else:
                    return f"Ошибка: сервис '{service_id}' не существует"

            elif action == "discover_services":
                service_type = parameters.get("service_type")
                services = self._discovery.discover_services(service_type)

                if not services:
                    return "Сервисы не найдены"

                result = f"Найдено {len(services)} сервисов:\n\n"
                for service in services:
                    result += f"ID сервиса: {service.service_id}\n"
                    result += f"  Название: {service.service_name}\n"
                    result += f"  Тип: {service.service_type}\n"
                    result += f"  Endpoint: {service.endpoint}\n"
                    if service.capabilities:
                        result += f"  Возможности: {', '.join(service.capabilities)}\n"
                    if service.metadata:
                        result += f"  Метаданные: {service.metadata}\n"
                    result += "\n"
                return result
                
            elif action == "add_node":
                node_id = parameters.get("node_id")
                endpoint = parameters.get("endpoint")
                metadata = parameters.get("metadata", {})
                
                if not all([node_id, endpoint]):
                    return "Ошибка: укажите node_id и endpoint"
                
                self._network.add_node(node_id, endpoint, metadata)
                return f"✅ Узел '{node_id}' добавлен"
                
            elif action == "route_message":
                from_node = parameters.get("from_node")
                to_node = parameters.get("to_node")
                message = parameters.get("message", {})
                
                if not all([from_node, to_node]):
                    return "Ошибка: укажите from_node и to_node"
                
                path = self._network.route_message(from_node, to_node, message)
                if path:
                    return f"Маршрут сообщения: {' -> '.join(path)}"
                else:
                    return "Маршрут не найден"
                
            elif action == "get_stats":
                stats = self._network.get_network_stats()
                result = "Статистика сети:\n"
                for key, value in stats.items():
                    result += f"- {key}: {value}\n"
                return result
                
            else:
                return f"Ошибка: неподдерживаемая операция '{action}'"
                
        except Exception as e:
            return f"Ошибка операции ANP: {str(e)}"
    
    def get_parameters(self) -> List[ToolParameter]:
        """Получить определение параметров инструмента"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Тип: register_service, unregister_service, discover_services, add_node, route_message, get_stats",
                required=True
            ),
            ToolParameter(
                name="service_id",
                type="string",
                description="ID сервиса (register_service, unregister_service)",
                required=False
            ),
            ToolParameter(
                name="service_type",
                type="string",
                description="Тип сервиса (register_service)",
                required=False
            ),
            ToolParameter(
                name="endpoint",
                type="string",
                description="Endpoint (register_service, add_node)",
                required=False
            ),
            ToolParameter(
                name="node_id",
                type="string",
                description="ID узла (add_node)",
                required=False
            ),
            ToolParameter(
                name="from_node",
                type="string",
                description="ID исходного узла (route_message)",
                required=False
            ),
            ToolParameter(
                name="to_node",
                type="string",
                description="ID целевого узла (route_message)",
                required=False
            ),
            ToolParameter(
                name="message",
                type="object",
                description="Содержимое сообщения (route_message)",
                required=False
            ),
            ToolParameter(
                name="metadata",
                type="object",
                description="Метаданные (register_service, add_node, опционально)",
                required=False
            )
        ]

