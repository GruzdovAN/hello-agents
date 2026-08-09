# Глава 10. Протоколы общения агентов

В предыдущих главах мы создали полнофункциональные автономные агенты с возможностями рассуждения, вызова инструментов и памяти. Однако при попытке создать более сложные системы ИИ возникают естественные вопросы: **Как агенты могут эффективно взаимодействовать с внешним миром? Как несколько агентов могут сотрудничать друг с другом?**

Это как раз основная проблема, которую призваны решить протоколы связи агентов. В этой главе будут представлены три протокола связи в структуре HelloAgents: **MCP (протокол контекста модели)** для стандартизированной связи между агентами и инструментами, **A2A (протокол агент-агент)** для однорангового сотрудничества между агентами и **ANP (протокол агентской сети)** для построения крупномасштабных агентских сетей. Эти три протокола вместе образуют уровень инфраструктуры для связи агентов.

Изучая эту главу, вы освоите философию проектирования и практические навыки протоколов связи агентов, поймете различия в конструкции между тремя основными протоколами и узнаете, как выбирать подходящие протоколы для решения практических задач.

## 10.1 Основы протокола связи агента

### 10.1.1 Зачем нужны протоколы связи

Вспомните агент ReAct, который мы создали в главе 7 и который уже обладает мощными возможностями рассуждений и вызова инструментов. Рассмотрим типичный сценарий использования:

```python
from hello_agents import ReActAgent, HelloAgentsLLM
from hello_agents.tools import CalculatorTool, SearchTool

llm = HelloAgentsLLM()
agent = ReActAgent(name="AI Assistant", llm=llm)
agent.add_tool(CalculatorTool())
agent.add_tool(SearchTool())

# Agent can complete tasks independently
response = agent.run("Search for the latest AI news and calculate the total market value of related companies")
```

Этот агент работает хорошо, но сталкивается с тремя фундаментальными ограничениями. Во-первых, это **дилемма интеграции инструментов**: всякий раз, когда нам нужен доступ к новому внешнему сервису (например, GitHub API, базе данных, файловой системе), мы должны написать специализированный класс инструмента. Это не только трудоемко, но и инструменты, написанные разными разработчиками, не могут быть совместимы друг с другом. Второе - ** узкое место расширения возможностей **: возможности агента ограничены предопределенным набором инструментов и не могут динамически обнаруживать и использовать новые сервисы. Наконец, **отсутствие сотрудничества**: когда задачи достаточно сложны, чтобы требовать совместной работы нескольких специализированных агентов (таких как исследователь + писатель + редактор), мы можем координировать их работу только с помощью ручной оркестровки.

Давайте разберемся с этими ограничениями на более конкретном примере. Предположим, вы хотите создать интеллектуального научного сотрудника, которому необходимо:

```python
# Traditional approach: Manually integrate each service
class GitHubTool(BaseTool):
    """Need to manually write GitHub API adapter"""
    def run(self, repo_url):
        # Lots of API calling code...
        pass

class DatabaseTool(BaseTool):
    """Need to manually write database adapter"""
    def run(self, query):
        # Database connection and query code...
        pass

class WeatherTool(BaseTool):
    """Need to manually write weather API adapter"""
    def run(self, location):
        # Weather API calling code...
        pass

# Each new service requires repeating this process
agent.add_tool(GitHubTool())
agent.add_tool(DatabaseTool())
agent.add_tool(WeatherTool())
```

У этого подхода есть очевидные проблемы: дублирование кода (каждый инструмент должен обрабатывать HTTP-запросы, обработку ошибок, аутентификацию и т. д.), сложность в обслуживании (изменения API требуют модификации всех связанных инструментов), невозможность повторного использования (инструменты других разработчиков нельзя использовать напрямую), плохая масштабируемость (добавление новых сервисов требует обширной работы по кодированию).

**Основная ценность протоколов связи ** заключается именно в решении этих проблем. Он предоставляет набор стандартизированных спецификаций интерфейса, которые позволяют агентам получать доступ к различным внешним службам единым способом без необходимости писать специализированные адаптеры для каждой службы. Это похоже на протокол TCP/IP в Интернете, который позволяет различным устройствам взаимодействовать друг с другом без необходимости писать специализированный код связи для каждого типа устройств.

С помощью протоколов связи приведенный выше код можно упростить до:

```python
from hello_agents.tools import MCPTool

# Connect to MCP server, automatically obtain all tools
mcp_tool = MCPTool()  # Built-in server provides basic tools

# Or connect to professional MCP servers
github_mcp = MCPTool(server_command=["npx", "-y", "@modelcontextprotocol/server-github"])
database_mcp = MCPTool(server_command=["python", "database_mcp_server.py"])

# Agent automatically obtains all capabilities without manually writing adapters
agent.add_tool(mcp_tool)
agent.add_tool(github_mcp)
agent.add_tool(database_mcp)
```

Изменения, вносимые протоколами связи, являются фундаментальными: **стандартизованные интерфейсы** позволяют различным сервисам предоставлять унифицированные методы доступа, **взаимодействие** обеспечивает плавную интеграцию инструментов разных разработчиков, **динамическое обнаружение** позволяет агентам обнаруживать новые сервисы и возможности во время выполнения, а **масштабируемость** позволяет системам легко добавлять новые функциональные модули.

### 10.1.2 Сравнение трех принципов проектирования протокола

Протоколы связи агентов — это не единое решение, а серия стандартов, разработанных для разных сценариев связи. В этой главе в качестве примеров для практики используются три основных в настоящее время протокола MCP, A2A и ANP. Ниже представлено обзорное сравнение.

**(1) MCP: мост между агентами и инструментами**

MCP (Model Context Protocol) был предложен командой Anthropic<sup>[1]</sup>, и его основная философия разработки заключается в **стандартизации метода связи между агентами и внешними инструментами/ресурсами**. Представьте, что вашему агенту требуется доступ к различным сервисам, таким как файловые системы, базы данных, GitHub, Slack и т. д. Традиционный подход заключается в написании специализированных адаптеров для каждого сервиса, что не только трудоемко, но и сложно поддерживать. MCP определяет унифицированную спецификацию протокола, которая обеспечивает одинаковый доступ ко всем сервисам.

Философия дизайна MCP — «совместное использование контекста». Это не просто протокол RPC (удаленный вызов процедур), но, что более важно, он позволяет агентам и инструментам обмениваться обширной контекстной информацией. Как показано на рисунке 10.1, когда агент обращается к хранилищу кода, сервер MCP может не только предоставить содержимое файла, но также предоставить контекстную информацию, такую ​​​​как структура кода, отношения зависимостей и историю коммитов, что позволяет агенту принимать более разумные решения.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-1.png" alt="" width="85%"/>
  <p>Рисунок 10.1 Основные принципы проектирования ГЦНА</p>
</div>

**(2) A2A: Диалог между агентами**

Протокол A2A (межагентный протокол) был предложен командой Google<sup>2</sup>, и его основная философия заключается в **реализации одноранговой связи между агентами**. В отличие от MCP, который фокусируется на взаимодействии между агентами и инструментами, A2A фокусируется на том, как агенты взаимодействуют друг с другом. Такая конструкция позволяет агентам участвовать в диалоге, переговорах и сотрудничестве, как человеческие команды.

Философия дизайна A2A — «одноранговое общение». Как показано на рисунке 10.2, в сети A2A каждый агент является одновременно поставщиком и потребителем услуг. Агенты могут активно инициировать запросы, а также отвечать на запросы других агентов. Такая одноранговая структура позволяет избежать узких мест, связанных с централизованными координаторами, что делает сеть агентов более гибкой и масштабируемой.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-2.png" alt="" width="85%"/>
  <p>Рисунок 10.2 Философия проектирования A2A</p>
</div>

**(3) ANP: инфраструктура для агентских сетей**

ANP (Протокол агентской сети) – это концептуальная структура протокола<sup>3</sup>, которая в настоящее время поддерживается сообществом разработчиков программного обеспечения с открытым исходным кодом и еще не имеет развитой экосистемы. Его основная философия проектирования — **построение инфраструктуры для крупномасштабных агентских сетей**. Если MCP решает, «как получить доступ к инструментам», а A2A решает, «как вести диалог с другими агентами», то ANP решает, «как обнаруживать и подключать агентов в крупномасштабных сетях».

Философия дизайна ANP — «открытие децентрализованных сервисов». Как агенты смогут найти нужные им услуги в сети, состоящей из сотен или тысяч агентов? Как показано на рисунке 10.3, ANP обеспечивает механизмы регистрации, обнаружения и маршрутизации служб, позволяя агентам динамически обнаруживать другие службы в сети без необходимости предварительно настраивать все отношения соединений.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-3.png" alt="" width="85%"/>
  <p>Рисунок 10.3 Философия проектирования ANP</p>
</div>

Наконец, в таблице 10.1 давайте используем сравнительную таблицу, чтобы более четко понять различия между этими тремя протоколами:

<div align="center">
  <p>Таблица 10.1 Сравнение трех протоколов</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-table-1.png" alt="" width="85%"/>
</div>

**(4) Как выбрать правильный протокол?**

Текущие протоколы все еще находятся на ранних стадиях разработки. Экосистема MCP относительно зрелая, хотя актуальность различных инструментов зависит от сопровождающих. Более рекомендуется выбирать инструменты MCP, поддерживаемые крупными компаниями.

Ключ к выбору протокола заключается в понимании ваших потребностей:

- Если вашему агенту необходим доступ к внешним сервисам (файлам, базам данных, API), выберите **MCP**.
- Если вам нужно несколько агентов для совместной работы над задачами, выберите **A2A**
- Если вы хотите построить крупномасштабную экосистему агентов, рассмотрите **ANP**.

### 10.1.3 Проект архитектуры протокола связи HelloAgents

Поняв принципы разработки трех протоколов, давайте посмотрим, как реализовать и использовать их в среде HelloAgents. Наша цель разработки: **Позволить учащимся использовать эти протоколы самым простым способом, сохраняя при этом достаточную гибкость для обработки сложных сценариев**.

Как показано на рисунке 10.4, архитектура протокола связи HelloAgents имеет трехуровневую структуру, снизу вверх: уровень реализации протокола, уровень инкапсуляции инструментов и уровень интеграции агентов.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-4.png" alt="" width="85%"/>
  <p>Рис. 10.4. Проектирование протокола связи HelloAgents.</p>
</div>

**(1) Уровень реализации протокола **: этот уровень содержит конкретные реализации трех протоколов. MCP реализован на базе библиотеки FastMCP, предоставляющей клиентский и серверный функционал; A2A реализован на базе официального a2a-sdk Google; ANP - наша собственная легковесная реализация, предоставляющая функции обнаружения сервисов и управления сетью. Конечно, в настоящее время также существует официальная [реализация](https://github.com/agent-network-protocol/AgentConnect), но, учитывая будущие итерации, здесь мы лишь моделируем концепцию.

**(2) Уровень инкапсуляции инструмента**: этот уровень инкапсулирует реализации протокола в единый интерфейс инструмента. MCPTool, A2ATool и ANPTool наследуют от BaseTool, обеспечивая согласованное`run()`метод. Такая конструкция позволяет агентам использовать разные протоколы одинаково.

**(3) Уровень интеграции агентов **: этот уровень является точкой интеграции между агентами и протоколами. Все агенты (ReActAgent, SimpleAgent и т. д.) используют инструменты протокола через систему инструментов, не заботясь о деталях базового протокола.

### 10.1.4 Цели обучения и краткий опыт работы с этой главой

Давайте сначала посмотрим на содержание обучения для главы 10:

```
hello_agents/
├── protocols/                          # Communication protocol module
│   ├── mcp/                            # MCP protocol implementation (Model Context Protocol)
│   │   ├── client.py                   # MCP client (supports 5 transport methods)
│   │   ├── server.py                   # MCP server (FastMCP wrapper)
│   │   └── utils.py                    # Utility functions (create_context/parse_context)
│   ├── a2a/                            # A2A protocol implementation (Agent-to-Agent Protocol)
│   │   └── implementation.py           # A2A server/client (based on a2a-sdk, optional dependency)
│   └── anp/                            # ANP protocol implementation (Agent Network Protocol)
│       └── implementation.py           # ANP service discovery/registration (conceptual implementation)
└── tools/builtin/                      # Built-in tools module
    └── protocol_tools.py               # Protocol tool wrappers (MCPTool/A2ATool/ANPTool)
```

В этой главе основное внимание уделяется приложениям, а целью обучения является умение применять протоколы в ваших собственных проектах. Кроме того, поскольку протоколы в настоящее время находятся на ранних стадиях разработки, нет необходимости тратить слишком много усилий на изобретение велосипеда. Прежде чем приступить к практической работе, подготовим среду разработки:

```bash
# Install HelloAgents framework (Chapter 10 version)
pip install "hello-agents[protocol]==0.2.2"

# Install NodeJS, refer to documentation in Additional-Chapter
```

Давайте испытаем базовую функциональность трех протоколов с помощью простейшего кода:

```python
from hello_agents.tools import MCPTool, A2ATool, ANPTool

# 1. MCP: Access tools
mcp_tool = MCPTool()
result = mcp_tool.run({
    "action": "call_tool",
    "tool_name": "add",
    "arguments": {"a": 10, "b": 20}
})
print(f"MCP calculation result: {result}")  # Output: 30.0

# 2. ANP: Service discovery
anp_tool = ANPTool()
anp_tool.run({
    "action": "register_service",
    "service_id": "calculator",
    "service_type": "math",
    "endpoint": "http://localhost:8080"
})
services = anp_tool.run({"action": "discover_services"})
print(f"Discovered services: {services}")

# 3. A2A: Agent communication
a2a_tool = A2ATool("http://localhost:5000")
print("A2A tool created successfully")
```

Этот простой пример демонстрирует основные функции трех протоколов. В следующих разделах мы подробно изучим подробное использование и лучшие практики каждого протокола.


## 10.2 Протокол MCP на практике

Теперь давайте углубимся в MCP и узнаем, как предоставить агентам доступ к внешним инструментам и ресурсам.

### 10.2.1 Введение в концепцию протокола MCP

**(1) MCP: USB-C для агентов**

Представьте, что вашему агенту может потребоваться сделать много вещей одновременно, например:
- Чтение документов из локальной файловой системы
- Запрос баз данных PostgreSQL
- Поиск кода на GitHub
- Отправлять сообщения Slack
- Доступ к Google Диску.

Традиционно вам нужно было бы написать код адаптера для каждой службы, обрабатывающий различные API, методы аутентификации, обработку ошибок и т. д. Это не только трудоемко, но и сложно поддерживать. Что еще более важно, разные платформы LLM имеют совершенно разные реализации вызовов функций, что требует значительного переписывания кода при переключении моделей.

Появление MCP все изменило. Подобно тому, как USB-C унифицировал методы подключения различных устройств, **MCP унифицировал методы взаимодействия между агентами и внешними инструментами**. Независимо от того, используете ли вы Claude, GPT или другие модели, если они поддерживают протокол MCP, они могут беспрепятственно получить доступ к одним и тем же инструментам и ресурсам.

**(2) Архитектура ГЦНА **

Протокол MCP использует трехуровневую архитектуру хоста, клиента и серверов. Давайте разберемся, как эти компоненты работают вместе в сценарии, показанном на рисунке 10.5.

Предположим, вы используете Claude Desktop и спрашиваете: «Какие документы находятся на моем рабочем столе?»

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-5.png" alt="" width="85%"/>
  <p>Рисунок 10.5 Демонстрация случая MCP</p>
</div>

**Обязанности трехуровневой архитектуры:**

1. **Хост (уровень хоста)**: Claude Desktop выступает в роли хоста, отвечая за получение вопросов пользователей и взаимодействие с моделью Claude. Хост — это интерфейс, с которым пользователи напрямую взаимодействуют, управляя всем потоком разговора.

2. **Клиент (клиентский уровень)**: когда модель Claude решает, что ей необходим доступ к файловой системе, активируется клиент MCP, встроенный в хост. Клиент несет ответственность за установление соединений с соответствующим MCP-сервером, отправку запросов и получение ответов.

3. **Сервер (Серверный уровень)**: вызывается сервер файловой системы MCP, выполняет фактическую операцию сканирования файлов, обращается к каталогу рабочего стола и возвращает список найденных документов.

**Полный поток взаимодействия:** Вопрос пользователя → Claude Desktop (хост) → Анализ модели Claude → Требуется информация о файле → Соединение с клиентом MCP → Файловая система MCP Server → Выполнить операцию → Возврат результата → Claude генерирует ответ → Отобразить на Claude Desktop

Преимущество этого архитектурного проекта заключается в **разделении проблем**: хост фокусируется на пользовательском опыте, клиент фокусируется на связи по протоколу, а сервер фокусируется на реализации конкретной функциональности. Разработчикам нужно только сосредоточиться на разработке соответствующего MCP Сервера, не заботясь о деталях реализации Хоста и Клиента.

**(3) Основные возможности MCP**

Как показано в таблице 10.2, протокол MCP предоставляет три основные возможности, образуя полную структуру доступа к инструментам:

<div align="center">
  <p>Таблица 10.2 Основные возможности MCP</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-table-2.png" alt="" width="85%"/>
</div>

Разница между этими тремя возможностями заключается в следующем: **Инструменты активны** (выполняют операции), **Ресурсы пассивны** (предоставляют данные), **Подсказки носят инструктивный характер** (предоставляют шаблоны).

**(4) Рабочий процесс MCP**

Давайте рассмотрим полный рабочий процесс MCP на конкретном примере, как показано на рисунке 10.6:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-6.png" alt="" width="85%"/>
  <p>Рисунок 10.6 Демонстрация случая MCP</p>
</div>

Ключевой вопрос: **Как Клод (или другие специалисты LLM) решают, какие инструменты использовать?**

Когда пользователь задает вопрос, полный процесс выбора инструмента выглядит следующим образом:

1. **Фаза обнаружения инструмента**: после того, как клиент MCP подключается к серверу, он сначала вызывает `list_tools()`, чтобы получить информацию описания для всех доступных инструментов (включая имя инструмента, описание функции, определение параметров).

2. **Построение контекста**: Клиент преобразует список инструментов в формат, понятный LLM, и добавляет его в системную подсказку. Например:
   ```
   You can use the following tools:
   - read_file(path: str): Read the content of the file at the specified path
   - search_code(query: str, language: str): Search in the codebase
   ```

3. **Model Reasoning**: LLM анализирует вопрос пользователя и доступные инструменты, решая, вызывать ли инструменты и какой инструмент вызывать. Это решение основано на описаниях инструментов и текущем контексте разговора

4. **Выполнение инструмента**: если LLM решает использовать инструмент, Клиент запускает выбранный инструмент через MCP-сервер и получает результат.

5. **Интеграция результатов**: результат выполнения инструмента отправляется обратно в LLM, который объединяет результаты для генерации окончательного ответа.

Этот процесс **полностью автоматизирован**, и LLM будет решать, использовать ли инструменты и как их использовать, основываясь на качестве описаний инструментов. Поэтому написание четких и точных описаний инструментов имеет решающее значение.

**(5) Различия между MCP и вызовом функций**

Многие разработчики задаются вопросом: **Я уже использую вызов функций, зачем мне еще нужен MCP?** Давайте разберемся в их различиях с помощью Таблицы 10.3.

<div align="center">
  <p>Таблица 10.3. Сравнение вызова функций и MCP</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-table-3.png" alt="" width="85%"/>
</div>

Здесь мы используем пример агента, которому необходимо получить доступ к репозиториям GitHub и локальной файловой системе, чтобы детально сравнить две реализации одной и той же задачи.

**Метод 1: использование вызова функций**

```python
# Step 1: Define functions for each LLM provider
# OpenAI format
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_github",
            "description": "Search GitHub repositories",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords"}
                },
                "required": ["query"]
            }
        }
    }
]

# Claude format
claude_tools = [
    {
        "name": "search_github",
        "description": "Search GitHub repositories",
        "input_schema": {  # Note: not parameters
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keywords"}
            },
            "required": ["query"]
        }
    }
]

# Step 2: Implement tool functions yourself
def search_github(query):
    import requests
    response = requests.get(
        "https://api.github.com/search/repositories",
        params={"q": query}
    )
    return response.json()

# Step 3: Handle different model response formats
# OpenAI response
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    result = search_github(**json.loads(tool_call.function.arguments))

# Claude response
if response.content[0].type == "tool_use":
    tool_use = response.content[0]
    result = search_github(**tool_use.input)
```

**Метод 2: Использование MCP**

```python
from hello_agents.protocols import MCPClient

# Step 1: Connect to community-provided MCP server (no need to implement yourself)
github_client = MCPClient([
    "npx", "-y", "@modelcontextprotocol/server-github"
])

fs_client = MCPClient([
    "npx", "-y", "@modelcontextprotocol/server-filesystem", "."
])

# Step 2: Unified calling method (model-independent)
async with github_client:
    # Automatically discover tools
    tools = await github_client.list_tools()

    # Call tool (standardized interface)
    result = await github_client.call_tool(
        "search_repositories",
        {"query": "AI agents"}
    )

# Step 3: Any model supporting MCP can use it
# OpenAI, Claude, Llama, etc. all use the same MCP client
```

Во-первых, необходимо пояснить, что вызов функций и MCP не конкурируют, а скорее дополняют друг друга. Вызов функций — это основная возможность больших языковых моделей, отражающая присущий модели интеллект, позволяющий модели понимать, когда вызывать функции, и точно генерировать соответствующие параметры вызова. Напротив, MCP играет роль инфраструктурного протокола, решая инженерную проблему соединения инструментов с моделями на инженерном уровне, описывая и вызывая инструменты стандартизированным способом.

Чтобы понять это, можно использовать простую аналогию: вызов функций эквивалентен изучению навыка «как позвонить по телефону», включая то, когда набирать номер, как общаться с собеседником и когда вешать трубку. MCP, с другой стороны, представляет собой глобально унифицированный «стандарт телефонной связи», который гарантирует, что любой телефон может успешно дозвониться до другого телефона.

После понимания их взаимодополняющих отношений давайте посмотрим, как использовать протокол MCP в HelloAgents.

### 10.2.2 Использование клиента MCP

HelloAgents реализует полную функциональность клиента MCP на основе FastMCP 2.0. Мы предоставляем как асинхронные, так и синхронные API для различных сценариев использования. Для большинства приложений рекомендуется использовать асинхронный API, поскольку он лучше обрабатывает одновременные запросы и длительные операции. Ниже мы предоставим пошаговую демонстрацию работы.

**(1) Подключение к серверу MCP **

Клиент MCP поддерживает несколько методов подключения, наиболее распространенным из которых является режим Stdio (взаимодействие с локальными процессами через стандартный ввод/вывод):

```python
import asyncio
from hello_agents.protocols import MCPClient

async def connect_to_server():
    # Method 1: Connect to community-provided file system server
    # npx will automatically download and run the @modelcontextprotocol/server-filesystem package
    client = MCPClient([
        "npx", "-y",
        "@modelcontextprotocol/server-filesystem",
        "."  # Specify root directory
    ])

    # Use async with to ensure connection is properly closed
    async with client:
        # Use client here
        tools = await client.list_tools()
        print(f"Available tools: {[t['name'] for t in tools]}")

    # Method 2: Connect to custom Python MCP server
    client = MCPClient(["python", "my_mcp_server.py"])
    async with client:
        # Use client...
        pass

# Run async function
asyncio.run(connect_to_server())
```

**(2) Обнаружение доступных инструментов**

После успешного подключения первым шагом обычно является запрос того, какие инструменты предоставляет сервер:

```python
async def discover_tools():
    client = MCPClient(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

    async with client:
        # Get all available tools
        tools = await client.list_tools()

        print(f"Server provides {len(tools)} tools:")
        for tool in tools:
            print(f"\nTool name: {tool['name']}")
            print(f"Description: {tool.get('description', 'No description')}")

            # Print parameter information
            if 'inputSchema' in tool:
                schema = tool['inputSchema']
                if 'properties' in schema:
                    print("Parameters:")
                    for param_name, param_info in schema['properties'].items():
                        param_type = param_info.get('type', 'any')
                        param_desc = param_info.get('description', '')
                        print(f"  - {param_name} ({param_type}): {param_desc}")

asyncio.run(discover_tools())

# Output example:
# Server provides 5 tools:
#
# Tool name: read_file
# Description: Read file content
# Parameters:
#   - path (string): File path
#
# Tool name: write_file
# Description: Write file content
# Parameters:
#   - path (string): File path
#   - content (string): File content
```

**(3) Инструменты вызова**

При вызове инструментов просто укажите имя инструмента и параметры, соответствующие схеме JSON:

```python
async def use_tools():
    client = MCPClient(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

    async with client:
        # Read file
        result = await client.call_tool("read_file", {"path": "my_README.md"})
        print(f"File content:\n{result}")

        # List directory
        result = await client.call_tool("list_directory", {"path": "."})
        print(f"Current directory files: {result}")

        # Write file
        result = await client.call_tool("write_file", {
            "path": "output.txt",
            "content": "Hello from MCP!"
        })
        print(f"Write result: {result}")

asyncio.run(use_tools())
```

Вот более безопасный способ позвонить в службу MCP для справки:

```python
async def safe_tool_call():
    client = MCPClient(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

    async with client:
        try:
            # Try to read a potentially non-existent file
            result = await client.call_tool("read_file", {"path": "nonexistent.txt"})
            print(result)
        except Exception as e:
            print(f"Tool call failed: {e}")
            # Can choose to retry, use default value, or report error to user

asyncio.run(safe_tool_call())
```

**(4) Доступ к ресурсам**

Помимо инструментов, серверы MCP также могут предоставлять ресурсы:

```python
# List available resources
resources = client.list_resources()
print(f"Available resources: {[r['uri'] for r in resources]}")

# Read resource
resource_content = client.read_resource("file:///path/to/resource")
print(f"Resource content: {resource_content}")
```

**(5) Использование шаблонов подсказок**

Серверы MCP могут предоставлять предопределенные шаблоны подсказок:

```python
# List available prompts
prompts = client.list_prompts()
print(f"Available prompts: {[p['name'] for p in prompts]}")

# Get prompt content
prompt = client.get_prompt("code_review", {"language": "python"})
print(f"Prompt content: {prompt}")
```

**(6) Полный пример: использование службы GitHub MCP**

Давайте посмотрим, как использовать предоставляемый сообществом сервис GitHub MCP, используя полный пример, используя инкапсулированные инструменты MCP:

```python
"""
GitHub MCP Service Example

Note: Need to set environment variable
    Windows: $env:GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
    Linux/macOS: export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
"""

from hello_agents.tools import MCPTool

# Create GitHub MCP tool
github_tool = MCPTool(
    server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
)

# 1. List available tools
print("📋 Available tools:")
result = github_tool.run({"action": "list_tools"})
print(result)

# 2. Search repositories
print("\n🔍 Search repositories:")
result = github_tool.run({
    "action": "call_tool",
    "tool_name": "search_repositories",
    "arguments": {
        "query": "AI agents language:python",
        "page": 1,
        "perPage": 3
    }
})
print(result)

```

### 10.2.3 Объяснение методов транспортировки MCP

Важной особенностью протокола MCP является **транспортный агностицизм**. Это означает, что сам протокол MCP не зависит от конкретных методов транспортировки и может работать на разных каналах связи. HelloAgents, основанный на FastMCP 2.0, обеспечивает полную поддержку метода транспортировки, позволяя выбрать наиболее подходящий режим транспортировки на основе реальных сценариев.

**(1) Обзор методов транспортировки **

HelloAgents '`MCPClient`поддерживает пять методов транспортировки, каждый с различными вариантами использования, как показано в таблице 10.4:

<div align="center">
  <p>Таблица 10.4. Сравнение методов транспортировки MCP</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-table-4.png" alt="" width="85%"/>
</div>

**(2) Примеры использования метода транспортировки**

```python
from hello_agents.tools import MCPTool

# 1. Memory Transport - Memory transport (for testing)
# No parameters specified, uses built-in demo server
mcp_tool = MCPTool()

# 2. Stdio Transport - Standard input/output transport (local development)
# Use command list to start local server
mcp_tool = MCPTool(server_command=["python", "examples/mcp_example_server.py"])

# 3. Stdio Transport with Args - Command transport with parameters
# Can pass additional parameters
mcp_tool = MCPTool(server_command=["python", "examples/mcp_example_server.py", "--debug"])

# 4. Stdio Transport - Community server (npx method)
# Use npx to start community MCP server
mcp_tool = MCPTool(server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

# 5. HTTP/SSE/StreamableHTTP Transport
# Note: MCPTool is mainly for Stdio and Memory transport
# For HTTP/SSE and other remote transports, recommend using MCPClient directly
```

**(3) Транспортировка памяти**

Вариант использования: модульное тестирование, быстрое прототипирование

```python
from hello_agents.tools import MCPTool

# Use built-in demo server (Memory transport)
mcp_tool = MCPTool()

# List available tools
result = mcp_tool.run({"action": "list_tools"})
print(result)

# Call tool
result = mcp_tool.run({
    "action": "call_tool",
    "tool_name": "add",
    "arguments": {"a": 10, "b": 20}
})
print(result)
```

**(4) Stdio Transport — стандартный транспорт ввода/вывода**

Вариант использования: локальная разработка, отладка, серверы сценариев Python.

```python
from hello_agents.tools import MCPTool

# Method 1: Use custom Python server
mcp_tool = MCPTool(server_command=["python", "my_mcp_server.py"])

# Method 2: Use community server (file system)
mcp_tool = MCPTool(server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."])

# List tools
result = mcp_tool.run({"action": "list_tools"})
print(result)

# Call tool
result = mcp_tool.run({
    "action": "call_tool",
    "tool_name": "read_file",
    "arguments": {"path": "README.md"}
})
print(result)
```

**(5) HTTP-транспорт**

Вариант использования: производственная среда, удаленные сервисы, микросервисная архитектура.

```python
# Note: MCPTool is mainly for Stdio and Memory transport
# For HTTP/SSE and other remote transports, recommend using underlying MCPClient

import asyncio
from hello_agents.protocols import MCPClient

async def test_http_transport():
    # Connect to remote HTTP MCP server
    client = MCPClient("http://api.example.com/mcp")

    async with client:
        # Get server information
        tools = await client.list_tools()
        print(f"Remote server tools: {len(tools)} tools")

        # Call remote tool
        result = await client.call_tool("process_data", {
            "data": "Hello, World!",
            "operation": "uppercase"
        })
        print(f"Remote processing result: {result}")

# Note: Requires actual HTTP MCP server
# asyncio.run(test_http_transport())
```

**(6) Транспорт SSE — транспорт событий, отправленных сервером**

Вариант использования: общение в реальном времени, потоковая обработка, длинные соединения.

```python
# Note: MCPTool is mainly for Stdio and Memory transport
# For SSE transport, recommend using underlying MCPClient

import asyncio
from hello_agents.protocols import MCPClient

async def test_sse_transport():
    # Connect to SSE MCP server
    client = MCPClient(
        "http://localhost:8080/sse",
        transport_type="sse"
    )

    async with client:
        # SSE is especially suitable for streaming processing
        result = await client.call_tool("stream_process", {
            "input": "Large data processing request",
            "stream": True
        })
        print(f"Streaming processing result: {result}")

# Note: Requires MCP server supporting SSE
# asyncio.run(test_sse_transport())
```

**(7) StreamableHTTP Transport — потоковая передача HTTP**

Вариант использования: сценарии HTTP, требующие двунаправленной потоковой связи.

```python
# Note: MCPTool is mainly for Stdio and Memory transport
# For StreamableHTTP transport, recommend using underlying MCPClient

import asyncio
from hello_agents.protocols import MCPClient

async def test_streamable_http_transport():
    # Connect to StreamableHTTP MCP server
    client = MCPClient(
        "http://localhost:8080/mcp",
        transport_type="streamable_http"
    )

    async with client:
        # Supports bidirectional streaming communication
        tools = await client.list_tools()
        print(f"StreamableHTTP server tools: {len(tools)} tools")

# Note: Requires MCP server supporting StreamableHTTP
# asyncio.run(test_streamable_http_transport())
```

### 10.2.4 Использование инструментов MCP в агентах

Ранее мы узнали, как напрямую использовать клиент MCP. Но в практических приложениях мы предпочитаем, чтобы агенты **автоматически** вызывали инструменты MCP, а не вручную писали вызывающий код. HelloAgents предоставляет`MCPTool`оболочка, позволяющая серверам MCP легко интегрироваться в цепочку инструментов агента.

**(1) Механизм автоматического расширения инструментов ГЦНА **

Привет, агенты`MCPTool`имеет функцию: **автоматическое расширение**. Когда вы добавляете инструмент MCP к агенту, он автоматически расширяет все инструменты, предоставляемые сервером MCP, до независимых инструментов, позволяя агенту вызывать их как обычные инструменты.

**Метод 1: Использование встроенного демонстрационного сервера**

Ранее мы реализовали функции калькулятора, а здесь преобразуем их в сервисы MCP. Это самый простой способ использования.

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool

agent = SimpleAgent(name="Assistant", llm=HelloAgentsLLM())

# No configuration needed, automatically uses built-in demo server
mcp_tool = MCPTool(name="calculator")
agent.add_tool(mcp_tool)
# ✅ MCP tool 'calculator' expanded into 6 independent tools

# Agent can directly use expanded tools
response = agent.run("Calculate 25 times 16")
print(response)  # Output: The result of 25 times 16 is 400
```

**Инструменты после автоматического расширения**:

- `calculator_add` - Калькулятор сложения
- `calculator_subtract` - Калькулятор вычитания
- `calculator_multiply` - Калькулятор умножения
- `calculator_divide` - Калькулятор деления
- `calculator_greet` — Дружеское приветствие
- `calculator_get_system_info` - Получить информацию о системе

Когда Агент звонит, ему нужно только предоставить параметры, например:`[TOOL_CALL:calculator_multiply:a=25,b=16]`, и система автоматически обработает преобразование типов и вызовы MCP.

**Метод 2: подключение к внешним серверам MCP**

В реальных проектах вам необходимо подключиться к более мощным серверам MCP. Этими серверами могут быть:
- **Официальные серверы, предоставленные сообществом** (например, файловая система, GitHub, база данных и т. д.)
- **Пользовательские серверы, которые вы пишете сами** (инкапсулирующие бизнес-логику).

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool

agent = SimpleAgent(name="File Assistant", llm=HelloAgentsLLM())

# Example 1: Connect to community-provided file system server
fs_tool = MCPTool(
    name="filesystem",  # Specify unique name
    description="Access local file system",
    server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."]
)
agent.add_tool(fs_tool)

# Example 2: Connect to custom Python MCP server
# For how to write custom MCP servers, refer to Section 10.5
custom_tool = MCPTool(
    name="custom_server",  # Use different name
    description="Custom business logic server",
    server_command=["python", "my_mcp_server.py"]
)
agent.add_tool(custom_tool)

# Agent can now automatically use these tools!
response = agent.run("Please read the my_README.md file and summarize its main content")
print(response)
```

При использовании нескольких серверов MCP обязательно укажите другое имя для каждого MCPTool. Это имя будет добавлено в качестве префикса к расширенным именам инструментов, чтобы избежать конфликтов. Например:`name="fs"`расширится до`fs_read_file`, `fs_write_file`и т. д. Если вам нужно написать собственный сервер MCP для инкапсуляции конкретной бизнес-логики, обратитесь к разделу 10.5.

**(2) Как работает автоматическое расширение инструмента MCP**

Понимание механизма автоматического расширения поможет вам лучше использовать инструменты MCP. Давайте углубимся в то, как это работает:

```python
# User code
fs_tool = MCPTool(name="fs", server_command=[...])
agent.add_tool(fs_tool)

# What happens internally:
# 1. MCPTool connects to server, discovers 14 tools
# 2. Creates wrapper for each tool:
#    - fs_read_text_file (parameters: path, tail, head)
#    - fs_write_file (parameters: path, content)
#    - ...
# 3. Registers to Agent's tool registry

# Agent call
response = agent.run("Read README.md")

# Inside Agent:
# 1. Identifies need to call fs_read_text_file
# 2. Generates parameters: path=README.md
# 3. Wrapper converts to MCP format:
#    {"action": "call_tool", "tool_name": "read_text_file", "arguments": {"path": "README.md"}}
# 4. Calls MCP server
# 5. Returns file content
```

Система автоматически преобразует типы на основе определений параметров инструмента:

```python
# Agent calls calculator
agent.run("Calculate 25 times 16")

# Agent generates: a=25,b=16 (string)
# System automatically converts to: {"a": 25.0, "b": 16.0} (number)
# MCP server receives correct number type
```

**(3) Практический пример: интеллектуальный помощник по работе с документами**

Давайте создадим полноценного интеллектуального помощника по работе с документами. Здесь мы демонстрируем простую многоагентную оркестровку:

```python
"""
Multi-Agent Collaborative Intelligent Document Assistant

Uses two SimpleAgents for division of labor:
- Agent1: GitHub search expert
- Agent2: Document generation expert
"""
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="../HelloAgents/.env")

print("="*70)
print("Multi-Agent Collaborative Intelligent Document Assistant")
print("="*70)

# ============================================================
# Agent 1: GitHub Search Expert
# ============================================================
print("\n[Step 1] Creating GitHub search expert...")

github_searcher = SimpleAgent(
    name="GitHub Search Expert",
    llm=HelloAgentsLLM(),
    system_prompt="""You are a GitHub search expert.
Your task is to search GitHub repositories and return results.
Please return clear, structured search results, including:
- Repository name
- Brief description

Keep it concise, don't add extra explanations."""
)

# Add GitHub tool
github_tool = MCPTool(
    name="gh",
    server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
)
github_searcher.add_tool(github_tool)

# ============================================================
# Agent 2: Document Generation Expert
# ============================================================
print("\n[Step 2] Creating document generation expert...")

document_writer = SimpleAgent(
    name="Document Generation Expert",
    llm=HelloAgentsLLM(),
    system_prompt="""You are a document generation expert.
Your task is to generate structured Markdown reports based on provided information.

The report should include:
- Title
- Introduction
- Main content (listed in points, including project names, descriptions, etc.)
- Summary

Please output the complete Markdown format report content directly, do not use tools to save."""
)

# Add file system tool
fs_tool = MCPTool(
    name="fs",
    server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "."]
)
document_writer.add_tool(fs_tool)

# ============================================================
# Execute Task
# ============================================================
print("\n" + "="*70)
print("Starting task execution...")
print("="*70)

try:
    # Step 1: GitHub search
    print("\n[Step 3] Agent1 searching GitHub...")
    search_task = "Search for GitHub repositories about 'AI agent', return the top 5 most relevant results"

    search_results = github_searcher.run(search_task)

    print("\nSearch results:")
    print("-" * 70)
    print(search_results)
    print("-" * 70)

    # Step 2: Generate report
    print("\n[Step 4] Agent2 generating report...")
    report_task = f"""
Based on the following GitHub search results, generate a Markdown format research report:

{search_results}

Report requirements:
1. Title: # AI Agent Framework Research Report
2. Introduction: Explain this is a GitHub project survey about AI Agents
3. Main findings: List found projects and their features (including names, descriptions, etc.)
4. Summary: Summarize common characteristics of these projects

Please output the complete Markdown format report directly.
"""

    report_content = document_writer.run(report_task)

    print("\nReport content:")
    print("=" * 70)
    print(report_content)
    print("=" * 70)

    # Step 3: Save report
    print("\n[Step 5] Saving report to file...")
    import os
    try:
        with open("report.md", "w", encoding="utf-8") as f:
            f.write(report_content)
        print("✅ Report saved to report.md")

        # Verify file
        file_size = os.path.getsize("report.md")
        print(f"✅ File size: {file_size} bytes")
    except Exception as e:
        print(f"❌ Save failed: {e}")

    print("\n" + "="*70)
    print("Task completed!")
    print("="*70)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

```

`github_searcher`без доставки`gh_search_repositories`во время этого процесса для поиска проектов GitHub. Полученные результаты будут возвращены`document_writer`в качестве входных данных, дальнейшего формирования отчета и, наконец, сохранения отчета в report.md.

### 10.2.5 Экосистема сообщества MCP

Огромным преимуществом протокола MCP является его **богатая экосистема сообщества **. Антропные и комьюнити-разработчики создали большое количество готовых MCP-серверов, охватывающих различные сценарии, такие как файловые системы, базы данных, API-сервисы и т.д. Это означает, что вам не нужно писать инструментальные адаптеры с нуля, и вы можете напрямую использовать эти проверенные серверы.

Вот три репозитория ресурсов для сообщества MCP:

1. **Потрясающие серверы MCP ** (https://github.com/punkpeye/awesome-mcp-servers)
   - Список серверов MCP, поддерживаемый сообществом
   - Содержит различные сторонние серверы
   - Классифицированы по функциям, легко найти

2. **Веб-сайт серверов MCP** (https://mcpservers.org/)
   - Официальный сайт каталога серверов MCP
   - Обеспечивает функции поиска и фильтрации.
   - Содержит инструкции по использованию и примеры.

3. **Официальные серверы MCP** (https://github.com/modelcontextprotocol/servers)
   - Серверы официально обслуживаются Anthropic.
   - Высочайшее качество и самая полная документация
   - Содержит реализации часто используемых сервисов.

В таблицах 10.5 и 10.6 показаны часто используемые официальные серверы MCP и популярные серверы MCP сообщества:

<div align="center">
  <p>Таблица 10.5 Часто используемые официальные серверы MCP</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-table-5.png" alt="" width="85%"/>
</div>

<div align="center">
  <p>Таблица 10.6 Популярные серверы MCP сообщества</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-table-6.png" alt="" width="85%"/>
</div>

Вот некоторые особенно интересные задачи TODO для справки:

1. **Автоматическое веб-тестирование (драматург)**

   ```python
   # Agent can automatically:
   # - Open browser to visit website
   # - Fill forms and submit
   # - Screenshot to verify results
   # - Generate test reports
   playwright_tool = MCPTool(
       name="playwright",
       server_command=["npx", "-y", "@playwright/mcp"]
   )
   ```

2. **Интеллектуальный помощник по заметкам (Обсидиан + Недоумение)**
   ```python
   # Agent can:
   # - Search latest tech news (Perplexity)
   # - Organize into structured notes
   # - Save to Obsidian knowledge base
   # - Automatically establish links between notes
   ```

3. **Автоматизация управления проектами (Jira + GitHub)**
   ```python
   # Agent can:
   # - Create Jira tasks from GitHub Issues
   # - Sync code commits to Jira
   # - Automatically update Sprint progress
   # - Generate project reports
   ```

5. **Рабочий процесс создания контента (YouTube + Notion + Spotify)**

   ```python
   # Agent can:
   # - Get YouTube video subtitles
   # - Generate content summaries
   # - Save to Notion database
   # - Play background music (Spotify)
   ```

Я надеюсь, что благодаря объяснениям в этом разделе вы сможете изучить больше случаев реализации MCP, и вклад в HelloAgents приветствуется! Далее давайте узнаем о протоколе A2A.

## 10.3 Протокол A2A на практике

A2A (Agent-to-Agent) - это протокол, который поддерживает прямую связь и сотрудничество между агентами.

### 10.3.1 Проектная мотивация протокола

Протокол MCP решает взаимодействие между агентами и инструментами, а протокол A2A решает проблему сотрудничества между агентами. В задаче, требующей сотрудничества нескольких агентов (например, исследователя, писателя, редактора), им необходимо общаться, делегировать задачи, согласовывать возможности и синхронизировать состояния.

Традиционные решения центрального координатора (звездная топология) имеют три основные проблемы:

- **Единая точка отказа**: отказ координатора приводит к общему параличу системы.
- **Узкое место в производительности**: весь обмен данными проходит через центральный узел, что ограничивает параллелизм.
- **Трудно масштабировать**: добавление или изменение агентов требует изменения центральной логики.

Протокол A2A использует одноранговую (P2P) архитектуру (ячеистую топологию), позволяющую агентам общаться напрямую, что принципиально решает вышеуказанные проблемы. Его ядром являются две абстрактные концепции **Задача** и **Артефакт**, что является его самым большим отличием от MCP, как показано в Таблице 10.7.

<div align="center">
  <p>Таблица 10.7 Основные понятия A2A</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-table-7.png" alt="" width="85%"/>
</div>

Для реализации управления процессом совместной работы A2A определяет стандартизированный жизненный цикл задач, включая такие состояния, как создание, согласование, делегирование, выполнение, завершение и сбой, как показано на рисунке 10.7.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-7.png" alt="" width="85%"/>
  <p>Рисунок 10.7 Жизненный цикл задачи A2A</p>
</div>


Этот механизм позволяет агентам выполнять согласование задач, отслеживание хода выполнения и обработку исключений.

Жизненный цикл запроса A2A — это последовательность, в которой подробно описаны четыре основных этапа, которым следует запрос: обнаружение агента, аутентификация, API отправки сообщений и API отправки потока сообщений. На рисунке 10.8 ниже, заимствованном из блок-схемы официального сайта, показан рабочий процесс, иллюстрирующий взаимодействие между клиентом, сервером A2A и сервером аутентификации.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-8.png" alt="" width="85%"/>
  <p>Рисунок 10.8 Жизненный цикл запроса A2A</p>
</div>

### 10.3.2 Протокол A2A на практике

Большинство существующих реализаций A2A`Sample Code`, и даже реализации Python довольно громоздки. Поэтому здесь мы принимаем только метод, который моделирует идеи протокола, реализуя частичную функциональность через A2A-SDK.

**(2) Создание простого агента A2A**

Давайте создадим агента A2A, снова используя в качестве демонстрации пример калькулятора:

```python
from hello_agents.protocols.a2a.implementation import A2AServer, A2A_AVAILABLE

def create_calculator_agent():
    """Create a calculator agent"""
    if not A2A_AVAILABLE:
        print("❌ A2A SDK not installed, please run: pip install a2a-sdk")
        return None

    print("🧮 Creating calculator agent")

    # Create A2A server
    calculator = A2AServer(
        name="calculator-agent",
        description="Professional mathematical calculation agent",
        version="1.0.0",
        capabilities={
            "math": ["addition", "subtraction", "multiplication", "division"],
            "advanced": ["power", "sqrt", "factorial"]
        }
    )

    # Add basic calculation skills
    @calculator.skill("add")
    def add_numbers(query: str) -> str:
        """Addition calculation"""
        try:
            # Simple parsing of "calculate 5 + 3" format
            parts = query.replace("calculate", "").replace("plus", "+").replace("add", "+")
            if "+" in parts:
                numbers = [float(x.strip()) for x in parts.split("+")]
                result = sum(numbers)
                return f"Calculation result: {' + '.join(map(str, numbers))} = {result}"
            else:
                return "Please use format: calculate 5 + 3"
        except Exception as e:
            return f"Calculation error: {e}"

    @calculator.skill("multiply")
    def multiply_numbers(query: str) -> str:
        """Multiplication calculation"""
        try:
            parts = query.replace("calculate", "").replace("times", "*").replace("×", "*")
            if "*" in parts:
                numbers = [float(x.strip()) for x in parts.split("*")]
                result = 1
                for num in numbers:
                    result *= num
                return f"Calculation result: {' × '.join(map(str, numbers))} = {result}"
            else:
                return "Please use format: calculate 5 * 3"
        except Exception as e:
            return f"Calculation error: {e}"

    @calculator.skill("info")
    def get_info(query: str) -> str:
        """Get agent information"""
        return f"I am {calculator.name}, can perform basic mathematical calculations. Supported skills: {list(calculator.skills.keys())}"

    print(f"✅ Calculator agent created successfully, supported skills: {list(calculator.skills.keys())}")
    return calculator

# Create agent
calc_agent = create_calculator_agent()
if calc_agent:
    # Test skills
    print("\n🧪 Testing agent skills:")
    test_queries = [
        "Get information",
        "Calculate 10 + 5",
        "Calculate 6 * 7"
    ]

    for query in test_queries:
        if "information" in query.lower():
            result = calc_agent.skills["info"](query)
        elif "+" in query:
            result = calc_agent.skills["add"](query)
        elif "*" in query or "×" in query:
            result = calc_agent.skills["multiply"](query)
        else:
            result = "Unknown query type"

        print(f"  📝 Query: {query}")
        print(f"  🤖 Reply: {result}")
        print()
```

**(2) Специальный агент A2A**

Вы также можете создать своего собственного агента A2A, вот простая демонстрация:

```python
from hello_agents.protocols.a2a.implementation import A2AServer, A2A_AVAILABLE

def create_custom_agent():
    """Create custom agent"""
    if not A2A_AVAILABLE:
        print("Please install A2A SDK first: pip install a2a-sdk")
        return None

    # Create agent
    agent = A2AServer(
        name="my-custom-agent",
        description="My custom agent",
        capabilities={"custom": ["skill1", "skill2"]}
    )

    # Add skills
    @agent.skill("greet")
    def greet_user(name: str) -> str:
        """Greet user"""
        return f"Hello, {name}! I am a custom agent."

    @agent.skill("calculate")
    def simple_calculate(expression: str) -> str:
        """Simple calculation"""
        try:
            # Safe calculation (only supports basic operations)
            allowed_chars = set('0123456789+-*/(). ')
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return f"Calculation result: {expression} = {result}"
            else:
                return "Error: Only basic mathematical operations supported"
        except Exception as e:
            return f"Calculation error: {e}"

    return agent

# Create and test custom agent
custom_agent = create_custom_agent()
if custom_agent:
    # Test skills
    print("Testing greeting skill:")
    result1 = custom_agent.skills["greet"]("Zhang San")
    print(result1)

    print("\nTesting calculation skill:")
    result2 = custom_agent.skills["calculate"]("10 + 5 * 2")
    print(result2)
```

### 10.3.3 Использование инструментов HelloAgents A2A

HelloAgents предоставляет унифицированный интерфейс инструмента A2A.

**(1) Создание сервера агентов A2A**

Сначала давайте создадим сервер агентов:

```python
from hello_agents.protocols import A2AServer
import threading
import time

# Create researcher Agent service
researcher = A2AServer(
    name="researcher",
    description="Agent responsible for searching and analyzing materials",
    version="1.0.0"
)

# Define skills
@researcher.skill("research")
def handle_research(text: str) -> str:
    """Handle research requests"""
    import re
    match = re.search(r'research\s+(.+)', text, re.IGNORECASE)
    topic = match.group(1).strip() if match else text

    # Actual research logic (simplified here)
    result = {
        "topic": topic,
        "findings": f"Research results about {topic}...",
        "sources": ["Source 1", "Source 2", "Source 3"]
    }
    return str(result)

# Start service in background
def start_server():
    researcher.run(host="localhost", port=5000)

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    print("✅ Researcher Agent service started at http://localhost:5000")

    # Keep program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nService stopped")
```

**(2) Создание клиента агента A2A**

Теперь создадим клиент для связи с сервером:

```python
from hello_agents.protocols import A2AClient

# Create client to connect to researcher Agent
client = A2AClient("http://localhost:5000")

# Send research request
response = client.execute_skill("research", "research AI applications in healthcare")
print(f"Received response: {response.get('result')}")

# Output:
# Received response: {'topic': 'AI applications in healthcare', 'findings': 'Research results about AI applications in healthcare...', 'sources': ['Source 1', 'Source 2', 'Source 3']}
```

**(3) Создание агентской сети**

Для совместной работы нескольких агентов мы можем подключить несколько агентов друг к другу:

```python
from hello_agents.protocols import A2AServer, A2AClient
import threading
import time

# 1. Create multiple Agent services
researcher = A2AServer(
    name="researcher",
    description="Researcher"
)

@researcher.skill("research")
def do_research(text: str) -> str:
    import re
    match = re.search(r'research\s+(.+)', text, re.IGNORECASE)
    topic = match.group(1).strip() if match else text
    return str({"topic": topic, "findings": f"Research results for {topic}"})

writer = A2AServer(
    name="writer",
    description="Writer"
)

@writer.skill("write")
def write_article(text: str) -> str:
    import re
    match = re.search(r'write\s+(.+)', text, re.IGNORECASE)
    content = match.group(1).strip() if match else text

    # Try to parse research data
    try:
        data = eval(content)
        topic = data.get("topic", "Unknown topic")
        findings = data.get("findings", "No research results")
    except:
        topic = "Unknown topic"
        findings = content

    return f"# {topic}\n\nBased on research: {findings}\n\nArticle content..."

editor = A2AServer(
    name="editor",
    description="Editor"
)

@editor.skill("edit")
def edit_article(text: str) -> str:
    import re
    match = re.search(r'edit\s+(.+)', text, re.IGNORECASE)
    article = match.group(1).strip() if match else text

    result = {
        "article": article + "\n\n[Edited and optimized]",
        "feedback": "Article quality is good",
        "approved": True
    }
    return str(result)

# 2. Start all services
threading.Thread(target=lambda: researcher.run(port=5000), daemon=True).start()
threading.Thread(target=lambda: writer.run(port=5001), daemon=True).start()
threading.Thread(target=lambda: editor.run(port=5002), daemon=True).start()
time.sleep(2)  # Wait for services to start

# 3. Create clients to connect to each Agent
researcher_client = A2AClient("http://localhost:5000")
writer_client = A2AClient("http://localhost:5001")
editor_client = A2AClient("http://localhost:5002")

# 4. Collaboration workflow
def create_content(topic):
    # Step 1: Research
    research = researcher_client.execute_skill("research", f"research {topic}")
    research_data = research.get('result', '')

    # Step 2: Write
    article = writer_client.execute_skill("write", f"write {research_data}")
    article_content = article.get('result', '')

    # Step 3: Edit
    final = editor_client.execute_skill("edit", f"edit {article_content}")
    return final.get('result', '')

# Usage
result = create_content("AI applications in healthcare")
print(f"\nFinal result:\n{result}")
```

### 10.3.4 Использование инструментов A2A в агентах

Теперь давайте посмотрим, как интегрировать A2A в агенты HelloAgents.

**(1) Использование оболочки A2ATool**

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import A2ATool
from dotenv import load_dotenv

load_dotenv()
llm = HelloAgentsLLM()

# Assume a researcher Agent service is already running at http://localhost:5000

# Create coordinator Agent
coordinator = SimpleAgent(name="Coordinator", llm=llm)

# Add A2A tool, connect to researcher Agent
researcher_tool = A2ATool(
    name="researcher",
    description="Researcher Agent, can search and analyze materials",
    agent_url="http://localhost:5000"
)
coordinator.add_tool(researcher_tool)

# Coordinator can call researcher Agent
response = coordinator.run("Please have the researcher help me research AI applications in education")
print(response)
```

**(2) Практический пример: интеллектуальная система обслуживания клиентов**

Давайте построим полноценную интеллектуальную систему обслуживания клиентов с тремя агентами:
- **Администратор**: анализирует типы вопросов клиентов.
- **Технический эксперт**: отвечает на технические вопросы.
- **Консультант по продажам**: отвечает на вопросы по продажам.

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import A2ATool
from hello_agents.protocols import A2AServer
import threading
import time
from dotenv import load_dotenv

load_dotenv()
llm = HelloAgentsLLM()

# 1. Create technical expert Agent service
tech_expert = A2AServer(
    name="tech_expert",
    description="Technical expert, answers technical questions"
)

@tech_expert.skill("answer")
def answer_tech_question(text: str) -> str:
    import re
    match = re.search(r'answer\s+(.+)', text, re.IGNORECASE)
    question = match.group(1).strip() if match else text
    # In actual applications, this would call LLM or knowledge base
    return f"Technical answer: Regarding '{question}', I suggest you check our technical documentation..."

# 2. Create sales consultant Agent service
sales_advisor = A2AServer(
    name="sales_advisor",
    description="Sales consultant, answers sales questions"
)

@sales_advisor.skill("answer")
def answer_sales_question(text: str) -> str:
    import re
    match = re.search(r'answer\s+(.+)', text, re.IGNORECASE)
    question = match.group(1).strip() if match else text
    return f"Sales answer: Regarding '{question}', we have special offers..."

# 3. Start services
threading.Thread(target=lambda: tech_expert.run(port=6000), daemon=True).start()
threading.Thread(target=lambda: sales_advisor.run(port=6001), daemon=True).start()
time.sleep(2)

# 4. Create receptionist Agent (using HelloAgents' SimpleAgent)
receptionist = SimpleAgent(
    name="Receptionist",
    llm=llm,
    system_prompt="""You are a customer service receptionist, responsible for:
1. Analyzing customer question types (technical questions or sales questions)
2. Forwarding questions to appropriate experts
3. Organizing expert answers and returning them to customers

Please remain polite and professional."""
)

# Add technical expert tool
tech_tool = A2ATool(
    agent_url="http://localhost:6000",
    name="tech_expert",
    description="Technical expert, answers technical-related questions"
)
receptionist.add_tool(tech_tool)

# Add sales consultant tool
sales_tool = A2ATool(
    agent_url="http://localhost:6001",
    name="sales_advisor",
    description="Sales consultant, answers price and purchase-related questions"
)
receptionist.add_tool(sales_tool)

# 5. Handle customer inquiries
def handle_customer_query(query):
    print(f"\nCustomer inquiry: {query}")
    print("=" * 50)
    response = receptionist.run(query)
    print(f"\nCustomer service reply: {response}")
    print("=" * 50)

# Test different types of questions
if __name__ == "__main__":
    handle_customer_query("How do I call your API?")
    handle_customer_query("What is the price of the enterprise version?")
    handle_customer_query("How do I integrate it into my Python project?")
```

**(3) Расширенное использование: переговоры с агентом **

Протокол A2A также поддерживает механизмы согласования между агентами:

```python
from hello_agents.protocols import A2AServer, A2AClient
import threading
import time

# Create two Agents that need to negotiate
agent1 = A2AServer(
    name="agent1",
    description="Agent 1"
)

@agent1.skill("propose")
def handle_proposal(text: str) -> str:
    """Handle negotiation proposals"""
    import re

    # Parse proposal
    match = re.search(r'propose\s+(.+)', text, re.IGNORECASE)
    proposal_str = match.group(1).strip() if match else text

    try:
        proposal = eval(proposal_str)
        task = proposal.get("task")
        deadline = proposal.get("deadline")

        # Evaluate proposal
        if deadline >= 7:  # Need at least 7 days
            result = {"accepted": True, "message": "Proposal accepted"}
        else:
            result = {
                "accepted": False,
                "message": "Timeline too tight",
                "counter_proposal": {"deadline": 7}
            }
        return str(result)
    except:
        return str({"accepted": False, "message": "Invalid proposal format"})

agent2 = A2AServer(
    name="agent2",
    description="Agent 2"
)

@agent2.skill("negotiate")
def negotiate_task(text: str) -> str:
    """Initiate negotiation"""
    import re

    # Parse task and deadline
    match = re.search(r'negotiate\s+task:(.+?)\s+deadline:(\d+)', text, re.IGNORECASE)
    if match:
        task = match.group(1).strip()
        deadline = int(match.group(2))

        # Send proposal to agent1
        proposal = {"task": task, "deadline": deadline}
        return str({"status": "negotiating", "proposal": proposal})
    else:
        return str({"status": "error", "message": "Invalid negotiation request"})

# Start services
threading.Thread(target=lambda: agent1.run(port=7000), daemon=True).start()
threading.Thread(target=lambda: agent2.run(port=7001), daemon=True).start()
```

## 10.4 Протокол ANP на практике

После того, как протокол MCP решил вызов инструмента, а протокол A2A решил проблему одноранговой совместной работы агентов, протокол ANP фокусируется на решении проблем управления агентами в крупномасштабных открытых сетевых средах.

В разделах 10.2 и 10.3 мы узнали о MCP (доступ к инструментам) и A2A (сотрудничество агентов). Теперь давайте узнаем о протоколе ANP (Agent Network Protocol), который ориентирован на создание **крупномасштабных открытых агентских сетей**.

### 10.4.1 Цели протокола

Когда сеть содержит большое количество агентов с различными функциями (например, обработка естественного языка, распознавание изображений, анализ данных и т. д.), система сталкивается с рядом проблем:

- **Обнаружение служб**. Как быстро найти агентов, способных справиться с этой задачей, когда поступает новая задача?
- **Интеллектуальная маршрутизация**. Если одну и ту же задачу могут выполнять несколько агентов, как выбрать наиболее подходящий (например, с учетом нагрузки, стоимости и т. д.) и передать ему задачу?
- **Динамическое масштабирование**: Как сделать так, чтобы другие участники могли обнаруживать и вызывать недавно присоединившихся агентов?

Целью проектирования ANP является предоставление стандартизированного механизма для решения вышеуказанных проблем обнаружения служб, выбора маршрутизации и масштабируемости сети.

Для достижения своих целей проектирования ANP определяет следующие основные концепции, как показано в Таблице 10.8:

<div align="center">
  <p>Таблица 10.8 Основные понятия ANP</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-table-8.png" alt="" width="85%"/>
</div>

Мы также заимствуем из официального [Руководства по началу работы](https://github.com/agent-network-protocol/AgentNetworkProtocol/blob/main/docs/chinese/ANP入门指南.md), чтобы представить архитектурный проект ANP, как показано на рисунке 10.9.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-9.png" alt="" width="85%"/>
  <p>Рисунок 10.9 Общий процесс ANP</p>
</div>


In this flowchart, the main steps include:

**1. Обнаружение и сопоставление служб.** Во-первых, агент A использует общедоступную службу обнаружения для запроса на основе семантических или функциональных описаний, чтобы найти агента B, который соответствует требованиям его задачи. Служба обнаружения устанавливает индекс путем предварительного сканирования стандартных конечных точек (`.well-known/agent-descriptions`), предоставляемый каждым агентом, тем самым достигая динамического соответствия между запросчиками и поставщиками услуг.

**2. Проверка личности на основе DID:** В начале взаимодействия агент А использует свой закрытый ключ для подписи запроса, содержащего его собственный DID. После того как агент Б получает его, он анализирует DID для получения соответствующего открытого ключа и использует его для проверки подлинности подписи и целостности запроса, тем самым устанавливая доверенную связь между обеими сторонами.

**3. Стандартизированное выполнение услуг:** после прохождения проверки личности агент Б отвечает на запрос, и обе стороны обмениваются данными или вызывают службы (такие как бронирование, запросы и т. д.) в соответствии с заранее определенными стандартными интерфейсами и форматами данных. Стандартизированные процессы взаимодействия являются основой для достижения межплатформенной и межсистемной совместимости.

Подводя итог, можно сказать, что ядром этого механизма является использование DID для создания децентрализованной основы доверия и использование стандартизированных протоколов описания для достижения динамического обнаружения сервисов. Этот подход позволяет агентам безопасно и эффективно формировать сети для совместной работы в Интернете, не требуя центральной координации.

### 10.4.2 Использование обнаружения службы ANP

**(1) Создание Центра обнаружения служб**

```python
from hello_agents.protocols import ANPDiscovery, register_service

# Create service discovery center
discovery = ANPDiscovery()

# Register Agent services
register_service(
    discovery=discovery,
    service_id="nlp_agent_1",
    service_name="NLP Processing Expert A",
    service_type="nlp",
    capabilities=["text_analysis", "sentiment_analysis", "ner"],
    endpoint="http://localhost:8001",
    metadata={"load": 0.3, "price": 0.01, "version": "1.0.0"}
)

register_service(
    discovery=discovery,
    service_id="nlp_agent_2",
    service_name="NLP Processing Expert B",
    service_type="nlp",
    capabilities=["text_analysis", "translation"],
    endpoint="http://localhost:8002",
    metadata={"load": 0.7, "price": 0.02, "version": "1.1.0"}
)

print("✅ Service registration completed")
```

**(2) Поиск сервисов**

```python
from hello_agents.protocols import discover_service

# Find by type
nlp_services = discover_service(discovery, service_type="nlp")
print(f"Found {len(nlp_services)} NLP services")

# Select service with lowest load
best_service = min(nlp_services, key=lambda s: s.metadata.get("load", 1.0))
print(f"Best service: {best_service.service_name} (load: {best_service.metadata['load']})")
```

**(3) Сеть агентов по созданию**

```python
from hello_agents.protocols import ANPNetwork

# Create network
network = ANPNetwork(network_id="ai_cluster")

# Add nodes
for service in discovery.list_all_services():
    network.add_node(service.service_id, service.endpoint)

# Establish connections (based on capability matching)
network.connect_nodes("nlp_agent_1", "nlp_agent_2")

stats = network.get_network_stats()
print(f"✅ Network construction completed, total {stats['total_nodes']} nodes")
```

### 10.4.3 Практический пример

Давайте построим полную систему распределенного планирования задач:

```python
from hello_agents.protocols import ANPDiscovery, register_service
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools.builtin import ANPTool
import random
from dotenv import load_dotenv

load_dotenv()
llm = HelloAgentsLLM()

# 1. Create service discovery center
discovery = ANPDiscovery()

# 2. Register multiple compute nodes
for i in range(10):
    register_service(
        discovery=discovery,
        service_id=f"compute_node_{i}",
        service_name=f"Compute Node {i}",
        service_type="compute",
        capabilities=["data_processing", "ml_training"],
        endpoint=f"http://node{i}:8000",
        metadata={
            "load": random.uniform(0.1, 0.9),
            "cpu_cores": random.choice([4, 8, 16]),
            "memory_gb": random.choice([16, 32, 64]),
            "gpu": random.choice([True, False])
        }
    )

print(f"✅ Registered {len(discovery.list_all_services())} compute nodes")

# 3. Create task scheduler Agent
scheduler = SimpleAgent(
    name="Task Scheduler",
    llm=llm,
    system_prompt="""You are an intelligent task scheduler, responsible for:
1. Analyzing task requirements
2. Selecting the most suitable compute node
3. Assigning tasks

When selecting nodes, consider: load, CPU cores, memory, GPU, and other factors."""
)

# Add ANP tool
anp_tool = ANPTool(
    name="service_discovery",
    description="Service discovery tool, can find and select compute nodes",
    discovery=discovery
)
scheduler.add_tool(anp_tool)

# 4. Intelligent task assignment
def assign_task(task_description):
    print(f"\nTask: {task_description}")
    print("=" * 50)

    # Let Agent intelligently select node
    response = scheduler.run(f"""
    Please select the most suitable compute node for the following task:
    {task_description}

    Requirements:
    1. List all available nodes
    2. Analyze characteristics of each node
    3. Select the most suitable node
    4. Explain selection reasoning
    """)

    print(response)
    print("=" * 50)

# Test different types of tasks
assign_task("Train a large deep learning model, requires GPU support")
assign_task("Process large amounts of text data, requires high memory")
assign_task("Run lightweight data analysis task")
```

Это пример балансировки нагрузки

```python
from hello_agents.protocols import ANPDiscovery, register_service
import random

# Create service discovery center
discovery = ANPDiscovery()

# Register multiple services of the same type
for i in range(5):
    register_service(
        discovery=discovery,
        service_id=f"api_server_{i}",
        service_name=f"API Server {i}",
        service_type="api",
        capabilities=["rest_api"],
        endpoint=f"http://api{i}:8000",
        metadata={"load": random.uniform(0.1, 0.9)}
    )

# Load balancing function
def get_best_server():
    """Select server with lowest load"""
    servers = discovery.discover_services(service_type="api")
    if not servers:
        return None

    best = min(servers, key=lambda s: s.metadata.get("load", 1.0))
    return best

# Simulate request allocation
for i in range(10):
    server = get_best_server()
    print(f"Request {i+1} -> {server.service_name} (load: {server.metadata['load']:.2f})")

    # Update load (simulated)
    server.metadata["load"] += 0.1
```

## 10.5 Создание пользовательских серверов MCP

В предыдущих разделах мы узнали, как использовать существующие сервисы MCP. Также мы узнали о характеристиках различных протоколов. Теперь давайте узнаем, как создать собственный сервер MCP.

### 10.5.1 Создание вашего первого сервера MCP

**(1) Зачем создавать собственный MCP-сервер?**

Хотя вы можете напрямую использовать общедоступные службы MCP, во многих практических сценариях приложений вам необходимо создавать собственные серверы MCP для удовлетворения конкретных потребностей.

К основным мотивам относятся следующие:

- **Инкапсуляция бизнес-логики**: инкапсулируйте специфичные для предприятия бизнес-процессы или сложные операции в виде стандартизированных инструментов MCP для унифицированного вызова агентами.
- **Доступ к личным данным**. Создайте безопасный и управляемый интерфейс или прокси-сервер для доступа к внутренним базам данных, API или другим частным источникам данных, которые не могут быть доступны из общедоступной сети.
- **Оптимизация производительности**. Выполните глубокую оптимизацию для высокочастотных вызовов или сценариев приложений со строгими требованиями к задержке ответа.
- **Расширение пользовательских функций**: реализация определенных функций, не предоставляемых стандартными службами MCP, например интеграция моделей собственных алгоритмов или подключение к определенным аппаратным устройствам.

**(2) Учебный пример: Сервер MCP запроса погоды**

Начнем с простого сервера запросов погоды и постепенно изучим разработку сервера MCP:

```python
#!/usr/bin/env python3
"""Weather Query MCP Server"""

import json
import requests
import os
from datetime import datetime
from typing import Dict, Any
from hello_agents.protocols import MCPServer

# Create MCP server
weather_server = MCPServer(name="weather-server", description="Real weather query service")

CITY_MAP = {
    "Beijing": "Beijing", "Shanghai": "Shanghai", "Guangzhou": "Guangzhou",
    "Shenzhen": "Shenzhen", "Hangzhou": "Hangzhou", "Chengdu": "Chengdu",
    "Chongqing": "Chongqing", "Wuhan": "Wuhan", "Xi'an": "Xi'an",
    "Nanjing": "Nanjing", "Tianjin": "Tianjin", "Suzhou": "Suzhou"
}


def get_weather_data(city: str) -> Dict[str, Any]:
    """Get weather data from wttr.in"""
    city_en = CITY_MAP.get(city, city)
    url = f"https://wttr.in/{city_en}?format=j1"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    current = data["current_condition"][0]

    return {
        "city": city,
        "temperature": float(current["temp_C"]),
        "feels_like": float(current["FeelsLikeC"]),
        "humidity": int(current["humidity"]),
        "condition": current["weatherDesc"][0]["value"],
        "wind_speed": round(float(current["windspeedKmph"]) / 3.6, 1),
        "visibility": float(current["visibility"]),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# Define tool function
def get_weather(city: str) -> str:
    """Get current weather for specified city"""
    try:
        weather_data = get_weather_data(city)
        return json.dumps(weather_data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "city": city}, ensure_ascii=False)


def list_supported_cities() -> str:
    """List all supported Chinese cities"""
    result = {"cities": list(CITY_MAP.keys()), "count": len(CITY_MAP)}
    return json.dumps(result, ensure_ascii=False, indent=2)


def get_server_info() -> str:
    """Get server information"""
    info = {
        "name": "Weather MCP Server",
        "version": "1.0.0",
        "tools": ["get_weather", "list_supported_cities", "get_server_info"]
    }
    return json.dumps(info, ensure_ascii=False, indent=2)


# Register tools to server
weather_server.add_tool(get_weather)
weather_server.add_tool(list_supported_cities)
weather_server.add_tool(get_server_info)


if __name__ == "__main__":
    weather_server.run()
```

**(3) Тестирование пользовательского сервера MCP**

Затем создайте тестовый скрипт:

```python
#!/usr/bin/env python3
"""Test Weather Query MCP Server"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'HelloAgents'))
from hello_agents.protocols.mcp.client import MCPClient


async def test_weather_server():
    server_script = os.path.join(os.path.dirname(__file__), "14_weather_mcp_server.py")
    client = MCPClient(["python", server_script])

    try:
        async with client:
            # Test 1: Get server information
            info = json.loads(await client.call_tool("get_server_info", {}))
            print(f"Server: {info['name']} v{info['version']}")

            # Test 2: List supported cities
            cities = json.loads(await client.call_tool("list_supported_cities", {}))
            print(f"Supported cities: {cities['count']} cities")

            # Test 3: Query Beijing weather
            weather = json.loads(await client.call_tool("get_weather", {"city": "Beijing"}))
            if "error" not in weather:
                print(f"\nBeijing weather: {weather['temperature']}°C, {weather['condition']}")

            # Test 4: Query Shenzhen weather
            weather = json.loads(await client.call_tool("get_weather", {"city": "Shenzhen"}))
            if "error" not in weather:
                print(f"Shenzhen weather: {weather['temperature']}°C, {weather['condition']}")

            print("\n✅ All tests completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_weather_server())
```

**(4) Использование пользовательского сервера MCP в агенте**

```python
"""Using Weather MCP Server in Agent"""

import os
from dotenv import load_dotenv
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool

load_dotenv()


def create_weather_assistant():
    """Create weather assistant"""
    llm = HelloAgentsLLM()

    assistant = SimpleAgent(
        name="Weather Assistant",
        llm=llm,
        system_prompt="""You are a weather assistant that can query city weather.
Use the get_weather tool to query weather, supports Chinese city names.
"""
    )

    # Add weather MCP tool
    server_script = os.path.join(os.path.dirname(__file__), "14_weather_mcp_server.py")
    weather_tool = MCPTool(server_command=["python", server_script])
    assistant.add_tool(weather_tool)

    return assistant


def demo():
    """Demo"""
    assistant = create_weather_assistant()

    print("\nQuery Beijing weather:")
    response = assistant.run("How's the weather in Beijing today?")
    print(f"Answer: {response}\n")


def interactive():
    """Interactive mode"""
    assistant = create_weather_assistant()

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break
        response = assistant.run(user_input)
        print(f"Assistant: {response}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        interactive()
```

```
🔗 Connecting to MCP server...
✅ Connection successful!
🔌 Connection disconnected
✅ Tool 'mcp_get_weather' registered.
✅ Tool 'mcp_list_supported_cities' registered.
✅ Tool 'mcp_get_server_info' registered.
✅ MCP tool 'mcp' expanded into 3 independent tools

You: I want to query Beijing's weather
🔗 Connecting to MCP server...
✅ Connection successful!
🔌 Connection disconnected
Assistant: The current weather in Beijing is as follows:

- Temperature: 10.0°C
- Feels like: 9.0°C
- Humidity: 94%
- Weather condition: Light rain
- Wind speed: 1.7 m/s
- Visibility: 10.0 km
- Timestamp: October 9, 2025 13:46:40

Please bring rain gear and adjust your clothing according to weather changes.
```

### 10.5.2 Загрузка MCP-сервера

Мы создали MCP-сервер реальных запросов погоды. Теперь давайте опубликуем его на платформе Smithery, чтобы разработчики со всего мира могли использовать наш сервис.

(1) Что такое Кузнечное дело?

[Кузница](https://smithery.ai/) — официальная платформа публикации серверов MCP, аналогичная PyPI Python или npm Node.js. Через Smithery пользователи могут:

- 🔍 Обнаружение и поиск серверов MCP
- 📦 Установите серверы MCP одним щелчком мыши
- 📊 Просматривать статистику использования и рейтинги сервера
- 🔄 Автоматически получать обновления сервера

(2) Подготовка к публикации
Во-первых, нам нужно организовать проект в стандартном издательском формате. Эта папка организована в`code`каталог для вашей справки:

```
weather-mcp-server/
├── README.md           # Project documentation
├── LICENSE            # Open source license
├── Dockerfile         # Docker build configuration (recommended)
├── pyproject.toml     # Python project configuration (required)
├── requirements.txt   # Python dependencies
├── smithery.yaml      # Smithery configuration file (required)
└── server.py          # MCP server main file
```

Обратите внимание, что`smithery.yaml`— это файл конфигурации платформы Smithery:
```yaml
name: weather-mcp-server
displayName: Weather MCP Server
description: Real-time weather query MCP server based on HelloAgents framework
version: 1.0.0
author: HelloAgents Team
homepage: https://github.com/yourusername/weather-mcp-server
license: MIT
categories:
  - weather
  - data
tags:
  - weather
  - real-time
  - helloagents
  - wttr
runtime: container
build:
  dockerfile: Dockerfile
  dockerBuildPath: .
startCommand:
  type: http
tools:
  - name: get_weather
    description: Get current weather for a city
  - name: list_supported_cities
    description: List all supported cities
  - name: get_server_info
    description: Get server information
```

Объяснение конфигурации:

- `name`: уникальный идентификатор сервера (строчные буквы, разделенные дефисом).
- `displayName`: отображаемое имя
- `description`: Краткое описание
- `version`: номер версии (следует за семантическим управлением версиями).
- `runtime`: среда выполнения (python/node).
- `entrypoint`: входной файл
- `tools`: Tool list

`pyproject.toml`— это стандартный файл конфигурации для проектов Python. Smithery требуется этот файл, поскольку позже он будет упакован на сервер:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "weather-mcp-server"
version = "1.0.0"
description = "Real-time weather query MCP server based on HelloAgents framework"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "HelloAgents Team", email = "xxx"}
]
requires-python = ">=3.10"
dependencies = [
    "hello-agents>=0.2.1",
    "requests>=2.31.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/weather-mcp-server"
Repository = "https://github.com/yourusername/weather-mcp-server"
"Bug Tracker" = "https://github.com/yourusername/weather-mcp-server/issues"

[tool.setuptools]
py-modules = ["server"]
```


Объяснение конфигурации:

- `[build-system]`: указывает инструмент сборки (setuptools).
- `[project]`: метаданные проекта.
  - `name`: Название проекта
  - `version`: номер версии (следует за семантическим управлением версиями).
  - `зависимости`: список зависимостей проекта.
  - `requires-python`: требования к версии Python.
- `[project.urls]`: ссылки, связанные с проектом.
- `[tool.setuptools]`: конфигурация setuptools

Хотя Smithery автоматически генерирует Dockerfile, предоставление специального Dockerfile гарантирует успешное развертывание:

```dockerfile
# Multi-stage build for weather-mcp-server
FROM python:3.12-slim-bookworm as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml requirements.txt ./
COPY server.py ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8081

# Expose port (Smithery uses 8081)
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the MCP server
CMD ["python", "server.py"]
```

Объяснение конфигурации Dockerfile:

- **Базовое изображение**: `python:3.12-slim-bookworm` — упрощенный образ Python.
- **Рабочий каталог**: `/app` — корневой каталог приложения.
- **Порт**: `8081` — стандартный порт платформы Smithery.
- **Команда запуска**: `python server.py` — запустить сервер MCP.

Здесь нам нужно форкнуть`hello-agents`репозиторий, получите исходный код в`code`и создайте репозиторий с именем`weather-mcp-server`используя собственный GitHub, меняя`yourusername`к вашему имени пользователя GitHub.

(3) Отправить в Кузницу

Откройте браузер и посетите [https://smithery.ai/](https://smithery.ai/). Войдите в Smithery, используя свою учетную запись GitHub. Нажмите кнопку «Опубликовать сервер» на странице, введите URL-адрес своего репозитория GitHub:`https://github.com/yourusername/weather-mcp-server`, и дождитесь публикации.

После завершения публикации вы увидите страницу, подобную этой, как показано на рисунке 10.10:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-10.png" alt="" width="85%"/>
  <p>Рисунок 10.10 Страница успешной публикации Smithery</p>
</div>



После успешной публикации сервера пользователи смогут использовать его следующими способами:

Способ 1: через интерфейс командной строки Smithery

```bash
# Install Smithery CLI
npm install -g @smithery/cli

# Install your server
smithery install weather-mcp-server
```

Способ 2: настройка в Claude Desktop

```json
{
  "mcpServers": {
    "weather": {
      "command": "smithery",
      "args": ["run", "weather-mcp-server"]
    }
  }
}
```

Способ 3: использование в HelloAgents

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools.builtin.protocol_tools import MCPTool

agent = SimpleAgent(name="Weather Assistant", llm=HelloAgentsLLM())

# Use Smithery-installed server
weather_tool = MCPTool(
    server_command=["smithery", "run", "weather-mcp-server"]
)
agent.add_tool(weather_tool)

response = agent.run("How's the weather in Beijing today?")
```

Конечно, это всего лишь пример, и есть еще множество вариантов использования, которые вы можете изучить самостоятельно. На рисунке 10.11 ниже показана информация, включаемая в случае успешной публикации инструмента MCP, с отображением имени службы «Погода» и ее уникального идентификатора.`@jjyaoao/weather-mcp-server`и информацию о состоянии. В области «Инструменты» показаны только что реализованные методы, а в области «Подключение» представлена ​​техническая информация, необходимая для подключения и использования этой службы, включая **URL-адрес доступа** службы и **фрагменты кода конфигурации** на нескольких языках/средах. Если вы хотите узнать больше, вы можете нажать на эту [ссылку](https://smithery.ai/server/@jjyaoao/weather-mcp-server).

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/10-figures/10-11.png" alt="" width="85%"/>
  <p>Рисунок 10.11. Инструмент MCP успешно опубликован на сайте Smithery.</p>
</div>

Теперь пришло время создать свой собственный сервер MCP!



## 10.6 Краткое содержание главы

В этой главе систематически представлены три основных протокола для связи агентов: MCP, A2A и ANP, а также рассмотрены принципы их разработки, сценарии применения и практические методы.

**Позиционирование протокола:**

- **MCP (Протокол контекста модели)**: служит связующим звеном между агентами и инструментами и обеспечивает унифицированный интерфейс доступа к инструментам, подходящий для расширения возможностей отдельных агентов.
- **A2A (протокол «агент-агент»)**: как система диалога между агентами поддерживает прямое общение и согласование задач, подходит для тесного сотрудничества в небольших группах.
- **ANP (сетевой протокол агентов)**: в качестве «Интернета» для агентов обеспечивает механизмы обнаружения, маршрутизации и балансировки нагрузки, подходящие для построения крупномасштабных открытых сетей агентов.

**Решение для интеграции HelloAgents**

В`HelloAgents`Framework эти три протокола единообразно абстрагируются как инструменты (Tool), обеспечивая плавную интеграцию, позволяя разработчикам гибко добавлять агентам различные уровни коммуникационных возможностей:

```python
# Unified Tool interface
from hello_agents.tools import MCPTool, A2ATool, ANPTool

# All protocols can be added to Agent as Tools
agent.add_tool(MCPTool(...))
agent.add_tool(A2ATool(...))
agent.add_tool(ANPTool(...))
```

**Резюме практического опыта**

- Отдайте приоритет использованию услуг MCP зрелого сообщества, чтобы уменьшить ненужную избыточную разработку.
- Выбирайте соответствующие протоколы в зависимости от масштаба системы: A2A рекомендуется для сценариев совместной работы небольшого масштаба, а ANP следует использовать для сценариев крупномасштабной сети.

После изучения этой главы рекомендуется:

1. **Практическая практика**:
   - Создайте свой собственный сервер MCP
   - Создавайте многоагентные системы совместной работы с использованием протоколов
   - Стратегии комбинированного применения для MCP, A2A и ANP
2. **Углубленное обучение**:
   - Прочтите официальную документацию MCP: https://modelcontextprotocol.io.
   - Прочтите официальную документацию A2A: https://a2a-protocol.org/latest/.
   - Прочтите официальную документацию ANP: https://agent-network-protocol.com/guide/.
3. **Участвовать в сообществе**:
   - Вносите в сообщество новые услуги MCP.
   - Поделитесь собственными разработанными кейсами внедрения агентов
   - Участвуйте в обсуждениях технических стандартов для связанных протоколов, задавайте вопросы в разделе «Проблемы» или напрямую помогайте HelloAgents поддерживать новые примеры случаев.

**Поздравляем с завершением главы 10!**

Теперь вы овладели основными знаниями протоколов связи агентов. Продолжайте в том же духе! 🚀

## Упражнения

> **Примечание**. Для некоторых упражнений нет стандартных ответов. Основное внимание уделяется развитию у учащихся всестороннего понимания и практических навыков в протоколах связи агентов.

1. В этой главе были представлены три протокола связи агентов: MCP, A2A и ANP. Пожалуйста, проанализируйте:

   - В разделе 10.1.2 сравнивались принципы разработки трех протоколов. Пожалуйста, проанализируйте глубже: почему MCP подчеркивает «совместное использование контекста», A2A подчеркивает «диалоговое сотрудничество», а ANP подчеркивает «топологию сети»? Какие основные проблемы решают эти философии дизайна?
   - Предположим, вы хотите создать «интеллектуальную систему обслуживания клиентов», которая требует следующих функций: (1) доступ к базе данных клиентов и системе заказов; (2) Несколько профессиональных агентов по обслуживанию клиентов сотрудничают для решения сложных проблем; (3) Поддержка крупномасштабных одновременных запросов пользователей. Пожалуйста, выберите наиболее подходящий протокол для каждой функции и объясните свои аргументы.
   - Можно ли использовать три протокола в сочетании? Пожалуйста, разработайте сценарий практического применения, показывающий, как одновременно использовать MCP, A2A и ANP для создания полноценной агентской системы. Нарисуйте схему архитектуры системы и объясните обязанности каждого протокола.

2. MCP (Model Context Protocol) — это стандартный протокол для связи агента и инструмента. Основываясь на содержании раздела 10.2, пожалуйста, глубоко подумайте:

> **Примечание**: это практический вопрос, рекомендуется использовать в реальных условиях.

   - В реализации сервера MCP в разделе 10.2.3 мы определили основные методы, такие как list_tools и call_tool. Расширьте эту реализацию, добавив новый сервер MCP, который предоставляет следующие инструменты: (1) инструмент запросов к базе данных; (2) Инструмент визуализации данных; (3) Инструмент создания отчетов. Требуйте, чтобы инструменты могли совместно выполнять сложные задачи анализа данных.
   - Протокол MCP поддерживает две важные концепции: «Ресурсы» и «Подсказки», но в этой главе основное внимание уделяется «Инструментам». Ознакомьтесь с официальной документацией MCP, чтобы понять цели разработки ресурсов и подсказок, а также разработайте сценарий приложения, показывающий, как использовать эти три основные концепции для создания более мощной системы агентов.
   - MCP использует JSON-RPC 2.0 в качестве базового протокола связи и обменивается данными между процессами через stdio. Пожалуйста, проанализируйте: каковы преимущества и ограничения этой конструкции? Если вам необходимо поддерживать удаленные серверы MCP (доступ к которым осуществляется через HTTP/WebSocket), как следует расширить текущую реализацию?

3. A2A (протокол «агент-агент») поддерживает диалоговое сотрудничество между агентами. На основе содержания раздела 10.3 выполните следующую расширенную практику:

> **Примечание**: это практический вопрос, рекомендуется использовать в реальных условиях.

   - В случае «исследовательской группы» в разделе 10.3.4 исследователи и авторы сотрудничают посредством протокола A2A для завершения написания статьи. Пожалуйста, расширьте этот случай, добавив третьего агента «Рецензент», который может проверять качество статьи и предлагать предложения по доработке. Разработайте процесс сотрудничества между тремя агентами и внедрите полный код.
   - Протокол A2A определяет типы сообщений, такие как «задача» и «task_result». Пожалуйста, проанализируйте: если во время сотрудничества возникают конфликты (например, два агента имеют разные мнения по одному и тому же вопросу), как следует разработать механизм разрешения конфликтов? Пожалуйста, расширьте протокол A2A, добавив такие типы сообщений, как «переговоры» и «голосование».
   - Сравните протокол A2A с мультиагентными платформами, такими как AutoGen и CAMEL, представленными в главе 6: Какова связь между A2A как стандартным протоколом и этими платформами? Могут ли они заменить друг друга? Пожалуйста, разработайте решение, которое позволит агентам на основе протокола A2A взаимодействовать с агентами в среде AutoGen.

4. ANP (протокол агентской сети) поддерживает крупномасштабные агентские сети. Основываясь на содержании раздела 10.4, пожалуйста, подробно проанализируйте:

   - В разделе 10.4.2 представлена ​​топология сети ANP, включая звездообразную, ячеистую, иерархическую и другие структуры. Пожалуйста, проанализируйте: в каких сценариях следует выбирать какую структуру топологии? Если масштаб сети увеличится с 10 агентов до 1000 агентов, как должна развиваться структура топологии?
   - Протокол ANP поддерживает механизмы «маршрутизации» и «обнаружения», позволяя агентам динамически находить подходящих партнеров для сотрудничества. Пожалуйста, разработайте «интеллектуальный алгоритм маршрутизации»: автоматически выбирайте оптимальный путь маршрутизации сообщений в зависимости от типа задачи, возможностей агента, нагрузки на сеть и других факторов.
   - В случае «умного города» в разделе 10.4.4 несколько агентов сотрудничают для управления городскими системами. Подумайте: если критический агент (например, агент управления трафиком) выйдет из строя, как должна реагировать вся система? Пожалуйста, разработайте «механизм отказоустойчивости», включающий обнаружение неисправностей, резервное переключение, восстановление состояния и другие функции.

5. Безопасность и защита конфиденциальности протоколов связи агентов являются ключевыми вопросами практического применения. Пожалуйста, подумайте:

   - В реализации клиента MCP, описанной в разделе 10.2.4, агенты могут вызывать любой инструмент, предоставляемый сервером MCP. Пожалуйста, проанализируйте: какие риски безопасности несет эта конструкция? Если сервер MCP выполняет опасные операции (например, удаление файлов, выполнение системных команд), как следует спроектировать механизм контроля разрешений?
   - Протоколы A2A и ANP предусматривают связь между несколькими агентами, которая может содержать конфиденциальную информацию (например, данные о конфиденциальности пользователей, коммерческую тайну). Пожалуйста, разработайте решение «сквозного шифрования»: убедитесь, что сообщения не подслушиваются и не подделываются во время передачи, поддерживая при этом аутентификацию личности агента и контроль доступа.
   - В крупномасштабных агентских сетях злонамеренные агенты могут отправлять ложную информацию, запускать атаки типа «отказ в обслуживании» или красть данные у других агентов. Пожалуйста, разработайте «систему оценки доверия»: динамически оценивайте надежность каждого агента на основе исторического поведения, качества сотрудничества, оценки сообщества и других факторов и соответствующим образом корректируйте коммуникационные стратегии.

## Ссылки

[1] Антропный. (2024). *Протокол контекста модели*. Получено 7 октября 2025 г. с сайтаhttps://modelcontextprotocol.io/

[2] Проект А2А. (2025). *Протокол A2A: открытый протокол для связи между агентами*. Получено 7 октября 2025 г. с сайтаhttps://a2a-protocol.org/

[3] Чанг Г., Линь Э., Юань К., Цай Р., Чен Б., Се Х. и Чжан Ю. (2025). *Технический документ по протоколу агентской сети*. arXiv.https://doi.org/10.48550/arXiv.2508.00007

