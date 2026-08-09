# Глава 4. Классические парадигмы агентов

В предыдущей главе мы глубоко исследовали большие языковые модели как «мозг» современных агентов. Мы узнали об их внутренней архитектуре Transformer, методах взаимодействия с ними и границах их возможностей. Теперь пришло время применить эти теоретические знания на практике и создать агентов своими руками.

Основная способность современного агента заключается в его способности связывать мыслительную силу больших языковых моделей с внешним миром. Он может автономно понимать намерения пользователя, разлагать сложные задачи и достигать целей, вызывая ряд «инструментов», таких как интерпретаторы кода, поисковые системы и API, для получения информации и выполнения операций. Однако агенты не всемогущи; они также сталкиваются с проблемами, связанными с проблемой «галлюцинаций», присущей большим моделям, потенциальными цепочками рассуждений в сложных задачах и неправильным использованием инструментов, которые составляют границы возможностей агентов.

Чтобы лучше организовать процессы «мышления» и «действия» агентов, в отрасли появилось множество классических архитектурных парадигм. В этой главе мы сосредоточимся на трех наиболее типичных из них и реализуем их шаг за шагом с нуля:

- **ReAct (рассуждение и действие):** парадигма, которая тесно сочетает в себе «мышление» и «действие», позволяя агентам думать во время действий и динамически приспосабливаться.
- **Планируй и решай**.** Парадигма «думай, прежде чем действовать», при которой агенты сначала создают полный план действий, а затем строго его выполняют.
- **Рефлексия**. Парадигма, которая наделяет агентов способностью «размышлять», оптимизируя результаты посредством самокритики и исправлений.

Поняв это, вы можете спросить: если уже доступно множество отличных фреймворков, таких как LangChain и LlamaIndex, зачем «изобретать велосипед»? Ответ заключается в том, что, хотя зрелые структуры имеют значительные преимущества в эффективности проектирования, прямое использование высокоабстрагированных инструментов не помогает нам понять, как работают лежащие в основе механизмы проектирования или какие преимущества они предлагают. Во-вторых, этот процесс выявляет инженерные проблемы в проектах. Платформы решают за нас многие проблемы, такие как анализ выходных форматов модели, повторение неудачных вызовов инструментов и предотвращение попадания агентов в бесконечные циклы. Решение этих проблем на собственном опыте — это самый прямой способ развить способности к проектированию систем. Наконец, что наиболее важно, освоение принципов проектирования позволяет вам по-настоящему превратиться из «пользователя» фреймворка в «создателя» интеллектуальных приложений. Если стандартные компоненты не могут удовлетворить ваши сложные потребности, у вас будет возможность глубоко настроить или даже создать совершенно новый агент с нуля.

## 4.1 Подготовка среды и определение основного инструмента

Прежде чем мы начнем сборку, нам необходимо настроить среду разработки и определить некоторые основные компоненты. Это поможет нам избежать повторяющейся работы и больше сосредоточиться на основной логике при последующей реализации различных парадигм.

### 4.1.1 Установка зависимостей

В практической части этой книги в основном будет использоваться язык Python, рекомендуется Python 3.10 или выше. Сначала убедитесь, что вы установили`openai`библиотека для взаимодействия с большими языковыми моделями и`python-dotenv`библиотека для безопасного управления нашими ключами API.

Запустите следующую команду в своем терминале:

```bash
pip install openai python-dotenv
```

### 4.1.2 Настройка ключей API

Чтобы сделать код универсальнее, параметры сервиса модели (model ID, API-ключ, адрес сервиса) задаём единообразно через переменные окружения.

1. В корневом каталоге вашего проекта создайте файл с именем `.env`.
2. В этот файл добавьте следующее содержимое. Вы можете указать его на официальном сервисе OpenAI или на любом местном/стороннем сервисе, совместимом с интерфейсом OpenAI, в соответствии с вашими потребностями.
3. Если вы действительно не знаете, как его получить, вы можете обратиться к [Конфигурации среды] (https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra07-环境配置.md).

```bash
# .env file
LLM_API_KEY="YOUR-API-KEY"
LLM_MODEL_ID="YOUR-MODEL"
LLM_BASE_URL="YOUR-URL"
```

Наш код автоматически загрузит эти конфигурации из этого файла.

### 4.1.3 Инкапсуляция базовых функций вызова LLM

Чтобы сделать структуру кода более понятной и более пригодной для повторного использования, давайте определим специальный клиентский класс LLM. Этот класс будет инкапсулировать все детали взаимодействия с модельными сервисами, позволяя нашей основной логике больше сосредоточиться на создании агентов.

```python
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables from .env file
load_dotenv()

class HelloAgentsLLM:
    """
    A customized LLM client for the book "Hello Agents".
    It is used to call any service compatible with the OpenAI interface and uses streaming responses by default.
    """
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        """
        Initialize the client. Prioritize passed parameters; if not provided, load from environment variables.
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("Model ID, API key, and service address must be provided or defined in the .env file.")

        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        Call the large language model to think and return its response.
        """
        print(f"🧠 Calling {self.model} model...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            # Handle streaming response
            print("✅ Large language model response successful:")
            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print()  # Newline after streaming output ends
            return "".join(collected_content)

        except Exception as e:
            print(f"❌ Error occurred when calling LLM API: {e}")
            return None

# --- Client Usage Example ---
if __name__ == '__main__':
    try:
        llmClient = HelloAgentsLLM()
        
        exampleMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "Write a quicksort algorithm"}
        ]
        
        print("--- Calling LLM ---")
        responseText = llmClient.think(exampleMessages)
        if responseText:
            print("\n\n--- Complete Model Response ---")
            print(responseText)

    except ValueError as e:
        print(e)


>>>
--- Calling LLM ---
🧠 Calling xxxxxx model...
✅ Large language model response successful:
Quicksort is a very efficient sorting algorithm...
```



## 4.2 Реакт

После подготовки клиента LLM мы построим первую и самую классическую парадигму агента: **ReAct (Причина + Действие)**. ReAct был предложен Шуньюй Яо в ​​2022 году<sup>[1]</sup>. Его основная идея — имитировать то, как люди решают проблемы, путем явного объединения **Рассуждений** и **Действий**, образуя цикл «думай-действуй-наблюдай».

### 4.2.1 Рабочий процесс ReAct

До появления ReAct основные методы можно было разделить на две категории: одна — это тип «чистого мышления», такой как **Цепочка мыслей**, который может направлять модели для выполнения сложных логических рассуждений, но не может взаимодействовать с внешним миром и склонен к фактическим галлюцинациям; другой — тип «чистого действия», когда модели напрямую выводят действия для выполнения, но им не хватает возможностей планирования и исправления ошибок.

Гениальность ReAct заключается в признании того, что **мышление и действие дополняют друг друга**. Мышление направляет действие, а действие, в свою очередь, приводит к правильному мышлению. С этой целью парадигма ReAct использует специальную разработку подсказок, которая направляет модель так, чтобы каждый шаг ее результатов следовал фиксированной траектории:

- **Мысль (Мышление):** Это «внутренний монолог» агента. Он анализирует текущую ситуацию, декомпозирует задачи, формулирует следующий план или размышляет о результатах предыдущего шага.
- **Действие (действующее):** Это конкретное действие, которое агент решает предпринять, обычно вызывая внешний инструмент, например «Поиск['последний телефон Huawei']».
- **Наблюдение (Наблюдение):** Это результат, возвращаемый внешним инструментом после выполнения «Действия», например сводка результатов поиска или возвращаемое значение API.

Агент будет постоянно повторять этот цикл **Мысль -> Действие -> Наблюдение**, добавляя новые результаты наблюдения в историю, чтобы сформировать постоянно растущий контекст, пока он не определится в`Thought`что он нашел окончательный ответ и затем выводит результат. Этот процесс образует мощную синергию: **рассуждение делает действия более целенаправленными, а действия обеспечивают фактическую основу для рассуждений.**

Мы можем формально выразить этот процесс, как показано на рисунке 4.1. В частности, на каждом временном шаге $t$ политика агента (т. е. большая языковая модель $\pi$) генерирует текущую мысль $th_t$ и действие $a_t$ на основе исходного вопроса $q$ и исторической траектории всех предыдущих шагов «действия-наблюдения» $((a_1,o_1),\dots,(a_{t-1},o_{t-1}))$:

$$\left(th_t,a_t\right)=\pi\left(q,(a_1,o_1),\ldots,(a_{t-1},o_{t-1})\right)$$

Впоследствии инструмент $T$ в среде выполняет действие $a_t$ и возвращает новый результат наблюдения $o_t$:

$$o_t = Т(a_t)$$

Этот цикл продолжается, добавляя в историю новые пары $(a_t,o_t)$ до тех пор, пока модель мысленно не определит $th_t$, что задача выполнена.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/4-figures/4-1.png" alt="Think-Act-Observe synergistic loop in ReAct paradigm" width="90%"/>
  <p>Рисунок 4.1. Синергический цикл «думай-действуй-наблюдай» в парадигме ReAct</p>
</div>

Этот механизм особенно подходит для следующих сценариев:

- **Задачи, требующие внешних знаний**: например, запрос информации в реальном времени (погода, новости, цены на акции), поиск знаний в профессиональных областях и т. д.
- **Задачи, требующие точных расчетов**: делегирование математических задач калькуляторам, чтобы избежать ошибок в расчетах LLM.
- **Задачи, требующие взаимодействия с API**: например, работа с базами данных, вызов API службы для выполнения определенных функций.

Поэтому мы создадим агент ReAct с возможностью **использовать внешние инструменты** для ответа на вопросы, на которые большие языковые модели не могут напрямую ответить, используя только свою собственную базу знаний. Например: «Какой последний телефон Huawei? Каковы его основные преимущества?» Этот вопрос требует от агента понимания того, что ему необходимо выполнить поиск в Интернете, вызвать инструменты для поиска результатов и обобщить ответ.

### 4.2.2 Определение и реализация инструмента

Если большие языковые модели — это мозг агента, то **Инструменты** — это его «руки и ноги» для взаимодействия с внешним миром. Чтобы парадигма ReAct действительно могла решить поставленные нами задачи, агенту необходима возможность вызывать внешние инструменты.

Для достижения цели, поставленной в этом разделе — ответить на вопросы о «последнем телефоне Huawei» — нам необходимо предоставить агенту инструмент веб-поиска. Здесь мы выбираем **SerpApi**, который предоставляет структурированные результаты поиска Google через API и может напрямую возвращать «поля со сводкой ответов» или точную информацию о диаграмме знаний.

Сначала вам нужно установить библиотеку:

```bash
pip install google-search-results
```

При этом вам необходимо зайти на [официальный сайт SerpApi](https://serpapi.com/), чтобы зарегистрировать бесплатную учетную запись, получить ключ API и добавить его в`.env`файл в корневом каталоге нашего проекта:

```bash
# .env file
# ... (Keep previous LLM configuration)
SERPAPI_API_KEY="YOUR_SERPAPI_API_KEY"
```

Далее мы определим этот инструмент и будем управлять им с помощью кода. Мы будем действовать шаг за шагом: сначала реализуем основные функции инструмента, затем создадим общий менеджер инструментов.

(1) Реализация основной логики инструмента поиска

Четко определенный инструмент должен содержать следующие три основных элемента:

1. **Имя**: краткий уникальный идентификатор агента, который будет вызываться в «Действии», например «Поиск».
2. **Описание**: четкое описание на естественном языке, объясняющее назначение этого инструмента. **Это наиболее важная часть всего механизма**, поскольку модель большого языка будет полагаться на это описание, чтобы определить, когда какой инструмент использовать.
3. **Логика выполнения**: функция или метод, который фактически выполняет задачу.

Наш первый инструмент —`search`функция, которая получает строку запроса и затем возвращает результаты поиска.

```python
from serpapi import SerpApiClient

def search(query: str) -> str:
    """
    A practical web search engine tool based on SerpApi.
    It intelligently parses search results, prioritizing direct answers or knowledge graph information.
    """
    print(f"🔍 Executing [SerpApi] web search: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "Error: SERPAPI_API_KEY not configured in .env file."

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # Country code
            "hl": "zh-cn", # Language code
        }
        
        client = SerpApiClient(params)
        results = client.get_dict()
        
        # Intelligent parsing: prioritize finding the most direct answer
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # If no direct answer, return summaries of the first three organic results
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        
        return f"Sorry, no information found about '{query}'."

    except Exception as e:
        return f"Error occurred during search: {e}"
```

В приведенном выше коде сначала проверяется,`answer_box`(окно со сводкой ответов Google) или`knowledge_graph`(граф знаний) информация существует. Если да, то он напрямую возвращает наиболее точные ответы. В противном случае возвращается сводка первых трех результатов обычного поиска. Этот «интеллектуальный анализ» может обеспечить более качественный ввод информации для LLM.

(2) Создание универсального исполнителя инструментов

Когда агенту необходимо использовать несколько инструментов (например, помимо поиска ему могут понадобиться еще расчеты, запросы к базе данных и т. д.), нам нужен единый менеджер для регистрации и отправки этих инструментов. Для этого мы создаем`ToolExecutor`сорт.

```python
from typing import Dict, Any

class ToolExecutor:
    """
    A tool executor responsible for managing and executing tools.
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        """
        Register a new tool in the toolbox.
        """
        if name in self.tools:
            print(f"Warning: Tool '{name}' already exists and will be overwritten.")
        self.tools[name] = {"description": description, "func": func}
        print(f"Tool '{name}' registered.")

    def getTool(self, name: str) -> callable:
        """
        Get a tool's execution function by name.
        """
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """
        Get a formatted description string of all available tools.
        """
        return "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])

```

(3) Тестирование

Теперь мы зарегистрируем`search`инструмент в`ToolExecutor`и смоделировать вызов, чтобы убедиться, что весь процесс работает правильно.

```python
# --- Tool Initialization and Usage Example ---
if __name__ == '__main__':
    # 1. Initialize tool executor
    toolExecutor = ToolExecutor()

    # 2. Register our practical search tool
    search_description = "A web search engine. Use this tool when you need to answer questions about current events, facts, and information not found in your knowledge base."
    toolExecutor.registerTool("Search", search_description, search)

    # 3. Print available tools
    print("\n--- Available Tools ---")
    print(toolExecutor.getAvailableTools())

    # 4. Agent's Action call, this time we ask a real-time question
    print("\n--- Execute Action: Search['What is NVIDIA's latest GPU model'] ---")
    tool_name = "Search"
    tool_input = "What is NVIDIA's latest GPU model"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- Observation ---")
        print(observation)
    else:
        print(f"Error: Tool named '{tool_name}' not found.")

>>>
Tool 'Search' registered.

--- Available Tools ---
- Search: A web search engine. Use this tool when you need to answer questions about current events, facts, and information not found in your knowledge base.

--- Execute Action: Search['What is NVIDIA's latest GPU model'] ---
🔍 Executing [SerpApi] web search: What is NVIDIA's latest GPU model
--- Observation ---
[1] GeForce RTX 50 Series Graphics Cards
GeForce RTX™ 50 Series GPUs are powered by NVIDIA Blackwell architecture, bringing new gameplay for gamers and creators. RTX 50 Series has powerful AI computing power, bringing upgraded experience and more realistic graphics.

[2] Compare GeForce Series Latest Generation and Previous Generation Graphics Cards
Compare the latest RTX 30 series graphics cards with previous RTX 20 series, GTX 10 and 900 series graphics cards. View specifications, features, technical support, etc.

[3] GeForce Graphics Cards | NVIDIA
DRIVE AGX. Powerful in-vehicle computing power for AI-driven intelligent vehicle systems · Clara AGX. AI computing for innovative medical devices and imaging. Gaming and Creation. GeForce. Explore graphics cards, gaming solutions, AI ...
```

На данный момент мы снабдили агента`Search`инструмент, который подключается к реальному Интернету, обеспечивая прочную основу для последующего цикла ReAct.



### 4.2.3 Кодирование реализации агента ReAct

Теперь мы соберем все независимые компоненты — клиент LLM и исполнитель инструмента — для создания полноценного агента ReAct. Мы инкапсулируем его основную логику через`ReActAgent`сорт. Для простоты понимания мы разобьем процесс реализации этого класса на следующие ключевые части для объяснения.

(1) Проектирование системы

Подсказка является краеугольным камнем всего механизма ReAct, предоставляя инструкции по работе с большой языковой моделью. Нам необходимо тщательно разработать шаблон, который будет динамически вставлять доступные инструменты, вопросы пользователей и историю взаимодействия на промежуточных шагах.

```bash
# ReAct Prompt Template
REACT_PROMPT_TEMPLATE = """
Please note that you are an intelligent assistant capable of calling external tools.

Available tools are as follows:
{tools}

Please respond strictly in the following format:

Thought: Your thinking process, used to analyze problems, decompose tasks, and plan the next action.
Action: The action you decide to take, must be in one of the following formats:
- {{tool_name}}[{{tool_input}}]`: Call an available tool.
- `Finish[final answer]`: When you believe you have obtained the final answer.
- When you have collected enough information to answer the user's final question, you must use `Finish[final answer]` after the Action: field to output the final answer.

Now, please start solving the following problem:
Question: {question}
History: {history}
"""
```

Этот шаблон определяет спецификацию взаимодействия между агентом и LLM:

- **Определение роли**: «Вы умный помощник, способный вызывать внешние инструменты» определяет роль LLM.
- **Список инструментов (`{tools}`)**: сообщает LLM, какие «руки и ноги» у него есть в наличии.
- **Соглашение о формате («Мысль»/«Действие»)**: это самая важная часть, заставляющая структурировать выходные данные LLM, чтобы мы могли точно проанализировать его намерения через код.
- **Динамический контекст (`{question}`/`{history}`)**: добавляет исходный вопрос пользователя и постоянно накапливаемую историю взаимодействия, что позволяет LLM принимать решения на основе полного контекста.

(2) Реализация основного цикла

Ядро`ReActAgent`представляет собой цикл, который непрерывно «форматирует приглашение -> вызывает LLM -> выполняет действие -> интегрирует результаты» до тех пор, пока задача не будет завершена или не будет достигнут максимальный предел шагов.

```python
class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str):
        """
        Run the ReAct agent to answer a question.
        """
        self.history = [] # Reset history for each run
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"--- Step {current_step} ---")

            # 1. Format prompt
            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_desc,
                question=question,
                history=history_str
            )

            # 2. Call LLM to think
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)

            if not response_text:
                print("Error: LLM failed to return a valid response.")
                break

            # ... (Subsequent parsing, execution, integration steps)

```

The `run`Метод является точкой входа агента. Его`while`цикл составляет основную часть парадигмы ReAct, а`max_steps`Параметр является важным предохранительным клапаном, предотвращающим попадание агента в бесконечный цикл и исчерпание ресурсов.

(3) Реализация выходного анализатора

LLM возвращает обычный текст, и нам нужно точно извлечь`Thought`и`Action`от этого. Это достигается с помощью нескольких вспомогательных функций синтаксического анализа, которые обычно используют регулярные выражения.

```python
# (These methods are part of the ReActAgent class)
    def _parse_output(self, text: str):
        """Parse LLM output to extract Thought and Action.
        """
        # Thought: match until Action: or end of text
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: match until end of text
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        """Parse Action string to extract tool name and input.
        """
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return None, None
```

- `_parse_output`: отвечает за разделение двух основных частей «Мысль» и «Действие» из полного ответа LLM.
- `_parse_action`: отвечает за дальнейший анализ строки "Действие", например, извлечение имени инструмента "Поиск" и входных данных инструмента "Последний телефон Huawei" из "Поиск [последний телефон Huawei]".

(4) Вызов и выполнение инструмента

```python
# (This logic is inside the while loop of the run method)
            # 3. Parse LLM output
            thought, action = self._parse_output(response_text)

            if thought:
                print(f"Thought: {thought}")

            if not action:
                print("Warning: Failed to parse valid Action, process terminated.")
                break

            # 4. Execute Action
            if action.startswith("Finish"):
                # If it's a Finish instruction, extract the final answer and end
                final_answer = re.match(r"Finish\[(.*)\]", action).group(1)
                print(f"🎉 Final Answer: {final_answer}")
                return final_answer

            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                # ... Handle invalid Action format ...
                continue

            print(f"🎬 Action: {tool_name}[{tool_input}]")

            tool_function = self.tool_executor.getTool(tool_name)
            if not tool_function:
                observation = f"Error: Tool named '{tool_name}' not found."
            else:
                observation = tool_function(tool_input) # Call real tool

```

Этот код является центром выполнения`Action`. Сначала он проверяет, является ли это`Finish`инструкция; если да, то процесс завершается. В противном случае он получает соответствующую функцию инструмента через`tool_executor`и выполняет его, чтобы получить`observation`.

(5) Интегрирование результатов наблюдений

Последний шаг и ключ к формированию замкнутого цикла — добавление`Action`себя и`Observation`после выполнения инструмента возвращается в историю, предоставляя новый контекст для следующего цикла.

```python
# (This logic follows tool invocation, at the end of the while loop)
            print(f"👀 Observation: {observation}")

            # Add this round's Action and Observation to history
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        # Loop ends
        print("Maximum steps reached, process terminated.")
        return None
```

Добавив`Observation`к`self.history`, агент может «увидеть» результаты предыдущего действия при создании подсказки в следующем раунде и соответствующим образом провести новое обдумывание и планирование.

(6) Запуск экземпляра и анализ

Объединив все вышеперечисленные части, мы получаем полную`ReActAgent`сорт. Полный экземпляр выполняемого кода можно найти в`code`папка репозитория сопроводительного кода этой книги.

Ниже приведен реальный рекорд бега:

```
Tool 'Search' registered.

--- Step 1 ---
🧠 Calling xxxxxx model...
✅ Large language model response successful:
Thought: To answer this question, I need to search for Huawei's latest released phone model and its main features. This information may be outside my existing knowledge base, so I need to use a search engine to obtain the latest data.
Action: Search[Huawei latest phone model and main selling points]
🤔 Thought: To answer this question, I need to search for Huawei's latest released phone model and its main features. This information may be outside my existing knowledge base, so I need to use a search engine to obtain the latest data.
🎬 Action: Search[Huawei latest phone model and main selling points]
🔍 Executing [SerpApi] web search: Huawei latest phone model and main selling points
👀 Observation: [1] Huawei Phones - Huawei Official Website
Smartphones ; Mate Series. Extraordinary Flagship · HUAWEI Mate XTs. Extraordinary Master ; Pura Series. Pioneer Imaging · HUAWEI Pura 80 Pro+ ; Pocket Series. Aesthetic New Chapter. HUAWEI Pocket 2 ; nova Series. Professional Portrait.

[2] Which Huawei phone has the best value in 2025? Huawei phone recommendations and market analysis ...
Now the biggest selling point of Huawei phones is only the HarmonyOS system, and the controversial brand faith. Here are several Huawei series phones worth buying, choose according to different budgets:. Huawei's currently most popular, also equipped with ...

[3] Which new Huawei phone has the best value in 2025? 10 new Huawei phone recommendations
Choosing Huawei mainly recommends high-end phones, Mate 70 and Pura 70 series are the latest flagship models. HUAWEI Mate 70. Advantages are, photography configuration is still top-level, full focal length coverage, suitable for professional photography, excellent workmanship, outdoor drop resistance ...

--- Step 2 ---
🧠 Calling xxxxxx model...
✅ Large language model response successful:
Thought: Based on the search results, Huawei's latest flagship models include Mate 70 and Pura 80 Pro+. To determine the latest model and its main selling points, I will focus on this information. From the provided links, both Mate 70 series and Pura 80 Pro+ are recently released products, but which one is "latest" needs further confirmation. Meanwhile, I can extract their main selling points from this information.
Action: Finish[According to the latest information, Huawei's latest phones may be HUAWEI Pura 80 Pro+ or HUAWEI Mate 70. Among them, HUAWEI Mate 70's main selling points include top-level photography configuration, full focal length coverage, suitable for professional photography, excellent workmanship, and good outdoor drop resistance. While HUAWEI Pura 80 Pro+ emphasizes pioneer imaging technology.]
🤔 Thought: Based on the search results, Huawei's latest flagship models include Mate 70 and Pura 80 Pro+. To determine the latest model and its main selling points, I will focus on this information. From the provided links, both Mate 70 series and Pura 80 Pro+ are recently released products, but which one is "latest" needs further confirmation. Meanwhile, I can extract their main selling points from this information.
🎉 Final Answer: According to the latest information, Huawei's latest phones may be HUAWEI Pura 80 Pro+ or HUAWEI Mate 70. Among them, HUAWEI Mate 70's main selling points include top-level photography configuration, full focal length coverage, suitable for professional photography, excellent workmanship, and good outdoor drop resistance. While HUAWEI Pura 80 Pro+ emphasizes pioneer imaging technology.
```

Из приведенного выше вывода мы видим, что агент четко демонстрирует свою цепочку мыслей: сначала он понимает, что его знаний недостаточно, и ему необходимо использовать инструмент поиска; затем он рассуждает и обобщает результаты поиска, получая окончательный ответ за два шага.

Стоит отметить, что, поскольку знания модели и информация в Интернете постоянно обновляются, результаты вашего бега могут быть не такими, как сейчас. По состоянию на 8 сентября 2025 года, когда был написан этот раздел, HUAWEI Mate 70 и HUAWEI Pura 80 Pro+, упомянутые в результатах поиска, действительно были телефонами последней флагманской серии Huawei на тот момент. Это в полной мере демонстрирует мощные возможности парадигмы ReAct в решении срочных задач.

### 4.2.4 Характеристики, ограничения и методы отладки ReAct

Внедрив агент ReAct из первых рук, мы не только освоили его рабочий процесс, но и должны глубже понять его внутренние механизмы. Любая техническая парадигма имеет свои особенности и области для улучшения; в этом разделе будет подведен итог ReAct.

(1) Основные характеристики ReAct

1. **Высокая интерпретируемость**. Одним из самых больших преимуществ ReAct является прозрачность. Через цепочку «Мысль» мы можем ясно увидеть «мысленное путешествие» агента на каждом этапе — почему он выбрал этот инструмент и что он планирует делать дальше. Это имеет решающее значение для понимания, доверия и отладки поведения агента.
2. **Возможность динамического планирования и исправления ошибок**. В отличие от парадигм, которые создают полные планы одновременно, ReAct действует по принципу «сделай один шаг, взгляни на один шаг». Он динамически корректирует последующие «Мысли» и «Действия» на основе «Наблюдений», полученных из внешнего мира на каждом этапе. Если предыдущие результаты поиска неудовлетворительны, можно исправить условия поиска на следующем этапе и повторить попытку.
3. **Возможность синергии инструментов**: парадигма ReAct естественным образом сочетает в себе возможности рассуждения больших языковых моделей с возможностями выполнения внешних инструментов. LLM отвечают за разработку стратегии (планирование и рассуждение), инструменты отвечают за решение конкретных проблем (поиск, расчет), и оба работают синергетически, преодолевая присущие отдельным LLM ограничения в своевременности знаний, точности вычислений и т. д.

(2) Неотъемлемые ограничения ReAct

1. **Сильная зависимость от собственных возможностей LLM**: Успех процесса ReAct во многом зависит от комплексных возможностей основного LLM. Если способность LLM к логическому рассуждению, способности следовать инструкциям или способности форматированного вывода недостаточна, легко осуществить неправильное планирование на этапе «Мысль» или сгенерировать инструкции, которые не соответствуют формату на этапе «Действие», что приведет к прерыванию всего процесса.
2. **Проблемы с эффективностью выполнения**. Из-за поэтапного характера выполнения задачи обычно требуется несколько вызовов LLM. Каждый вызов сопровождается задержкой в ​​сети и вычислительными затратами. Для сложных задач, требующих большого количества шагов, этот последовательный цикл «думай-действуй» может привести к увеличению общего времени и затрат.
3. **Хрупкость подсказок**: Стабильная работа всего механизма построена на тщательно разработанном шаблоне подсказок. Любое незначительное изменение в шаблоне, даже различия в формулировках, может повлиять на поведение LLM. Кроме того, не все модели могут последовательно следовать заданным форматам, что увеличивает неопределенность в практическом применении.
4. **Может попасть в локальный оптимум**. Пошаговый режим принятия решений означает, что у агента отсутствует глобальный долгосрочный план. Он может выбрать путь, который кажется правильным в краткосрочной перспективе, но неоптимальным в долгосрочной перспективе из-за немедленного «наблюдения», или даже в некоторых случаях попасть в цикл «вращения на месте».

(3) Методы отладки

Если встроенный агент ReAct ведет себя неожиданно, вы можете выполнить отладку по следующим аспектам:

- **Проверьте полную подсказку**: перед каждым звонком в LLM распечатывайте окончательную отформатированную полную подсказку, содержащую всю историю. Это самый прямой способ отследить источник решений LLM.
- **Анализ необработанного вывода**: если синтаксический анализ вывода не удался (например, регулярные выражения не соответствуют «Действию»), обязательно распечатайте необработанный необработанный текст, возвращенный LLM. Это может помочь вам определить, не соответствует ли LLM формату или ваша логика синтаксического анализа неверна.
- **Проверка входных и выходных данных инструмента**: проверьте, находится ли `tool_input`, сгенерированный агентом, в формате, ожидаемом функцией инструмента, а также убедитесь, что `наблюдение`, возвращаемое инструментом, находится в формате, который агент может понять и обработать.
- **Корректировка примеров в подсказке (подсказка из нескольких шагов)**: если модель часто допускает ошибки, вы можете добавить в подсказку один или два полных успешных случая «мысль-действие-наблюдение», чтобы помочь модели лучше следовать вашим инструкциям с помощью примеров.
- **Попробуйте разные модели или параметры**: переключение на более мощную модель или настройку параметра «температура» (обычно установленного на 0, чтобы обеспечить детерминированность выходного сигнала) иногда может напрямую решить проблему.

## 4.3 Планирование и решение

После освоения ReAct, этой реактивной, пошаговой парадигмы агента, принимающего решения, мы затем рассмотрим метод совершенно другого стиля, но не менее мощный: **Планируй и решай**. Как следует из названия, эта парадигма явно делит обработку задач на два этапа: **Сначала планируй, затем решай**.

Если ReAct похож на опытного детектива, который шаг за шагом рассуждает на основе улик на месте происшествия (наблюдение) и в любой момент корректирует направление расследования; тогда Plan-and-Solve больше похож на архитектора, который должен сначала нарисовать полный проект (Plan) перед началом строительства, а затем строить строго по чертежу (Solve). Фактически, режимы агента многих инструментов для больших моделей, которые мы используем, теперь включают этот шаблон проектирования.

### 4.3.1 Принцип работы «Планируй и решай»

Подсказки «Планируй и решай» были предложены Лэй Ваном в 2023 году<sup>[2]</sup>. Его основная мотивация — решить проблему, заключающуюся в том, что цепочка мыслей легко «сбивается с пути» при решении многоэтапных и сложных задач.

В отличие от ReAct, который объединяет мышление и действие на каждом этапе, Plan-and-Solve разделяет весь процесс на два основных этапа, как показано на рисунке 4.2:

1. **Этап планирования**. Сначала агент получает полный вопрос пользователя. Его первая задача — не напрямую решить проблему или вызвать инструменты, а **декомпозировать проблему и сформулировать четкий пошаговый план действий**. Этот план сам по себе является результатом вызова большой языковой модели.
2. **Этап решения**: после получения полного плана агент переходит к этапу выполнения. Он будет выполняться **строго в соответствии с шагами плана, один за другим**. Выполнение каждого шага может представлять собой независимый вызов LLM или обработку результатов предыдущего шага до тех пор, пока все шаги плана не будут завершены и не будет получен окончательный ответ.

Эта стратегия «планируй, прежде чем действовать» позволяет агенту поддерживать более высокую согласованность целей при выполнении сложных задач, требующих долгосрочного планирования, избегая потери на промежуточных шагах.

Мы можем формально выразить этот двухэтапный процесс. Сначала модель планирования $\pi_{\text{plan}}$ генерирует план $P = (p_1, p_2, \dots, p_n)$, содержащий $n$ шагов, на основе исходного вопроса $q$:

$$
P = \pi_{\text{plan}}(q)
$$

Впоследствии, на этапе выполнения, модель выполнения $\pi_{\text{solve}}$ выполнит шаги плана один за другим. Для $i$-го шага построение его решения $s_i$ будет зависеть от исходного вопроса $q$, полного плана $P$ и результатов выполнения всех предыдущих шагов $(s_1, \dots, s_{i-1})$:

$$
s_i = \pi_{\text{solve}}(q, P, (s_1, \dots, s_{i-1}))
$$

Окончательный ответ — это результат выполнения последнего шага $s_n$.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/4-figures/4-2.png" alt="Two-stage workflow of Plan-and-Solve paradigm" width="90%"/>
  <p>Рисунок 4.2 Двухэтапный рабочий процесс парадигмы «планируй и решай»</p>
</div>

Plan-and-Solve особенно подходит для сложных задач с четкой структурой, которые можно четко разложить, например:

- **Многоэтапные математические задачи**: необходимо сначала перечислить этапы расчета, а затем решать их один за другим.
- **Написание отчета с интеграцией нескольких источников информации**: необходимо сначала спланировать структуру отчета (введение, источник данных A, источник данных B, резюме), а затем заполнять содержимое по одному.
- **Задачи по генерации кода**: необходимо сначала придумать структуру функций, классов и модулей, а затем реализовать их по одному.

### 4.3.2 Этап планирования

Чтобы подчеркнуть преимущества парадигмы «Планируй и решай» в задачах структурированного рассуждения, мы не будем использовать инструменты, а выполним задачу рассуждения посредством быстрого проектирования.

Характерной чертой задач этого типа является то, что ответ невозможно получить с помощью одного запроса или вычисления; проблему необходимо сначала разложить на ряд логически последовательных подэтапов, а затем решить по порядку. Это в точности использует основную возможность Plan-and-Solve: «сначала планируй, потом выполняй».

**Наша целевая задача:** «В понедельник в фруктовом магазине было продано 15 яблок. Во вторник было продано в два раза больше яблок, чем в понедельник. В среду было продано на 5 яблок меньше, чем во вторник. Сколько всего яблок было продано за эти три дня?»

Эта задача не представляет особой сложности для больших языковых моделей, но содержит четкую логическую цепочку для справки. Для некоторых реальных логических головоломок, если большая модель не может дать точные и качественные ответы, вы можете обратиться к этому шаблону проектирования, чтобы создать собственного агента для выполнения задачи. Агенту необходимо:

1. **Этап планирования**. Сначала разбейте задачу на три независимых этапа расчета (расчет продаж во вторник, расчет продаж в среду, расчет общего объема продаж).
2. **Фаза выполнения**. Затем строго следуйте плану, выполняйте вычисления шаг за шагом и используйте результат каждого шага в качестве входных данных для следующего шага, в конечном итоге получая итоговую сумму.

Цель этапа планирования — получить от большой языковой модели исходную проблему и выдать четкий пошаговый план действий. Этот план должен быть структурирован так, чтобы наш код мог легко анализировать и выполнять его один за другим. Таким образом, приглашение, которое мы разрабатываем, должно четко указывать модели ее роль и задачу, а также предоставлять пример выходного формата.

````python
PLANNER_PROMPT_TEMPLATE = """
You are a top AI planning expert. Your task is to decompose complex problems posed by users into an action plan consisting of multiple simple steps.
Please ensure that each step in the plan is an independent, executable subtask and is strictly arranged in logical order.
Your output must be a Python list, where each element is a string describing a subtask.

Question: {question}

Please strictly output your plan in the following format, with ```питон и``` as prefix and suffix being necessary:
```питон
["Шаг 1", "Шаг 2", "Шаг 3", ...]
```
"""
````

Это приглашение обеспечивает качество и стабильность вывода за счет следующих моментов:
- **Настройка роли**: «Лучший эксперт по планированию ИИ» активирует профессиональные возможности модели.
- **Описание задачи**: Четко определяет цель «декомпозиции проблем».
- **Ограничение формата**: выводит строку в формате списка Python, что значительно упрощает последующую работу по синтаксическому анализу кода, делая его более стабильным и надежным, чем синтаксический анализ естественного языка.

Далее мы инкапсулируем эту логику подсказки в`Planner`class, который также является нашим планировщиком.

```python
# Assume the HelloAgentsLLM class in llm_client.py is already defined
# from llm_client import HelloAgentsLLM

class Planner:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        """
        Generate an action plan based on user question.
        """
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)

        # To generate a plan, we build a simple message list
        messages = [{"role": "user", "content": prompt}]

        print("--- Generating Plan ---")
        # Use streaming output to get the complete plan
        response_text = self.llm_client.think(messages=messages) or ""

        print(f"✅ Plan Generated:\n{response_text}")

        # Parse the list string output by LLM
        try:
            # Find content between ```питон и```
            plan_str = response_text.split("```питон")[1].split("```")[0].strip()
            # Use ast.literal_eval to safely execute the string and convert it to a Python list
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"❌ Error parsing plan: {e}")
            print(f"Raw response: {response_text}")
            return []
        except Exception as e:
            print(f"❌ Unknown error occurred while parsing plan: {e}")
            return []
```

### 4.3.3 Исполнитель и управление состоянием

После планировщика (`Planner`) генерирует четкий план действий, нам нужен исполнитель (`Executor`) для выполнения задач плана одно за другим. Исполнитель не только отвечает за вызов большой языковой модели для решения каждой подзадачи, но также играет решающую роль: **управление состоянием**. Он должен записывать результаты выполнения каждого шага и предоставлять их в качестве контекста для последующих шагов, обеспечивая плавное движение информации по всей цепочке задач.

Подсказка исполнителя отличается от подсказки планировщика. Его цель — не разложить проблемы на составляющие, а **сосредоточиться на решении текущего шага на основе существующего контекста**. Поэтому приглашение должно включать следующую ключевую информацию:

- **Оригинальный вопрос**. Убедитесь, что модель всегда понимает конечную цель.
- **Полный план**: позвольте модели понять положение текущего шага во всей задаче.
- **Исторические шаги и результаты**: укажите выполненную на данный момент работу в качестве прямых входных данных для текущего шага.
- **Текущий этап**. Четко проинструктируйте модель, какую конкретную задачу ей необходимо решить сейчас.

```python
EXECUTOR_PROMPT_TEMPLATE = """
You are a top AI execution expert. Your task is to strictly follow the given plan and solve the problem step by step.
You will receive the original question, the complete plan, and the steps and results completed so far.
Please focus on solving the "current step" and only output the final answer for that step, without any additional explanations or dialogue.

# Original Question:
{question}

# Complete Plan:
{plan}

# Historical Steps and Results:
{history}

# Current Step:
{current_step}

Please only output the answer for the "current step":
"""
```

Мы инкапсулируем логику выполнения в`Executor`сорт. Этот класс будет проходить по плану, вызывать LLM и поддерживать историю (состояние).

```python
class Executor:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        """
        Execute step by step according to the plan and solve the problem.
        """
        history = "" # String to store historical steps and results

        print("\n--- Executing Plan ---")

        for i, step in enumerate(plan):
            print(f"\n-> Executing step {i+1}/{len(plan)}: {step}")

            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan=plan,
                history=history if history else "None", # If it's the first step, history is empty
                current_step=step
            )

            messages = [{"role": "user", "content": prompt}]

            response_text = self.llm_client.think(messages=messages) or ""

            # Update history for the next step
            history += f"Step {i+1}: {step}\nResult: {response_text}\n\n"

            print(f"✅ Step {i+1} completed, result: {response_text}")

        # After the loop ends, the last step's response is the final answer
        final_answer = response_text
        return final_answer
```

Теперь мы отдельно построили`Planner`ответственный за «планирование» и`Executor`ответственный за «исполнение». Последний шаг — объединить эти два компонента в единый агент.`PlanAndSolveAgent`и предоставить ему полные возможности решения проблем. Мы создадим основной класс`PlanAndSolveAgent`чья ответственность очень ясна: получить клиента LLM, инициализировать внутреннего планировщика и исполнителя и предоставить простой`run`метод для запуска всего процесса.

```python
class PlanAndSolveAgent:
    def __init__(self, llm_client):
        """
        Initialize the agent and create planner and executor instances.
        """
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self, question: str):
        """
        Run the agent's complete process: plan first, then execute.
        """
        print(f"\n--- Starting to Process Question ---\nQuestion: {question}")

        # 1. Call planner to generate plan
        plan = self.planner.plan(question)

        # Check if plan was successfully generated
        if not plan:
            print("\n--- Task Terminated --- \nUnable to generate valid action plan.")
            return

        # 2. Call executor to execute plan
        final_answer = self.executor.execute(question, plan)

        print(f"\n--- Task Completed ---\nFinal Answer: {final_answer}")
```

Дизайн этого`PlanAndSolveAgent`класс воплощает в себе принцип «композиция важнее наследования». Он сам по себе не содержит сложной логики, а выступает в роли оркестратора, четко вызывая свои внутренние компоненты для выполнения задач.

### 4.3.4 Запуск экземпляра и анализ

Полный код также можно найти в`code`папка репозитория сопроводительного кода этой книги; здесь мы демонстрируем только окончательные результаты.

````bash
--- Starting to Process Question ---
Question: A fruit store sold 15 apples on Monday. The number of apples sold on Tuesday was twice that of Monday. The number sold on Wednesday was 5 fewer than Tuesday. How many apples were sold in total over these three days?
--- Generating Plan ---
🧠 Calling xxxx model...
✅ Large language model response successful:
```питон
["Рассчитать продажи яблок в понедельник: 15", "Рассчитать продажи яблок во вторник: количество в понедельник × 2 = 15 × 2 = 30", "Рассчитать продажи яблок в среду: количество во вторник - 5 = 30 - 5 = 25", "Рассчитать общий объем продаж за три дня: понедельник + вторник + среда = 15 + 30 + 25 = 70"]
```
✅ Plan Generated:
```питон
["Рассчитать продажи яблок в понедельник: 15", "Рассчитать продажи яблок во вторник: количество в понедельник × 2 = 15 × 2 = 30", "Рассчитать продажи яблок в среду: количество во вторник - 5 = 30 - 5 = 25", "Рассчитать общий объем продаж за три дня: понедельник + вторник + среда = 15 + 30 + 25 = 70"]
```

--- Executing Plan ---

-> Executing step 1/4: Calculate Monday's apple sales: 15
🧠 Calling xxxx model...
✅ Large language model response successful:
15
✅ Step 1 completed, result: 15

-> Executing step 2/4: Calculate Tuesday's apple sales: Monday's quantity × 2 = 15 × 2 = 30
🧠 Calling xxxx model...
✅ Large language model response successful:
30
✅ Step 2 completed, result: 30

-> Executing step 3/4: Calculate Wednesday's apple sales: Tuesday's quantity - 5 = 30 - 5 = 25
🧠 Calling xxxx model...
✅ Large language model response successful:
25
✅ Step 3 completed, result: 25

-> Executing step 4/4: Calculate total sales for three days: Monday + Tuesday + Wednesday = 15 + 30 + 25 = 70
🧠 Calling xxxx model...
✅ Large language model response successful:
70
✅ Step 4 completed, result: 70

--- Task Completed ---
Final Answer: 70
````

Из приведенного выше журнала результатов мы ясно видим рабочий процесс парадигмы «Планируй и решай»:

1. **Фаза планирования**: агент сначала вызывает «Планировщик» и успешно разлагает сложную задачу на слова в список Python, содержащий четыре логических шага. Этот структурированный план закладывает основу для последующего исполнения.
2. **Фаза выполнения**: «Исполнитель» строго выполняет шаг за шагом в соответствии с созданным планом. На каждом этапе он использует исторические результаты в качестве контекста, обеспечивая правильную передачу информации (например, шаг 2 правильно использует результат шага 1 «15», а шаг 3 также правильно использует результат шага 2 «30»).
3. **Результат**: Весь процесс логически понятен и содержит четкие шаги, и агент точно приходит к правильному ответу «70».

## 4.4 Размышления

В парадигмах ReAct и Plan-and-Solve, которые мы уже реализовали, как только агент выполняет задачу, его рабочий процесс завершается. Однако первоначальные ответы, которые они генерируют, будь то траектории действий или конечные результаты, могут содержать ошибки или иметь возможности для улучшения. Основная идея механизма Reflection состоит в том, чтобы ввести для агента **цикл самокоррекции**, позволяющий ему проверять свою работу, выявлять недостатки и итеративно оптимизировать, как это делают люди.

### 4.4.1 Основная идея механизма отражения

Вдохновением для создания механизма отражения послужил процесс обучения человека: мы проверяем его после завершения первого черновика и проверяем после решения математической задачи. Эта идея воплощена в многочисленных исследованиях, таких как концепция рефлексии, предложенная Шинном и Ноем в 2023 году<sup>[3]</sup>. Его основной рабочий процесс можно резюмировать как краткий трехэтапный цикл: **Выполнить -> Отразить -> Уточнить**.

1. **Выполнение**. Сначала агент пытается выполнить задачу, используя знакомые методы (например, ReAct или Plan-and-Solve), генерируя предварительное решение или траекторию действия. Это можно рассматривать как «первый проект».
2. **Рефлексия**. Затем агент вступает в фазу размышления. Он вызывает независимый экземпляр модели большого языка или экземпляр со специальными подсказками, который играет роль «рецензента». Этот «рецензент» изучает «первый черновик», созданный на первом этапе, и оценивает его по нескольким параметрам, например:
   - **Фактические ошибки**. Есть ли контент, противоречащий здравому смыслу или известным фактам?
   - **Логические ошибки**. Есть ли в процессе рассуждения несоответствия или противоречия?
   - **Проблемы с эффективностью**. Есть ли более прямой и краткий путь выполнения задачи?
   - **Недостающая информация**. Не упускаются ли из виду некоторые ключевые ограничения или аспекты проблемы? На основе оценки генерируется структурированная **обратная связь**, указывающая на конкретные проблемы и предложения по улучшению.
3. **Уточнение**. Наконец, агент использует «первый черновик» и «отзыв» в качестве нового контекста, снова вызывает большую языковую модель и просит ее пересмотреть первый черновик на основе содержимого отзыва, создавая более полный «пересмотренный черновик».

Как показано на рисунке 4.3, этот цикл можно повторять несколько раз, пока на этапе отражения не перестанут обнаруживаться новые проблемы или не будет достигнут заданный предел итераций. Мы можем формально выразить этот итеративный процесс оптимизации. Предполагая, что $O_i$ — это результат $i$-й итерации ($O_0$ — это начальный результат), модель отражения $\pi_{\text{reflect}}$ генерирует обратную связь $F_i$ для $O_i$:
$$
F_i = \pi_{\text{reflect}}(\text{Task}, O_i)
$$
Впоследствии уточняющая модель $\pi_{\text{refine}}$ объединяет исходную задачу, выходные данные предыдущей версии и обратную связь для создания выходных данных новой версии $O_{i+1}$:
$$
O_{i+1} = \pi_{\text{refine}}(\text{Task}, O_i, F_i)
$$



<div align="center">
<img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/4-figures/4-3.png" alt="Execute-Reflect-Refine iterative loop in Reflection mechanism" width="70%"/>
<p>Рисунок 4.3. Итерационный цикл «Выполнение-Отражение-Уточнение» в механизме отражения</p>
</div>



По сравнению с двумя предыдущими парадигмами ценность Reflection заключается в:

- Он предоставляет агенту внутренний цикл исправления ошибок, что делает его более не полностью зависимым от обратной связи с внешним инструментом (наблюдение ReAct), что дает возможность исправлять логические и стратегические ошибки более высокого уровня.
- Он превращает выполнение разовых задач в непрерывный процесс оптимизации, значительно повышая конечный показатель успеха и качество ответов на сложные задачи.
- Он создает временную **"краткосрочную память"** для агента. Вся траектория «выполнить-обдумать-доработать» формирует ценный опыт; агент не только знает окончательный ответ, но и помнит, как он прошел путь от ошибочного первого черновика до окончательной версии. Более того, эта система памяти также может быть **мультимодальной**, позволяя агенту размышлять и пересматривать выходные данные, выходящие за рамки текста (например, код, изображения и т. д.), закладывая основу для создания более мощных мультимодальных агентов.

### 4.4.2 Расположение корпуса и конструкция модуля памяти

Чтобы реализовать механизм Reflection на практике, мы введем механизм управления памятью, поскольку отражение обычно соответствует хранению и поиску информации. Если контекст достаточно длинный, «рецензент» напрямую получает всю информацию, а затем размышляет, что часто приводит к появлению большого количества избыточной информации. На этом практическом этапе мы в основном завершаем **генерацию кода и итеративную оптимизацию**.

Цель этого шага: «Написать функцию Python для поиска всех простых чисел от 1 до n».

Эта задача — отличный сценарий для тестирования механизма Reflection:

1. **Существует четкий путь оптимизации**. Код, изначально сгенерированный большой языковой моделью, скорее всего, представляет собой простую, но неэффективную рекурсивную реализацию.
2. **Четкие точки для размышления**. Благодаря размышлению можно обнаружить такие проблемы, как «чрезмерно высокая временная сложность» или «избыточные вычисления».
3. **Четкое направление оптимизации**. На основе отзывов его можно оптимизировать до более эффективной итеративной версии или версии, использующей шаблон запоминания.

Суть Reflection заключается в итерации, а необходимым условием для итерации является способность запоминать предыдущие попытки и полученные отзывы. Поэтому для реализации этой парадигмы необходим модуль «краткосрочной памяти». Этот модуль памяти будет отвечать за хранение полной траектории каждого цикла «выполнение-отражение».

```python
from typing import List, Dict, Any, Optional

class Memory:
    """
    A simple short-term memory module for storing the agent's action and reflection trajectory.
    """

    def __init__(self):
        """
        Initialize an empty list to store all records.
        """
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """
        Add a new record to memory.

        Parameters:
        - record_type (str): Type of record ('execution' or 'reflection').
        - content (str): Specific content of the record (e.g., generated code or reflection feedback).
        """
        record = {"type": record_type, "content": content}
        self.records.append(record)
        print(f"📝 Memory updated, added a '{record_type}' record.")

    def get_trajectory(self) -> str:
        """
        Format all memory records into a coherent string text for building prompts.
        """
        trajectory_parts = []
        for record in self.records:
            if record['type'] == 'execution':
                trajectory_parts.append(f"--- Previous Attempt (Code) ---\n{record['content']}")
            elif record['type'] == 'reflection':
                trajectory_parts.append(f"--- Reviewer Feedback ---\n{record['content']}")

        return "\n\n".join(trajectory_parts)

    def get_last_execution(self) -> Optional[str]:
        """
        Get the most recent execution result (e.g., the latest generated code).
        Returns None if it doesn't exist.
        """
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return None
```

Дизайн этого`Memory`Класс относительно краток, его основная структура выглядит следующим образом:

- Использует список «записей» для хранения каждого действия и отражения по порядку.
- Метод `add_record` отвечает за добавление новых записей в память.
- Метод get_trajectory — это ядро; он «сериализует» траекторию памяти в текстовый сегмент, который можно напрямую вставлять в последующие подсказки, обеспечивая полный контекст для отражения и оптимизации модели.
- `get_last_execution` позволяет получить последний «первый черновик» для размышления.



### 4.4.3 Кодирование реализации агента отражения

С`Memory`модуль в качестве основы, теперь мы можем приступить к созданию основной логики`ReflectionAgent`. Весь рабочий процесс агента будет вращаться вокруг цикла «выполнить-отразить-уточнить», который мы обсуждали ранее, и направлять большую языковую модель на выполнение различных ролей с помощью тщательно разработанных подсказок.

(1) Быстрый дизайн

В отличие от предыдущих парадигм, механизм отражения требует нескольких запросов для совместной работы разных ролей.

1. **Приглашение к начальному выполнению**: это приглашение для первой попытки агента решить проблему, с относительно простым содержанием, требующее только от модели выполнения указанной задачи.

```bash
INITIAL_PROMPT_TEMPLATE = """
You are a senior Python programmer. Please write a Python function according to the following requirements.
Your code must include a complete function signature, docstring, and follow PEP 8 coding standards.

Requirement: {task}

Please output the code directly without any additional explanations.
"""
```

2. **Подсказка к размышлению**: эта подсказка является душой механизма отражения. Он предписывает модели играть роль «ревьюера кода», критически анализировать код, созданный в предыдущем раунде, и предоставлять конкретную, полезную обратную связь.

````bash
REFLECT_PROMPT_TEMPLATE = """
You are an extremely strict code review expert and senior algorithm engineer with ultimate requirements for code performance.
Your task is to review the following Python code and focus on finding its main bottlenecks in <strong>algorithm efficiency</strong>.

# Original Task:
{task}

# Code to Review:
```питон
{код}
```

Please analyze the time complexity of this code and consider whether there is an <strong>algorithmically superior</strong> solution to significantly improve performance.
If one exists, please clearly point out the deficiencies of the current algorithm and propose specific, feasible algorithm improvement suggestions (e.g., using sieve method instead of trial division).
Only if the code has reached optimality at the algorithm level can you answer "no improvement needed."

Please output your feedback directly without any additional explanations.
"""
````

3. **Запрос на уточнение**: после получения отзыва этот запрос поможет модели пересмотреть и оптимизировать исходный код на основе содержания отзыва.

````bash

REFINE_PROMPT_TEMPLATE = """
You are a senior Python programmer. You are optimizing your code based on feedback from a code review expert.

# Original Task:
{task}

# Your Previous Code Attempt:
{last_code_attempt}
Reviewer's Feedback:
{feedback}

Please generate an optimized new version of the code based on the reviewer's feedback.
Your code must include a complete function signature, docstring, and follow PEP 8 coding standards.
Please output the optimized code directly without any additional explanations.
"""
````

(2) Инкапсуляция и реализация агента

Теперь мы интегрируем этот набор логики подсказок и`Memory`модуль в`ReflectionAgent`сорт.

```python
# Assume llm_client.py and memory.py are already defined
# from llm_client import HelloAgentsLLM
# from memory import Memory

class ReflectionAgent:
    def __init__(self, llm_client, max_iterations=3):
        self.llm_client = llm_client
        self.memory = Memory()
        self.max_iterations = max_iterations

    def run(self, task: str):
        print(f"\n--- Starting to Process Task ---\nTask: {task}")

        # --- 1. Initial Execution ---
        print("\n--- Performing Initial Attempt ---")
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_code = self._get_llm_response(initial_prompt)
        self.memory.add_record("execution", initial_code)

        # --- 2. Iterative Loop: Reflection and Refinement ---
        for i in range(self.max_iterations):
            print(f"\n--- Iteration {i+1}/{self.max_iterations} ---")

            # a. Reflection
            print("\n-> Performing Reflection...")
            last_code = self.memory.get_last_execution()
            reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)
            feedback = self._get_llm_response(reflect_prompt)
            self.memory.add_record("reflection", feedback)

            # b. Check if stopping is needed
            if "no improvement needed" in feedback.lower():
                print("\n✅ Reflection considers code needs no improvement, task completed.")
                break

            # c. Refinement
            print("\n-> Performing Refinement...")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(
                task=task,
                last_code_attempt=last_code,
                feedback=feedback
            )
            refined_code = self._get_llm_response(refine_prompt)
            self.memory.add_record("execution", refined_code)

        final_code = self.memory.get_last_execution()
        print(f"\n--- Task Completed ---\nFinal Generated Code:\n```python\n{final_code}\n```")
        return final_code

    def _get_llm_response(self, prompt: str) -> str:
        """A helper method for calling LLM and getting complete streaming response."""
        messages = [{"role": "user", "content": prompt}]
        response_text = self.llm_client.think(messages=messages) or ""
        return response_text

```

### 4.4.4 Запуск экземпляра и анализ

Полный код также можно найти в`code`папка репозитория сопроводительного кода этой книги; здесь мы предоставляем экземпляр вывода.

````python
--- Starting to Process Task ---
Task: Write a Python function to find all prime numbers between 1 and n.

--- Performing Initial Attempt ---
🧠 Calling xxxxxx model...
✅ Large language model response successful:
```питон
защита find_primes(n):
    ...
    возвращать простые числа
```
📝 Memory updated, added an 'execution' record.

--- Iteration 1/2 ---

-> Performing Reflection...
🧠 Calling xxxxxx model...
✅ Large language model response successful:
The current code has a time complexity of O(n * sqrt(n)). While this implementation is acceptable for smaller n values, performance will significantly degrade when n is very large. The main bottleneck is that each number needs trial division checking, leading to high time overhead.

It is recommended to use the Sieve of Eratosthenes algorithm, which has a time complexity of O(n log(log n)) and can significantly improve the efficiency of finding prime numbers.

Improved code as follows:
```питон
защита find_primes(n):
    ...
    возвращать простые числа
```
📝 Memory updated, added a 'reflection' record.

-> Performing Refinement...
🧠 Calling xxxxxx model...
✅ Large language model response successful:
```питон
защита find_primes(n):
    ...
    возвращать простые числа
```
📝 Memory updated, added an 'execution' record.

--- Iteration 2/2 ---

-> Performing Reflection...
🧠 Calling xxxxxx model...
✅ Large language model response successful:
The current code uses the Sieve of Eratosthenes with time complexity O(n log log n) and space complexity O(n). This algorithm is already very efficient for finding all prime numbers between 1 and n, and usually requires no further optimization. However, in some specific scenarios, the following improvements can be considered:

1. <strong>Segmented Sieve</strong>: Suitable for cases where n is very large but memory is limited. Divide the interval into multiple small segments, process each segment separately with the sieve method, reducing memory usage.
2. <strong>Odd Number Sieve</strong>: Except for 2, all prime numbers are odd. When initializing the `is_prime` array, only mark odd numbers, which can reduce space complexity by half while reducing some unnecessary calculations.

However, these improvements are not necessary for most application scenarios because the standard Sieve of Eratosthenes is already efficient enough. Therefore, in general cases, <strong>no improvement needed</strong>.
📝 Memory updated, added a 'reflection' record.

✅ Reflection considers code needs no improvement, task completed.

--- Task Completed ---
Final Generated Code:
```питон
защита find_primes(n):
    """
    Находит все простые числа от 1 до n, используя алгоритм «Решето Эратосфена».

:param n: Верхний предел диапазона поиска простых чисел.
    :return: Список всех простых чисел от 1 до n.
    """
    если n < 2:
        вернуть []

is_prime = [Истина] * (n + 1)
    is_prime[0] = is_prime[1] = ложь

р = 2
    в то время как p * p <= n:
        если is_prime[p]:
            для i в диапазоне (p * p, n + 1, p):
                is_prime[i] = Ложь
        р += 1

простые числа = [число для числа в диапазоне (2, n + 1), если is_prime[num]]
    возвращать простые числа
```
````

Этот запущенный экземпляр демонстрирует, как механизм отражения заставляет агента выполнять глубокую оптимизацию:

1. **Эффективная «критика» является предпосылкой для оптимизации**: в первом раунде размышлений, поскольку мы использовали «чрезвычайно строгую» и «ориентированную на эффективность алгоритма» подсказку, агент не был удовлетворен функционально правильным исходным кодом, но точно указал на узкое место временной сложности «O(n * sqrt(n))» и предложил предложения по улучшению на уровне алгоритма — решето Эратосфена.
2. **Итеративное улучшение**: получив четкую обратную связь, агент успешно реализовал более эффективный метод сита на этапе уточнения, уменьшив сложность алгоритма до «O(n log log n)», завершив первую значимую самоитерацию.
3. **Конвергенция и прекращение**: во втором раунде размышлений, столкнувшись с уже эффективным методом сита, агент продемонстрировал более глубокие знания. Он не только подтвердил эффективность текущего алгоритма, но даже упомянул более продвинутые направления оптимизации, такие как сегментированное сито, но в конечном итоге сделал правильное заключение: «в общих случаях улучшения не требуются». Это решение вызвало наше условие завершения, позволив процессу оптимизации сойтись.

Этот случай полностью доказывает, что ценность хорошо спроектированного механизма отражения заключается не только в исправлении ошибок, но, что более важно, в **разработке решений для поэтапного улучшения качества и эффективности**, что делает его одной из ключевых технологий для создания сложных, высококачественных агентов.

### 4.4.5 Анализ затрат и выгод механизма отражения

Хотя механизм Reflection отлично работает для повышения качества решения задач, эта возможность не обходится без затрат. В практических приложениях нам необходимо сопоставить выгоды, которые это приносит, с соответствующими затратами.

(1) Основные затраты

1. **Увеличенные накладные расходы на вызов модели**: это самые прямые затраты. Каждая итерация требует как минимум двух дополнительных вызовов большой языковой модели (один для отражения, другой для уточнения). При повторении нескольких раундов затраты на вызовы API и потребление вычислительных ресурсов возрастут в геометрической прогрессии.

2. **Значительно увеличенная задержка выполнения задач**. Отражение — это последовательный процесс; каждый раунд уточнения должен ждать завершения отражения предыдущего раунда. Это значительно увеличивает общее время выполнения задачи, что делает ее непригодной для сценариев с высокими требованиями к реальному времени.

3. **Повышенная сложность разработки подсказок**. Как показывает наш случай, успех Reflection во многом зависит от качественных и целенаправленных подсказок. Проектирование и отладка эффективных подсказок для различных этапов, таких как «выполнение», «обдумывание» и «уточнение», требует больше усилий при разработке.

(2) Основные преимущества

1. **Скачок в качестве решения**. Самым большим преимуществом является возможность итеративной оптимизации «качественного» начального решения до «отличного» конечного решения. Это улучшение от функциональной корректности к эффективности производительности, от грубой логики к строгой логике имеет решающее значение во многих критически важных задачах.

2. **Повышенная устойчивость и надежность**. Благодаря внутренним циклам самокоррекции агент может обнаруживать и исправлять потенциальные логические ошибки, фактические ошибки или неправильную обработку граничных случаев в первоначальном решении, что значительно повышает надежность конечного результата.

Подводя итог, можно сказать, что механизм отражения представляет собой типичную стратегию «цена за качество». Он очень подходит для сценариев, в которых **чрезвычайно высокие требования к качеству, точности и надежности конечных результатов и относительно мягкие требования к производительности выполнения задач в реальном времени**. Например:

- Создание критического бизнес-кода или технических отчетов.
- Проведение сложных логических рассуждений в научных исследованиях.
- Системы поддержки принятия решений, требующие глубокого анализа и планирования.

И наоборот, если сценарий приложения требует быстрых ответов или «приблизительно правильного» ответа уже достаточно, использование более легких парадигм ReAct или Plan-and-Solve может быть более экономичным выбором.

## 4.5 Краткое содержание главы

В этой главе, опираясь на обширные знания языковых моделей, полученные в главе 3, мы закодировали и реализовали с нуля три классические парадигмы построения отраслевых агентов, «создавая колеса самостоятельно»: ReAct, Plan-and-Solve и Reflection. Мы не только изучили их основные принципы работы, но и глубоко поняли их соответствующие преимущества, ограничения и применимые сценарии на конкретных практических примерах.

**Обзор основных знаний:**

1. ReAct: Мы создали агент ReAct, который может взаимодействовать с внешним миром. Посредством динамического цикла «мысль-действие-наблюдение» компания успешно использовала поисковые системы для ответа на вопросы в режиме реального времени, которые не могла охватить ее собственная база знаний. Его основные преимущества заключаются в **адаптивности к окружающей среде** и **возможности динамического исправления ошибок**, что делает его лучшим выбором для решения исследовательских задач, требующих ввода внешних инструментов.
2. «Планируй и решай». Мы реализовали агент «Планируй и решай», который сначала планирует, а затем выполняет, и использовали его для решения математических словесных задач, требующих многоэтапного рассуждения. Он разбивает сложные задачи на четкие шаги, а затем выполняет их один за другим. Его основные преимущества заключаются в **структуре** и **стабильности**, что особенно удобно для решения задач с определенными логическими путями и интенсивным внутренним рассуждением.
3. Отражение (саморефлексия и итерация). Мы создали агент отражения с возможностями самооптимизации. Введя итеративный цикл «выполнить-отразить-уточнить», он успешно оптимизировал изначально неэффективное кодовое решение до алгоритмически превосходной высокопроизводительной версии. Его основная ценность заключается в **значительном улучшении качества решений**, подходящих для сценариев с чрезвычайно высокими требованиями к точности и надежности результатов.

Три парадигмы, рассмотренные в этой главе, представляют собой три разные стратегии решения проблем агентами, как показано в таблице 4.1. В практических приложениях выбор зависит от основных требований задачи:

<div align="center">
<p>Таблица 4.1. Стратегия выбора для различных агентских циклов</p>
<img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/4-figures/4-4.png" alt="" width="70%"/>
</div>

На данный момент мы освоили основные технологии создания отдельных агентов. Чтобы передать знания и получить более глубокое понимание практических приложений, в следующем разделе мы рассмотрим, как использовать различные платформы с низким кодированием и решения с облегченным кодом для создания агентов.

## Упражнения

> **Примечание**. Некоторые упражнения не имеют стандартных ответов; основное внимание уделяется развитию у учащихся всестороннего понимания и практических способностей в разработке парадигм агентов.

1. В этой главе были представлены три классические парадигмы агентов: «ReAct», «Plan-and-Solve» и «Reflection». Пожалуйста, проанализируйте:

   - Каковы существенные различия в том, как эти три парадигмы организуют «мышление» и «действие»?
   - Если бы вам пришлось разработать «помощника по управлению умным домом» (который должен управлять освещением, кондиционером, шторами и другими устройствами и автоматически настраиваться в зависимости от привычек пользователя), какую парадигму вы бы выбрали в качестве базовой архитектуры? Почему?
   - Можно ли объединить эти три парадигмы? Если да, попробуйте спроектировать архитектуру агента гибридной парадигмы и объяснить применимые сценарии ее применения.

2. В реализации ReAct в разделе 4.2 мы использовали регулярные выражения для анализа выходных данных большой языковой модели (таких как «Мысль» и «Действие»). Пожалуйста, учтите:

   - Какие потенциальные уязвимости существуют в текущем методе синтаксического анализа? При каких обстоятельствах это может потерпеть неудачу?
   - Помимо регулярных выражений, какие есть более надежные решения для анализа вывода?
   - Попробуйте изменить код в этой главе, чтобы использовать более надежный формат вывода, и сравните плюсы и минусы двух подходов.

3. Вызов инструмента — одна из основных возможностей современных агентов. На основе конструкции ToolExecutor, описанной в разделе 4.2.2, выполните следующее расширение:

> **Примечание**. Это практический вопрос; рекомендуется писать код.

   - Добавьте к агенту ReAct инструмент «калькулятор», чтобы он мог решать сложные математические задачи (например, «Вычислить результат `(123 + 456) × 789/12 = ?`»).
   - Разработайте и внедрите механизм обработки «ошибки выбора инструмента»: когда агент неоднократно вызывает неправильный инструмент или предоставляет неверные параметры, как система должна направить его на исправление?
   - Подумайте: если количество вызываемых инструментов увеличится до 50 или даже 100, будет ли текущий метод описания инструментов по-прежнему работать эффективно? С инженерной точки зрения, как мы можем оптимизировать организацию и механизм поиска инструментов, когда количество вызываемых инструментов значительно увеличивается вместе с потребностями бизнеса?

4. Парадигма «Планируй и решай» разбивает задачи на два этапа: «планирование» и «исполнение». Пожалуйста, проанализируйте внимательно:

   - В реализации, описанной в разделе 4.3, план, созданный на этапе планирования, является «статическим» (создается один раз и не подлежит изменению). Если в ходе выполнения обнаруживается, что определенный шаг не может быть выполнен или результат не соответствует ожиданиям, как следует спроектировать механизм «динамического перепланирования»?
   - Сравните «Планируй и решай» с «ReAct»: при решении такой задачи, как «бронирование деловой поездки из Пекина в Шанхай (включая авиабилеты, отели, аренду автомобиля)», какая парадигма больше подходит? Почему?
   - Попробуйте разработать систему «иерархического планирования»: сначала создайте абстрактный план высокого уровня, затем создайте подробные подпланы для каждого шага высокого уровня. Какие преимущества имеет данная конструкция?

5. Механизм Reflection улучшает качество вывода за счет цикла «выполнить-отразить-уточнить». Пожалуйста, учтите:

   - В случае генерации кода в разделе 4.4 одна и та же модель используется на разных этапах. Если используются две разные модели (например, более мощная модель для отражения и более быстрая модель для выполнения), какое влияние это окажет?
   - Условием завершения работы механизма Reflection является «отзыв содержит **улучшение не требуется**» или «достигнуто максимальное количество итераций». Разумна ли такая конструкция? Можно ли разработать более разумное условие завершения?
   - Предположим, вы хотите создать «помощника по написанию академических статей», который может создавать черновики и постоянно оптимизировать содержание статьи. Пожалуйста, разработайте многомерный механизм отражения, который отражает и улучшается с разных точек зрения, таких как логика абзацев, инновации методов, языковое выражение и стандарты цитирования.

6. Оперативная разработка — ключевая технология, влияющая на конечный эффект агентов. В этой главе было продемонстрировано несколько тщательно разработанных шаблонов подсказок. Пожалуйста, проанализируйте:

   - Сравните подсказку «ReAct» в разделе 4.2.3 и подсказку «Планируй и решай» в разделе 4.3.2; они, очевидно, имеют существенные различия в конструктивном исполнении. Как эти различия служат основной логике соответствующих парадигм?
   - В подсказке `Reflection` в разделе 4.4.3 мы использовали такой параметр роли, как «вы чрезвычайно строгий эксперт по проверке кода». Попробуйте изменить этот параметр роли (например, изменив его на «вы являетесь специалистом по сопровождению проекта с открытым исходным кодом, который ценит читаемость кода»), наблюдайте за изменениями в выходных результатах и ​​суммируйте влияние параметров роли на поведение агента.
   - Добавление к подсказкам «несколько примеров» часто может значительно улучшить способность модели следовать определенным форматам. Пожалуйста, попробуйте добавить примеры «несколько раз» к одному из агентов в этой главе и сравните эффекты.

7. Стартап в сфере электронной коммерции теперь надеется использовать «агента по обслуживанию клиентов», который заменит человеческое обслуживание клиентов для снижения затрат и повышения эффективности. Он должен иметь следующие функции:

а. Узнайте причину запроса пользователя на возврат средств.

б. Запросить информацию о заказе пользователя и статус логистики.

в. Разумно определить, следует ли утверждать возврат средств, исходя из политики компании.

д. Создайте правильное ответное письмо и отправьте его на электронную почту пользователя.

е. Если решение является несколько спорным (уверенность в себе ниже порогового значения), будьте в состоянии поразмышлять над собой и дать более разумные предложения.

Как менеджер по продукту этого продукта:
   - Какую парадигму (или комбинацию парадигм) из этой главы вы бы выбрали в качестве базовой архитектуры системы?
   - Какие инструменты нужны этой системе? Пожалуйста, перечислите как минимум 3 инструмента и их функциональные описания.
   - Как составить подсказки, чтобы решения агента не только соответствовали интересам компании, но и сохраняли дружелюбное отношение к пользователям?
   - С какими рисками и проблемами может столкнуться этот продукт после запуска? Как можно снизить эти риски с помощью технических средств?

## Ссылки

[1] Яо С., Чжао Дж., Ю Д. и др. React: Синергия рассуждений и действий в языковых моделях[C] // Международная конференция по обучающим представлениям (ICLR). 2023.

[2] Ван Л., Сюй В., Лан Ю. и др. Подсказки «планируй и решай»: улучшение нулевой цепочки мыслей с помощью больших языковых моделей[J]. Препринт arXiv arXiv:2305.04091, 2023.

[3] Шинн Н., Кассано Ф., Гопинатх А. и др. Рефлексия: языковые агенты с обучением вербальному подкреплению [J]. Достижения в области нейронных систем обработки информации, 2023, 36: 8634-8652.

