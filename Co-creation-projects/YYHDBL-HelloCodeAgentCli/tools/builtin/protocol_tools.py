"""
Набор протокольных инструментов

Интерфейсы на базе протоколов:
- MCP Tool: fastmcp, подключение к MCP (Model Context Protocol)
- A2A Tool: a2a, связь между агентами (нужен a2a-sdk)
- ANP Tool: концептуальная реализация сети агентов
"""

from typing import Dict, Any, List, Optional
from ..base import Tool, ToolParameter
import os


# Карта env-переменных MCP-серверов
# Автоопределение env для известных серверов
MCP_SERVER_ENV_MAP = {
    "server-github": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "server-slack": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
    "server-google-drive": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"],
    "server-postgres": ["POSTGRES_CONNECTION_STRING"],
    "server-sqlite": [],  # env не нужны
    "server-filesystem": [],  # env не нужны
}


class MCPTool(Tool):
    """MCP (Model Context Protocol) Tool

    Подключение к MCP-серверу: инструменты, ресурсы, промпты.
    
    Возможности:
    - список инструментов
    - вызов инструментов
    - чтение ресурсов
    - шаблоны промптов

    Пример:
        >>> from hello_agents.tools.builtin import MCPTool
        >>>
        >>> # 1: встроенный демо-сервер
        >>> tool = MCPTool()  # встроенный демо-сервер
        >>> result = tool.run({"action": "list_tools"})
        >>>
        >>> # 2: внешний MCP
        >>> tool = MCPTool(server_command=["python", "examples/mcp_example.py"])
        >>> result = tool.run({"action": "list_tools"})
        >>>
        >>> # 3: свой FastMCP
        >>> from fastmcp import FastMCP
        >>> server = FastMCP("MyServer")
        >>> tool = MCPTool(server=server)

    Требуется fastmcp (в зависимостях)
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
        Инициализация MCP Tool

        Args:
            name: имя инструмента (по умолчанию "mcp"; для разных серверов — разные имена)
            description: описание (опционально)
            server_command: команда запуска сервера
            server_args: аргументы сервера
            server: экземпляр FastMCP (in-memory)
            auto_expand: auto_expand в отдельные Tool (по умолчанию True)
            env: env (высший приоритет)
            env_keys: env_keys из окружения

        Приоритет env:
            1. переданный env
            2. env_keys
            3. авто по server_command

        Если пусто — встроенный демо-сервер

        Пример:
            >>> # env напрямую
            >>> github_tool = MCPTool(
            ...     name="github",
            ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"],
            ...     env={"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"}
            ... )
            >>>
            >>> # из .env по env_keys
            >>> github_tool = MCPTool(
            ...     name="github",
            ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"],
            ...     env_keys=["GITHUB_PERSONAL_ACCESS_TOKEN"]
            ... )
            >>>
            >>> # авто (рекомендуется)
            >>> github_tool = MCPTool(
            ...     name="github",
            ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
            ...     # GITHUB_PERSONAL_ACCESS_TOKEN из env
            ... )
        """
        self.server_command = server_command
        self.server_args = server_args or []
        self.server = server
        self._client = None
        self._available_tools = []
        self.auto_expand = auto_expand
        self.prefix = f"{name}_" if auto_expand else ""

        # env > env_keys > авто
        self.env = self._prepare_env(env, env_keys, server_command)

        # Демо-сервер по умолчанию
        if not server_command and not server:
            self.server = self._create_builtin_server()

        # Discovery инструментов
        self._discover_tools()

        # описание по умолчанию или авто
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
        Подготовка env

        env > env_keys > авто

        Args:
            env: явный env
            env_keys: список env_keys
            server_command: server_command для авто

        Returns:
            итоговый env
        """
        result_env = {}

        # 1. авто (низший приоритет)
        if server_command:
            # имя сервера из команды
            server_name = None
            for part in server_command:
                if "server-" in part:
                    # server-github из пути
                    server_name = part.split("/")[-1] if "/" in part else part
                    break

            # MCP_SERVER_ENV_MAP
            if server_name and server_name in MCP_SERVER_ENV_MAP:
                auto_keys = MCP_SERVER_ENV_MAP[server_name]
                for key in auto_keys:
                    value = os.getenv(key)
                    if value:
                        result_env[key] = value
                        print(f"🔑 Автозагрузка env: {key}")

        # 2. env_keys
        if env_keys:
            for key in env_keys:
                value = os.getenv(key)
                if value:
                    result_env[key] = value
                    print(f"🔑 Загрузка env из env_keys: {key}")
                else:
                    print(f"⚠️  Предупреждение: переменная {key} не задана")

        # 3. явный env
        if env:
            result_env.update(env)
            for key in env.keys():
                print(f"🔑 Явный env: {key}")

        return result_env

    def _create_builtin_server(self):
        """Встроенный демо-сервер"""
        try:
            from fastmcp import FastMCP

            server = FastMCP("HelloAgents-BuiltinServer")

            @server.tool()
            def add(a: float, b: float) -> float:
                """Сложение"""
                return a + b

            @server.tool()
            def subtract(a: float, b: float) -> float:
                """Вычитание"""
                return a - b

            @server.tool()
            def multiply(a: float, b: float) -> float:
                """Умножение"""
                return a * b

            @server.tool()
            def divide(a: float, b: float) -> float:
                """Деление"""
                if b == 0:
                    raise ValueError("Делитель не может быть нулём")
                return a / b

            @server.tool()
            def greet(name: str = "World") -> str:
                """Приветствие"""
                return f"Hello, {name}! Добро пожаловать в MCP HelloAgents!"

            @server.tool()
            def get_system_info() -> dict:
                """Информация о системе"""
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
                "Нужен fastmcp: pip install fastmcp"
            )

    def _discover_tools(self):
        """Discovery инструментов MCP"""
        try:
            from hello_agents.protocols.mcp.client import MCPClient
            import asyncio

            async def discover():
                client_source = self.server if self.server else self.server_command
                async with MCPClient(client_source, self.server_args, env=self.env) as client:
                    tools = await client.list_tools()
                    return tools

            # async discovery
            try:
                loop = asyncio.get_running_loop()
                # новый поток при running loop
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
                # нет running loop
                self._available_tools = asyncio.run(discover())

        except Exception as e:
            # сбой discovery не блокирует init
            self._available_tools = []

    def _generate_description(self) -> str:
        """Расширенное описание инструмента"""
        if not self._available_tools:
            return "MCP: инструменты, ресурсы, промпты; встроенный и внешний сервер."

        if self.auto_expand:
            # auto_expand: кратко
            return f"MCP-сервер,{len(self._available_tools)}инструмент(ов), разворачиваются для агента."
        else:
            # без expand: подробно
            desc_parts = [
                f"MCP-сервер:{len(self._available_tools)}инструмент(ов):"
            ]

            # список инструментов
            for tool in self._available_tools:
                tool_name = tool.get('name', 'unknown')
                tool_desc = tool.get('description', 'без описания')
                # первая фраза описания
                short_desc = tool_desc.split('.')[0] if tool_desc else 'без описания'
                desc_parts.append(f"  • {tool_name}: {short_desc}")

            # формат вызова
            desc_parts.append("\nФормат: JSON-параметры")
            desc_parts.append('{"action": "call_tool", "tool_name": "имя инструмента", "arguments": {...}}')

            # пример
            if self._available_tools:
                first_tool = self._available_tools[0]
                tool_name = first_tool.get('name', 'example')
                desc_parts.append(f'\nПример:{{"action": "call_tool", "tool_name": "{tool_name}", "arguments": {{...}}}}')

            return "\n".join(desc_parts)

    def get_expanded_tools(self) -> List['Tool']:  # type: ignore
        """
        Список развёрнутых Tool

        Каждый MCP-инструмент → отдельный Tool

        Returns:
            Список Tool
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
        Выполнение MCP-операции

        Args:
            parameters: словарь параметров
                - action: action: list_tools, call_tool, ...
                  без action, но с tool_name → call_tool
                - tool_name: имя (для call_tool)
                - arguments: arguments для call_tool
                - uri: uri для read_resource
                - prompt_name: prompt_name
                - prompt_arguments: prompt_arguments

        Returns:
            результат
        """
        from hello_agents.protocols.mcp.client import MCPClient

        # авто call_tool
        action = parameters.get("action", "").lower()
        if not action and "tool_name" in parameters:
            action = "call_tool"
            parameters["action"] = action

        if not action:
            return "Ошибка:укажите action или tool_name"
        
        try:
            # async MCPClient
            import asyncio
            from hello_agents.protocols.mcp.client import MCPClient

            async def run_mcp_operation():
                # встроенный или внешний
                if self.server:
                    # in-memory server
                    client_source = self.server
                else:
                    # server_command
                    client_source = self.server_command

                async with MCPClient(client_source, self.server_args, env=self.env) as client:
                    if action == "list_tools":
                        tools = await client.list_tools()
                        if not tools:
                            return "инструменты не найдены"
                        result = f"Найдено {len(tools)} инструмент(ов):\n"
                        for tool in tools:
                            result += f"- {tool['name']}: {tool['description']}\n"
                        return result

                    elif action == "call_tool":
                        tool_name = parameters.get("tool_name")
                        arguments = parameters.get("arguments", {})
                        if not tool_name:
                            return "Ошибка: укажите tool_name"
                        result = await client.call_tool(tool_name, arguments)
                        return f"Инструмент '{tool_name}' — результат:\n{result}"

                    elif action == "list_resources":
                        resources = await client.list_resources()
                        if not resources:
                            return "ресурсы не найдены"
                        result = f"Найдено {len(resources)} ресурс(ов):\n"
                        for resource in resources:
                            result += f"- {resource['uri']}: {resource['name']}\n"
                        return result

                    elif action == "read_resource":
                        uri = parameters.get("uri")
                        if not uri:
                            return "Ошибка:укажите uri"
                        content = await client.read_resource(uri)
                        return f"Ресурс '{uri}' — содержимое:\n{content}"

                    elif action == "list_prompts":
                        prompts = await client.list_prompts()
                        if not prompts:
                            return "промпты не найдены"
                        result = f"Найдено {len(prompts)} промпт(ов):\n"
                        for prompt in prompts:
                            result += f"- {prompt['name']}: {prompt['description']}\n"
                        return result

                    elif action == "get_prompt":
                        prompt_name = parameters.get("prompt_name")
                        prompt_arguments = parameters.get("prompt_arguments", {})
                        if not prompt_name:
                            return "Ошибка:укажите prompt_name"
                        messages = await client.get_prompt(prompt_name, prompt_arguments)
                        result = f"Промпт '{prompt_name}':\n"
                        for msg in messages:
                            result += f"[{msg['role']}] {msg['content']}\n"
                        return result

                    else:
                        return f"Ошибка:неподдерживаемая операция '{action}'"

            # asyncio
            try:
                # running loop?
                try:
                    loop = asyncio.get_running_loop()
                    # новый loop в потоке
                    import concurrent.futures
                    import threading

                    def run_in_thread():
                        # new_event_loop
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(run_mcp_operation())
                        finally:
                            new_loop.close()

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        return future.result()
                except RuntimeError:
                    # asyncio.run
                    return asyncio.run(run_mcp_operation())
            except Exception as e:
                return f"ошибка async: {str(e)}"
                    
        except Exception as e:
            return f"ошибка MCP: {str(e)}"
    
    def get_parameters(self) -> List[ToolParameter]:
        """Возвращает определения параметров инструмента"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="action: list_tools, call_tool, list_resources, read_resource, list_prompts, get_prompt",
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
                description="Аргументы (для call_tool)",
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
    """A2A (Agent-to-Agent Protocol) Tool

    Подключение к A2A Agent.
    
    Возможности:
    - вопрос агенту
    - информация об агенте
    - произвольное сообщение

    Пример:
        >>> from hello_agents.tools.builtin import A2ATool
        >>> # A2A Agent (имя по умолчанию)
        >>> tool = A2ATool(agent_url="http://localhost:5000")
        >>> # A2A Agent (своё имя и описание)
        >>> tool = A2ATool(
        ...     agent_url="http://localhost:5000",
        ...     name="tech_expert",
        ...     description="Технический эксперт"
        ... )
        >>> # вопрос
        >>> result = tool.run({"action": "ask", "question": "2+2"})
        >>> # get_info
        >>> result = tool.run({"action": "get_info"})
    
    Нужен a2a-sdk: pip install a2a-sdk
    Документация: docs/chapter10/A2A_GUIDE.md
    Репозиторий: https://github.com/a2aproject/a2a-python
    """
    
    def __init__(self, agent_url: str, name: str = "a2a", description: str = None):
        """
        Инициализация A2A Tool

        Args:
            agent_url: Agent URL
            name: имя (по умолчанию "a2a")
            description: описание (опционально)
        """
        if description is None:
            description = "A2A Agent: вопросы и info; нужен a2a-sdk."

        super().__init__(
            name=name,
            description=description
        )
        self.agent_url = agent_url
        
    def run(self, parameters: Dict[str, Any]) -> str:
        """
        Операция A2A
        
        Args:
            parameters: словарь параметров
                - action: ask | get_info
                - question: question для ask
        
        Returns:
            результат
        """
        try:
            from hello_agents.protocols.a2a.implementation import A2AClient, A2A_AVAILABLE
            if not A2A_AVAILABLE:
                return ("Ошибка: нужен a2a-sdk\n"
                       "Установка: pip install a2a-sdk\n"
                       "Документация: docs/chapter10/A2A_GUIDE.md\n"
                       "Репозиторий: https://github.com/a2aproject/a2a-python")
        except ImportError:
            return ("Ошибка: не удалось импортировать A2A\n"
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
                return f"Ошибка:неподдерживаемая операция '{action}'"
                
        except Exception as e:
            return f"ошибка A2A: {str(e)}"
    
    def get_parameters(self) -> List[ToolParameter]:
        """Возвращает определения параметров инструмента"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="action: ask, get_info",
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
    """ANP (Agent Network Protocol) Tool

    Управление сетью агентов: discovery, узлы, маршрутизация.
    Концептуальная демонстрация сети агентов.
    
    Возможности:
    - регистрация и discovery сервисов
    - узлы сети
    - маршрутизация сообщений
    - статистика сети

    Пример:
        >>> from hello_agents.tools.builtin import ANPTool
        >>> tool = ANPTool()
        >>> # register_service
        >>> result = tool.run({
        ...     "action": "register_service",
        ...     "service_id": "calc-1",
        ...     "service_type": "calculator",
        ...     "endpoint": "http://localhost:5001"
        ... })
        >>> # discover_services
        >>> result = tool.run({
        ...     "action": "discover_services",
        ...     "service_type": "calculator"
        ... })
        >>> # add_node
        >>> result = tool.run({
        ...     "action": "add_node",
        ...     "node_id": "agent-1",
        ...     "endpoint": "http://localhost:5001"
        ... })
    
    Концепт, без дополнительных зависимостей
    Документация: docs/chapter10/ANP_CONCEPTS.md
    """
    
    def __init__(self, name: str = "anp", description: str = None, discovery=None, network=None):
        """Инициализация ANP Tool

        Args:
            name: Имя инструмента
            description: Описание инструмента
            discovery: ANPDiscovery (опционально)
            network: ANPNetwork (опционально)
        """
        if description is None:
            description = "Сеть агентов: discovery, узлы, маршрутизация (концепт)."

        super().__init__(
            name=name,
            description=description
        )
        from hello_agents.protocols.anp.implementation import ANPDiscovery, ANPNetwork
        self._discovery = discovery if discovery is not None else ANPDiscovery()
        self._network = network if network is not None else ANPNetwork()
        
    def run(self, parameters: Dict[str, Any]) -> str:
        """
        Операция ANP
        
        Args:
            parameters: словарь параметров
                - action: register_service | discover_services | ...
                - service_id, service_type, endpoint для register_service
                - node_id, endpoint для add_node
                - from_node, to_node, message для route_message
        
        Returns:
            результат
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
                return f"✅ Сервис зарегистрирован '{service_id}'"

            elif action == "unregister_service":
                service_id = parameters.get("service_id")
                if not service_id:
                    return "Ошибка: укажите service_id"

                # ANPDiscovery.unregister_service
                success = self._discovery.unregister_service(service_id)

                if success:
                    return f"✅ Сервис удалён '{service_id}'"
                else:
                    return f"Ошибка:Сервис '{service_id}' не существует"

            elif action == "discover_services":
                service_type = parameters.get("service_type")
                services = self._discovery.discover_services(service_type)

                if not services:
                    return "сервисы не найдены"

                result = f"Найдено {len(services)} сервис(ов):\n\n"
                for service in services:
                    result += f"ID сервиса: {service.service_id}\n"
                    result += f"  Имя: {service.service_name}\n"
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
                return f"✅ Узел добавлен '{node_id}'"
                
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
                    return "маршрут не найден"
                
            elif action == "get_stats":
                stats = self._network.get_network_stats()
                result = "Статистика сети:\n"
                for key, value in stats.items():
                    result += f"- {key}: {value}\n"
                return result
                
            else:
                return f"Ошибка:неподдерживаемая операция '{action}'"
                
        except Exception as e:
            return f"ошибка ANP: {str(e)}"
    
    def get_parameters(self) -> List[ToolParameter]:
        """Возвращает определения параметров инструмента"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="action: register_service, unregister_service, discover_services, add_node, route_message, get_stats",
                required=True
            ),
            ToolParameter(
                name="service_id",
                type="string",
                description="ID сервиса (register/unregister)",
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
                description="Исходный узел (route_message)",
                required=False
            ),
            ToolParameter(
                name="to_node",
                type="string",
                description="Целевой узел (route_message)",
                required=False
            ),
            ToolParameter(
                name="message",
                type="object",
                description="Сообщение (route_message)",
                required=False
            ),
            ToolParameter(
                name="metadata",
                type="object",
                description="Метаданные (опционально)",
                required=False
            )
        ]

