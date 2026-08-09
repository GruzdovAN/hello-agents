# Глава 12. Оценка производительности агентов

В предыдущих главах мы создали основные функциональные возможности платформы HelloAgents, реализовав различные парадигмы агентов, системы инструментов, механизмы памяти и обучение с подкреплением. При построении агентских систем нам также необходимо решить основную проблему: **Как объективно оценить эффективность агентов?** В частности, нам необходимо ответить на следующие вопросы:

1. Обладает ли агент ожидаемыми возможностями?
2. Как он справляется с разными задачами?
3. На каком уровне он находится по сравнению с другими агентами?

В этой главе в HelloAgents будет добавлена ​​**Система оценки эффективности**. Мы глубоко поймем теоретическую основу оценки агентов и внедрим инструменты оценки.

## 12.1 Основы оценки агентов

### 12.1.1 Зачем нужна оценка агента

Теперь у нас есть SimpleAgent, который уже обладает мощными возможностями рассуждения и вызова инструментов. Давайте рассмотрим типичный сценарий использования:

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import SearchTool

# Create LLM and agent
llm = HelloAgentsLLM()

# Create a system prompt emphasizing tool use
system_prompt = """You are an AI assistant that can use search tools to obtain the latest information.

When you need to search for information, please use the following format:
[TOOL_CALL:search:search keywords]

For example:
- [TOOL_CALL:search:latest AI news]
- [TOOL_CALL:search:Python programming tutorial]

Please use the search tool to obtain the latest information before answering questions."""

agent = SimpleAgent(name="AI Assistant", llm=llm, system_prompt=system_prompt)

# Add search tool
agent.add_tool(SearchTool())

# Example: Use search tool to answer questions
response = agent.run("What are the latest AI technology development trends?")
print(f"\nAnswer: {response}")
```

Этот агент может работать нормально, но мы сталкиваемся с основной проблемой: как объективно оценить его работу? Когда мы оптимизируем подсказки или меняем модели LLM, как мы узнаем, есть ли реальные улучшения? Как обеспечить надежность агента перед развертыванием в производственной среде? Все эти вопросы необходимо решать посредством систематической оценки.

Основная ценность оценки агентов заключается в предоставлении стандартизированных методов измерения возможностей агентов. Посредством оценки мы можем количественно оценить производительность агента с помощью конкретных числовых показателей, объективно сравнить преимущества различных проектных решений, быстро обнаружить слабые места агента в конкретных сценариях и доказать пользователям надежность агента.

В отличие от традиционного тестирования программного обеспечения, оценка агентов сталкивается с уникальными проблемами. Во-первых, это неопределенность результатов: на один и тот же вопрос может быть несколько правильных ответов, что затрудняет простое определение правильного или неправильного ответа. Во-вторых, разнообразие критериев оценки: разные задачи требуют разных методов оценки; вызов инструмента должен проверять сигнатуры функций, а задачи вопросов и ответов должны оценивать семантическое сходство. Наконец, высокая стоимость оценки: каждая оценка требует многочисленных вызовов API, что потенциально может стоить сотни юаней и более.

Для решения этих проблем научные круги и промышленность предложили несколько стандартизированных **контрольных показателей**. Эти тесты предоставляют унифицированные наборы данных, метрики оценки и методы оценки, что позволяет нам оценивать и сравнивать различные агентные системы по одним и тем же стандартам.

### 12.1.2 Обзор основных критериев оценки

В области оценки агентов появилось множество влиятельных эталонных тестов. Ниже приведены некоторые основные критерии и показатели оценки:

**(1) Оценка возможности вызова инструмента**

Вызов инструмента — одна из основных возможностей агентов. Агентам необходимо понимать намерения пользователя, выбирать подходящие инструменты и правильно создавать вызовы функций. Соответствующие критерии оценки включают в себя:

- **BFCL (таблица лидеров вызовов функций Беркли)**<sup>[1]</sup>: запущен Калифорнийским университетом в Беркли и включает более 1120 тестовых образцов, охватывающих четыре категории: простые, множественные, параллельные, нерелевантные, использует алгоритм сопоставления AST для оценки, умеренный размер набора данных, активное сообщество.
- **ToolBench**<sup>[2]</sup>: запущен Университетом Цинхуа и включает более 16 000 реальных сценариев вызовов API, охватывающих сложные сценарии использования инструментов в реальном мире.
- **API-Bank**<sup>[3]</sup>: запущен компанией Microsoft Research и включает 53 часто используемых инструмента API. Основное внимание уделяется оценке понимания агентами и использованию документации API.

**(2) Общая оценка возможностей**

Оценивает комплексную производительность агента в реальных задачах, включая многоэтапное рассуждение, применение знаний, мультимодальное понимание и т. д.:

- **GAIA (Общие помощники по искусственному интеллекту)**<sup>[4]</sup>: запущено совместно Meta AI и Hugging Face, включает 466 реальных задач, разделенных на уровни сложности 1/2/3, оценивает многоэтапное рассуждение, использование инструментов, обработку файлов, возможности просмотра веб-страниц, использует алгоритм Quasi Exact Match, задачи реалистичны и полны.
- **AgentBench**<sup>[5]</sup>: запущен Университетом Цинхуа, включает 8 задач в различных областях и всесторонне оценивает общие возможности агента.
- **WebArena**<sup>[6]</sup>: запускается CMU и оценивает выполнение задач агента и возможности веб-взаимодействия в реальных веб-средах.

**(3) Оценка многоагентного сотрудничества**

Оценивает способность нескольких агентов работать совместно:

- **ChatEval**<sup>[7]</sup>: оценивает качество многоагентных диалоговых систем.
- **SOTOPIA**<sup>[8]</sup>: оценивает возможности взаимодействия агентов в социальных сценариях.
- **Пользовательские сценарии сотрудничества**: задачи оценки, разработанные в соответствии с конкретными сценариями применения.

**(4) Общие показатели оценки**

В разных тестах используются разные метрики оценки, общие из них включают в себя:

- **Показатели точности**: точность, точное совпадение, оценка F1, используемые для измерения правильности ответов.
- **Показатели эффективности**: время ответа, использование токена, используемые для измерения эффективности выполнения.
- **Метрики надежности**: частота ошибок, восстановление после сбоев, используемые для измерения отказоустойчивости.
- **Показатели сотрудничества**: эффективность общения, выполнение задач, используемые для измерения эффективности сотрудничества.

### 12.1.3 Проектирование системы оценки HelloAgents

Учитывая кривую обучения и практичность, в этой главе основное внимание будет уделено следующим сценариям оценки:

1. **BFCL**: оценка возможности вызова инструмента.
   - Обоснование выбора: умеренный размер набора данных, четкие показатели оценки, активное сообщество.
   - Применимые сценарии: оценка точности вызова функций агента.

2. **GAIA**: оценка общих возможностей ИИ-помощника.
   - Обоснование выбора: реалистичные задачи, градация сложности, высокая полнота.
   - Применимые сценарии: оценка возможностей агента по комплексному решению проблем.

3. **Оценка качества генерации данных**: оценка качества данных, генерируемых LLM.
   - Обоснование выбора: В этом случае вы получите полную демонстрацию использования агента для создания и оценки данных.
   - Применимые сценарии: оценка качества сгенерированных данных обучения и тестовых данных.
   - Методы оценки: судья LLM, процент побед, ручная проверка.

Используя эти три сценария оценки, мы создадим полную систему оценки. На рис. 12.1 показан наш подход к построению системы оценки.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-1.png" alt="" width="85%"/>
  <p>Рисунок 12.1 Архитектура системы оценки HelloAgents</p>
</div>



### 12.1.4 Цели изучения главы и краткий опыт

Давайте сначала посмотрим на учебное содержание главы 12:

```
hello_agents/
├── evaluation/                         # Evaluation module
│   └── benchmarks/                     # Evaluation benchmark implementation
│       ├── bfcl/                       # BFCL evaluation implementation
│       │   ├── dataset.py              # BFCL dataset loader
│       │   ├── evaluator.py            # BFCL evaluator (AST matching)
│       │   ├── metrics.py              # BFCL-specific metrics
│       │   └── ast_matcher.py          # AST matching algorithm
│       ├── gaia/                       # GAIA evaluation implementation
│       │   ├── dataset.py              # GAIA dataset loader
│       │   ├── evaluator.py            # GAIA evaluator (quasi exact match)
│       │   ├── metrics.py              # GAIA-specific metrics
│       │   └── quasi_exact_match.py    # Quasi exact match algorithm
│       └── data_generation/            # Data generation evaluation implementation
│           ├── dataset.py              # AIME dataset loader
│           ├── llm_judge.py            # LLM Judge evaluator
│           └── win_rate.py             # Win Rate evaluator
└── tools/builtin/                      # Built-in tools module
    ├── bfcl_evaluation_tool.py         # BFCL evaluation tool
    ├── gaia_evaluation_tool.py         # GAIA evaluation tool
    ├── llm_judge_tool.py               # LLM Judge tool
    └── win_rate_tool.py                # Win Rate tool
```

В рамках содержания этой главы целью обучения является овладение умением применять инструменты оценки. Сначала подготовим среду разработки:

```bash
# Install HelloAgents framework (Chapter 12 version)
pip install "hello-agents[evaluation]==0.2.7"

# Set environment variables
export HF_TOKEN="your_huggingface_token"     # For GAIA dataset (setup steps will follow)

# Since the official `bfcl-eval` package requires numpy<=2.0.0, which conflicts with HelloAgents main dependencies, separate installation is needed
pip install "numpy==1.26.4" bfcl-eval
```

В следующих разделах мы подробно изучим подробное использование и представление каждого метода оценки.

## 12.2 BFCL: оценка возможностей вызова инструмента

### 12.2.1 Введение в тест BFCL

BFCL (Berkeley Function Calling Leaderboard) – это тест оценки возможностей вызова функций, запущенный Калифорнийским университетом в Беркли<sup>[1]</sup>. В агентских системах вызов инструментов является одной из основных возможностей. Агентам необходимо выполнить следующие задачи:

1. **Понимание требований задачи**: извлечение ключевой информации из описания пользователя на естественном языке.
2. **Выберите подходящие инструменты**: выберите наиболее подходящий инструмент из доступного набора инструментов.
3. **Построение вызовов функций**: правильно заполните имя функции и параметры.
4. **Обработка сложных сценариев**: поддержка расширенных сценариев, таких как многофункциональные вызовы и параллельные вызовы.

Тест BFCL содержит четыре категории оценки с возрастающей сложностью. Начиная с самого простого вызова одной функции (Простой), постепенно переходя к сценариям, требующим нескольких вызовов функций (Несколько), затем к сложным сценариям, требующим параллельных вызовов нескольких функций (Параллельный), и, наконец, к сценариям, требующим оценки необходимости вызова функций (Нерелевантность). Эти четыре категории охватывают различные сценарии вызова инструментов, с которыми агенты могут столкнуться в практических приложениях, как показано в Таблице 12.1:

<div align="center">
  <p>Таблица 12.1. Четыре категории оценки в тесте BFCL</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-table-1.png" alt="" width="85%"/>
</div>

Процесс оценки BFCL следует стандартным процедурам эталонного тестирования: сначала загружается набор данных и выбирается категория оценки, затем запускается агент для получения результатов прогнозирования, затем анализируются результаты прогнозирования в абстрактном синтаксическом дереве (AST) и, наконец, судится о правильности прогнозов с помощью алгоритма сопоставления AST. Весь процесс охватывает все тестовые образцы, в конечном итоге рассчитывая показатели оценки, такие как точность, и создавая отчеты об оценке. Полный процесс оценки показан на рисунке 12.2:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-2.png" alt="" width="85%"/>
  <p>Рисунок 12.2 Схема процесса оценки BFCL</p>
</div>

**(1) Структура набора данных BFCL**

Набор данных BFCL использует формат JSON, при этом каждый тестовый образец содержит следующие поля:

```json
{
  "id": "simple_001",
  "question": "What's the weather like in Beijing today?",
  "function": [
    {
      "name": "get_weather",
      "description": "Get the current weather for a location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city name"
          }
        },
        "required": ["location"]
      }
    }
  ],
  "ground_truth": [
    {
      "name": "get_weather",
      "arguments": {
        "location": "Beijing"
      }
    }
  ]
}
```

**Описание ключевых полей:**

- `вопрос`: запрос пользователя на естественном языке.
- `function`: список доступных функций (включая сигнатуры и описания функций).
- `ground_truth`: стандартный ответ (ожидаемый вызов функции)

**(2) Объяснение соответствия AST**

BFCL использует **Сопоставление AST (Сопоставление абстрактного синтаксического дерева)** в качестве основного алгоритма оценки, поэтому давайте разберемся в стратегии оценки, представленной ниже.

BFCL использует абстрактное синтаксическое дерево (AST) для интеллектуального сопоставления, а не простого сопоставления строк. Основная идея сопоставления AST заключается в следующем: **Разобрать вызовы функций в синтаксические деревья, затем сравнить древовидную структуру и значения узлов**.

Учитывая прогнозируемый вызов функции $P$ и стандартный ответ $G$, функция сопоставления AST определяется как:

$$
\text{AST\_Match}(P, G) = \begin{cases}
1 & \text{if } \text{AST}(P) \equiv \text{AST}(G) \\
0 и \text{иначе}
\end{случаи}
$$

Где $\text{AST}(x)$ представляет вызов функции синтаксического анализа в абстрактное синтаксическое дерево, $\equiv$ представляет эквивалентность синтаксического дерева.

Два синтаксических дерева эквивалентны, если они удовлетворяют трем основным условиям: имена функций должны быть полностью идентичны (точное совпадение), наборы пар ключ-значение параметров равны (игнорируя порядок), и каждое значение параметра семантически эквивалентно (например,`2+3`эквивалентно`5`). В конкретном процессе сопоставления сопоставление имен функций требует точного сопоставления строк, например`get_weather`и`get_temperature`считаются разными функциями. Сопоставление параметров использует AST для интеллектуального сравнения, что позволяет использовать разные порядки параметров (`f(a=1, b=2)`эквивалентно`f(b=2, a=1)`), допуская эквивалентные выражения (`f(x=2+3)`эквивалентно`f(x=5)`), а также позволяет использовать различные строковые представления (`f(s="hello")`эквивалентно`f(s='hello')`). Для сценариев многофункционального вызова алгоритм сопоставления требует вызова одинакового количества функций, каждый вызов функции должен совпадать, но порядок вызовов может отличаться (с использованием сопоставления наборов).

**Примеры сопоставления AST:**

```python
# Example 1: Different parameter order (match successful)
Prediction: get_weather(city="Beijing", unit="celsius")
Standard: get_weather(unit="celsius", city="Beijing")
Result: ✅ Match successful

# Example 2: Equivalent expression (match successful)
Prediction: calculate(x=2+3)
Standard: calculate(x=5)
Result: ✅ Match successful

# Example 3: Wrong function name (match failed)
Prediction: get_temperature(city="Beijing")
Standard: get_weather(city="Beijing")
Result: ❌ Match failed

# Example 4: Wrong parameter value (match failed)
Prediction: get_weather(city="Shanghai")
Standard: get_weather(city="Beijing")
Result: ❌ Match failed
```

**(3) Показатели оценки BFCL**

BFCL использует следующие показатели для оценки производительности агента:

**1. Точность**

Точность — это самый основной показатель, определяемый как доля образцов с успешным сопоставлением AST:

$$
\text{Accuracy} = \frac{1}{N} \sum_{i=1}^{N} \text{AST\_Match}(P_i, G_i)
$$

Где:
- $N$ — общее количество выборок
- $P_i$ — результат предсказания $i$-й выборки
- $G_i$ — стандартный ответ $i$-го образца
- $\text{AST\_Match}(P_i, G_i) \in \{0, 1\}$ — функция сопоставления AST

**2. Коэффициент совпадения AST**

То же, что и точность, с упором на использование алгоритма сопоставления AST:

$$
\text{Коэффициент совпадения AST} = \text{Точность}
$$

**3. Точность по категориям**

Для каждой категории $c \in \{\text{simple}, \text{multiple}, \text{parallel}, \ldots\}$ рассчитайте точность для этой категории:

$$
\text{Accuracy}_c = \frac{1}{|D_c|} \sum_{i \in D_c} \text{AST\_Match}(P_i, G_i)
$$

Где $D_c$ — набор выборок категории $c$, $|D_c|$ — количество выборок в этой категории.

**4. Взвешенная точность**

Учитывая веса сложности разных категорий:

$$
\text{Взвешенная точность} = \sum_{c} w_c \cdot \text{Точность}_c
$$

Где $w_c$ — вес категории $c$, удовлетворяющий условию $\sum_c w_c = 1$.

**5. Частота ошибок**

Доля образцов, в которых не удалось правильно вызвать функции:

$$
\text{Коэффициент ошибок} = 1 - \text{Точность} = \frac{1}{N} \sum_{i=1}^{N} (1 - \text{AST\_Match}(P_i, G_i))
$$

**Метрическая интерпретация:**

- **Точность = 1,0**: все образцы полностью верны.
- **Точность = 0,8**: 80 % образцов верны, 20 % образцов неверны.
- **Точность = 0,0**: все образцы неверны.

**Пример точности категории:**

```python
# Assume evaluation results
simple_accuracy = 0.95      # Simple category: 95% correct
multiple_accuracy = 0.82    # Multiple category: 82% correct
parallel_accuracy = 0.68    # Parallel category: 68% correct

# Weighted accuracy (assuming equal weights)
weighted_accuracy = (0.95 + 0.82 + 0.68) / 3 = 0.817
```

**(4) Официальный инструмент оценки BFCL**

BFCL предоставляет официальный инструмент CLI для оценки:

```bash
# Install BFCL evaluation tool
pip install bfcl

# Run official evaluation
bfcl evaluate \
    --model-result-path ./results.json \
    --test-category simple_python
```

Преимущества использования официального инструмента оценки: он использует официальный алгоритм сопоставления AST, результаты оценки полностью соответствуют таблице лидеров, поддерживают все категории BFCL v4 и могут автоматически генерировать подробные отчеты об оценке.


### 12.2.2 Получение набора данных BFCL

Набор данных BFCL можно получить следующими методами:

**Метод 1: клонирование из официального репозитория GitHub (рекомендуется)**

Это наиболее надежный метод, позволяющий получить полный набор данных и достоверную информацию:

```bash
# Clone BFCL repository
git clone https://github.com/ShishirPatil/gorilla.git temp_gorilla
cd temp_gorilla/berkeley-function-call-leaderboard

# View BFCL v4 dataset
ls bfcl_eval/data/
# Output: BFCL_v4_simple_python.json  BFCL_v4_multiple.json  BFCL_v4_parallel.json  ...

# View ground truth
ls bfcl_eval/data/possible_answer/
# Output: BFCL_v4_simple_python.json  BFCL_v4_multiple.json  ...
```

Причины, по которым рекомендуется этот метод: он содержит полную информацию (стандартные ответы), формат данных полностью соответствует официальному инструменту оценки, может напрямую использовать официальные сценарии оценки и поддерживает последнюю версию BFCL v4.

**Метод 2: загрузка официальных данных с помощью HelloAgents**

После клонирования репозитория загрузите данные с помощью HelloAgents:

```python
from hello_agents.evaluation import BFCLDataset

# Load BFCL official data
dataset = BFCLDataset(
    bfcl_data_dir="./temp_gorilla/berkeley-function-call-leaderboard/bfcl_eval/data",
    category="simple_python"  # BFCL v4 category
)

# Load data (including test data and ground truth)
data = dataset.load()

print(f"✅ Loaded {len(data)} test samples")
print(f"✅ Loaded {len(dataset.ground_truth)} ground truth")
# Output:
# ✅ Loaded 400 test samples
# ✅ Loaded 400 ground truth
```

Принцип работы этого загрузчика: сначала загрузите данные теста из`bfcl_eval/data/`, затем загрузите основную информацию из`bfcl_eval/data/possible_answer/`, затем автоматически объединяет тестовые данные и наземные данные и, наконец, сохраняет исходный формат данных BFCL. Категории наборов данных BFCL v4 можно просмотреть в таблице 12.2.

<div align="center">
  <p>Таблица 12.2 Четыре категории оценки в тесте BFCL</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-table-2.png" alt="" width="85%"/>
</div>

Вы также можете просмотреть доступные категории с помощью кода:

```python
# Get all supported categories
categories = dataset.get_available_categories()
print(f"Supported categories: {categories}")
# Output: ['simple_python', 'simple_java', 'simple_javascript', 'multiple', ...]
```

### 12.2.3 Реализация оценки BFCL в HelloAgents

Теперь давайте посмотрим, как реализовать оценку BFCL в среде HelloAgents. Мы предоставляем три способа использования:

**Метод 1: Использование BFCLEvaluationTool (рекомендуется)**

Это самый простой метод, завершающий оценку, создание отчета и официальную оценку с помощью одной строки кода:

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import BFCLEvaluationTool

# 1. Create agent to be evaluated
llm = HelloAgentsLLM()
agent = SimpleAgent(name="TestAgent", llm=llm)

# 2. Create BFCL evaluation tool
bfcl_tool = BFCLEvaluationTool()

# 3. Run evaluation (automatically complete all steps)
results = bfcl_tool.run(
    agent=agent,
    category="simple_python",  # Evaluation category
    max_samples=5              # Number of evaluation samples (0 means all)
)

# 4. View results
print(f"Accuracy: {results['overall_accuracy']:.2%}")
print(f"Correct: {results['correct_samples']}/{results['total_samples']}")
```

**Выполнить вывод:**

```
============================================================
BFCL One-Click Evaluation
============================================================

Configuration:
   Evaluation category: simple_python
   Sample count: 5
   Agent: TestAgent

============================================================
Step 1: Run HelloAgents Evaluation
============================================================
✅ BFCL dataset loaded
   Data directory: ./temp_gorilla/berkeley-function-call-leaderboard/bfcl_eval/data
   Category: simple_python
   Sample count: 400
   Ground truth count: 400

🔧 Starting BFCL evaluation...
   Progress: 1/5
   Progress: 5/5

✅ BFCL evaluation complete
   Overall accuracy: 100.00%
   simple_python: 100.00% (5/5)

📊 Evaluation results:
   Accuracy: 100.00%
   Correct: 5/5

============================================================
Step 2: Export BFCL Format Results
============================================================
✅ BFCL format results exported
   Output file: ./evaluation_results/bfcl_official/BFCL_v4_simple_python_result.json

============================================================
Step 3: Run BFCL Official Evaluation
============================================================
✅ Result file copied to: ./result/Qwen_Qwen3-8B/BFCL_v4_simple_python_result.json

🔄 Running command: bfcl evaluate --model Qwen/Qwen3-8B --test-category simple_python --partial-eval

============================================================
BFCL Official Evaluation Results
============================================================
📊 Evaluation results summary:
Model,Overall Acc,simple_python
Qwen/Qwen3-8B,100.00,100.00

🎯 Final results:
   Accuracy: 100.00%
   Correct: 5/5

============================================================
Step 4: Generate Evaluation Report
============================================================
📄 Report generated: ./evaluation_reports/bfcl_report_20251011_005938.md

Accuracy: 100.00%
Correct: 5/5
```

**Отчет об уценке, создаваемый автоматически:**

После завершения оценки автоматически создается подробный отчет Markdown, включающий:

```markdown
# BFCL Evaluation Report
**Generated**: 2025-10-11 00:59:38

## 📊 Evaluation Overview

- **Agent**: TestAgent
- **Evaluation Category**: simple_python
- **Overall Accuracy**: 100.00%
- **Correct Samples**: 5/5

## 📈 Detailed Metrics

### Category Accuracy

- **simple_python**: 100.00% (5/5)

## 📝 Sample Details

| Sample ID | Question | Prediction | Ground Truth | Correct |
|-----------|----------|------------|--------------|---------|
| simple_python_0 | Find the area of a triangle... | [{'name': 'calculate_triangle_area'...}] | [{'function_name': {'base': [10]...}}] | ✅ |
| simple_python_1 | Calculate the factorial of 5... | [{'name': 'calculate_factorial'...}] | [{'function_name': {'number': [5]}}] | ✅ |
...

## 📊 Accuracy Visualization
Accuracy: ██████████████████████████████████████████████████ 100.00%

## 💡 Recommendations
- ✅ Excellent performance! Agent shows outstanding tool calling capabilities.
```

**Метод 2: использование сценария оценки в один клик**

Подходит для быстрой оценки из командной строки. В сопроводительных примерах кода этой главы мы предоставляем`04_run_bfcl_evaluation.py`, поддерживающий прямую оценку из командной строки:

```bash
# Run evaluation script
python chapter12/04_run_bfcl_evaluation.py --category simple_python --samples 10

# Specify model name (for BFCL official evaluation)
python examples/04_run_bfcl_evaluation.py \
    --category simple_python \
    --samples 10 \
    --model-name "Qwen/Qwen3-8B"
```

Скрипт поддерживает три параметра:`--category`указывает категорию оценки (по умолчанию simple_python),`--samples`указывает количество оценочных образцов (по умолчанию 5, 0 означает все),`--model-name`указывает название модели для официальной оценки BFCL (по умолчанию Qwen/Qwen3-8B).

**Метод 3: непосредственное использование набора данных и средства оценки**

Подходит для сценариев, требующих индивидуального процесса оценки:

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.evaluation import BFCLDataset, BFCLEvaluator

# 1. Create agent
llm = HelloAgentsLLM()
agent = SimpleAgent(name="TestAgent", llm=llm)

# 2. Load dataset
dataset = BFCLDataset(
    bfcl_data_dir="./temp_gorilla/berkeley-function-call-leaderboard/bfcl_eval/data",
    category="simple_python"
)
data = dataset.load()

# 3. Create evaluator
evaluator = BFCLEvaluator(
    dataset=dataset,
    category="simple_python",
    evaluation_mode="ast"  # Use AST matching mode
)

# 4. Run evaluation
results = evaluator.evaluate(agent, max_samples=10)

# 5. View results
print(f"Accuracy: {results['overall_accuracy']:.2%}")
print(f"Correct: {results['correct_samples']}/{results['total_samples']}")

# 6. Export BFCL format results (optional)
evaluator.export_to_bfcl_format(
    results,
    output_path="./evaluation_results/my_results.json"
)
```

С помощью этих трех методов мы можем выбрать подходящие методы оценки, исходя из различных потребностей. Если вы просто хотите быстро оценить производительность агента, наиболее удобно использовать оценку одним щелчком мыши с помощью BFCLEvaluationTool; если вам нужна пакетная оценка или интеграция в конвейер CI/CD, лучше использовать сценарии командной строки; Если вам нужна глубокая настройка процесса оценки или интеграция в вашу собственную систему, непосредственное использование Dataset и Evaluator обеспечивает максимальную гибкость.




### 12.2.4 Интеграция официального инструмента оценки BFCL

Ранее мы узнали, как использовать встроенную функцию оценки HelloAgents. Фактически,`BFCLEvaluationTool`имеет **автоматически интегрированный официальный инструмент оценки BFCL**, позволяющий получать авторитетные и сопоставимые результаты оценки.

Весь процесс оценки состоит из четырех этапов: сначала загрузите тестовые данные из набора данных BFCL v4, затем используйте HelloAgents для запуска оценки и получения результатов прогнозирования агента, затем экспортируйте результаты в официальный формат BFCL (JSONL) и, наконец, используйте официальный сценарий оценки для расчета окончательных оценок. Этот процесс гарантирует, что результаты оценки полностью соответствуют таблице лидеров BFCL, как показано на рисунке 12.3:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-3.png" alt="" width="85%"/>
  <p>Рисунок 12.3. HelloAgents загружает процесс оценки BFCL</p>
</div>

При использовании`BFCLEvaluationTool`, официальная оценка **запускается автоматически** (включена по умолчанию):

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import BFCLEvaluationTool

# Create agent
llm = HelloAgentsLLM()
agent = SimpleAgent(name="TestAgent", llm=llm)

# Create evaluation tool
bfcl_tool = BFCLEvaluationTool()

# Run evaluation (automatically runs official evaluation)
results = bfcl_tool.run(
    agent=agent,
    category="simple_python",
    max_samples=5,
    # run_official_eval=True  # Default is True, can be omitted
    model_name="Qwen/Qwen3-8B"  # Optional, specify model name
)
```

Инструмент автоматически выполняет полный процесс оценки: сначала запустите оценку HelloAgents, чтобы получить результаты прогнозирования, затем экспортируйте результаты в формат BFCL и сохраните их в формате BFCL.`evaluation_results/bfcl_official/`каталог, следующий файл результатов копирования в`result/{model_name}/`каталог для удовлетворения требований официального инструмента оценки, затем запустите официальную команду оценки BFCL для расчета баллов и, наконец, отобразите официальные результаты оценки и сгенерируйте отчет об оценке в формате Markdown.

**Official Evaluation Output Example:**

```
============================================================
Step 3: Run BFCL Official Evaluation
============================================================

✅ Result file copied to:
   ./result/Qwen_Qwen3-8B/BFCL_v4_simple_python_result.json

🔄 Running command: bfcl evaluate --model Qwen/Qwen3-8B --test-category simple_python --partial-eval

============================================================
BFCL Official Evaluation Results
============================================================

📊 Evaluation results summary:
Model,Overall Acc,simple_python
Qwen/Qwen3-8B,100.00,100.00

🎯 Final results:
   Accuracy: 100.00%
   Correct: 5/5
```

Если вы хотите вручную контролировать процесс оценки, вы можете отключить автоматическую официальную оценку:

```python
# Disable official evaluation
results = bfcl_tool.run(
    agent=agent,
    category="simple_python",
    max_samples=5,
    run_official_eval=False  # Disable official evaluation
)

# Then manually run official evaluation
import subprocess
subprocess.run([
    "bfcl", "evaluate",
    "--model", "Qwen/Qwen3-8B",
    "--test-category", "simple_python",
    "--partial-eval"
])
```

Вы также можете создавать отчеты вручную:

```python
# Run evaluation
results = bfcl_tool.run(agent, category="simple_python", max_samples=5)

# Manually generate report
report = bfcl_tool.generate_report(
    results,
    output_file="./my_reports/custom_report.md"
)

# Print report content
print(report)
```



### 12.2.5 Детали реализации основного компонента

В предыдущих разделах мы узнали, как использовать инструменты оценки BFCL. Теперь давайте углубимся в то, как реализованы основные компоненты системы оценки HelloAgents. Понимание этих деталей реализации не только поможет вам лучше использовать систему оценки, но также позволит настраивать и расширять ее в соответствии с вашими потребностями.

**(1) BFCLDataset: загрузчик набора данных**

BFCLDataset отвечает за загрузку набора данных BFCL и управление им:

````python
class BFCLDataset:
    """BFCL dataset loader"""

    def __init__(self, category: str = "simple", local_data_path: Optional[str] = None):
        self.category = category
        self.local_data_path = local_data_path
        self.data = []

    def load(self) -> List[Dict[str, Any]]:
        """Load dataset"""
        # Load from local first
        if self.local_data_path:
            return self._load_from_local()
        # Otherwise load from Hugging Face
        return self._load_from_huggingface()
````

Поскольку набор данных BFCL находится в официальном репозитории, рекомендуемым подходом здесь является прямое клонирование локальной копии для оценки. Только если он не найден, он будет загружаться из Hugging Face.

**(2) BFCLEvaluator: Исполнитель оценки**

BFCLEvaluator отвечает за выполнение процесса оценки. Его ядром является`evaluate()`метод, который координирует весь процесс оценки:

````python
class BFCLEvaluator:
    """BFCL evaluator"""

    def evaluate(self, agent: Any, max_samples: Optional[int] = None) -> Dict[str, Any]:
        """Execute evaluation"""
        results = []

        for item in self.dataset[:max_samples]:
            # 1. Construct prompt
            prompt = self._build_prompt(item)

            # 2. Call agent
            response = agent.run(prompt)

            # 3. Extract function calls
            predicted_calls = self._extract_function_calls(response)

            # 4. Compare with ground truth
            is_correct = self._compare_calls(predicted_calls, item["ground_truth"])

            results.append({
                "id": item["id"],
                "prediction": predicted_calls,
                "ground_truth": item["ground_truth"],
                "is_correct": is_correct
            })

        return {"results": results, "total_samples": len(results)}
````

 Схема этого оценщика содержит три основных момента: во-первых, это построение подсказок, требующее преобразования вопросов и определений функций в наборе данных в подсказки, понятные агенту; во-вторых, извлечение вызовов функций, требующее извлечения вызовов функций из ответа агента и поддержки нескольких форматов (JSON, блоки кода и т. д.); наконец, это сопоставление AST, использующее абстрактное синтаксическое дерево для сравнения вызовов функций, что более точно, чем простое сопоставление строк.

Давайте посмотрим на реализацию извлечения вызовов функций:

```python
def _extract_function_calls(self, response: str) -> List[Dict[str, Any]]:
    """Extract function calls from response

    Supports multiple formats:
    1. JSON format: {"name": "func", "arguments": {...}}
    2. Code block format: ```python\nfunc(arg1=val1)\n```
    3. Plain text format: func(arg1=val1)
    """
    calls = []

    # Try JSON parsing
    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            if isinstance(data, dict) and "name" in data:
                calls.append(data)
            elif isinstance(data, list):
                calls.extend(data)
    except json.JSONDecodeError:
        pass

    # Try code block extraction
    code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', response, re.DOTALL)
    for code in code_blocks:
        # Parse Python function calls
        parsed_calls = self._parse_python_calls(code)
        calls.extend(parsed_calls)

    return calls
```

**(3) BFCLMetrics: Калькулятор показателей**

BFCLMetrics отвечает за расчет различных метрик оценки:

````python
class BFCLMetrics:
    """BFCL metrics calculator"""

    def compute_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute all metrics"""
        return {
            "accuracy": self._compute_accuracy(results),
            "ast_match_rate": self._compute_ast_match_rate(results),
            "parameter_accuracy": self._compute_parameter_accuracy(results),
            "f1_score": self._compute_f1_score(results),
            "category_statistics": self._compute_category_stats(results)
        }
````

**Реализация сопоставления AST**:

Сопоставление AST — это основная технология оценки BFCL. Он более интеллектуален, чем простое сопоставление строк, и может идентифицировать семантически эквивалентные вызовы функций:

```python
def _ast_match(self, pred_call: Dict, true_call: Dict) -> bool:
    """Match function calls using AST

    Advantages of AST matching:
    1. Ignore parameter order: func(a=1, b=2) equivalent to func(b=2, a=1)
    2. Recognize equivalent expressions: 2+3 equivalent to 5
    3. Ignore whitespace and format differences
    """
    # 1. Function name must match exactly
    if pred_call.get("name") != true_call.get("name"):
        return False

    # 2. Convert parameters to AST nodes
    pred_args = self._args_to_ast(pred_call.get("arguments", {}))
    true_args = self._args_to_ast(true_call.get("arguments", {}))

    # 3. Compare AST nodes
    return ast.dump(pred_args) == ast.dump(true_args)

def _args_to_ast(self, args: Dict[str, Any]) -> ast.AST:
    """Convert parameter dictionary to AST node"""
    # Construct a virtual function call
    code = f"func({', '.join(f'{k}={repr(v)}' for k, v in args.items())})"
    tree = ast.parse(code)
    return tree.body[0].value  # Return Call node
```

**(4) Инкапсуляция инструмента: BFCLEvaluationTool**

Наконец, мы инкапсулируем эти компоненты в инструмент, чтобы агенты могли напрямую вызывать его:

````python
class BFCLEvaluationTool(Tool):
    """BFCL evaluation tool"""

    def __init__(self, local_data_path: Optional[str] = None):
        super().__init__(
            name="bfcl_evaluation",
            description="Evaluate agent's tool calling capability"
        )
        self.dataset = None
        self.evaluator = None
        self.metrics_calculator = BFCLMetrics()

    def run(self, parameters: Dict[str, Any]) -> str:
        """Execute evaluation"""
        # 1. Load dataset
        self.dataset = BFCLDataset(...)

        # 2. Create evaluator
        self.evaluator = BFCLEvaluator(...)

        # 3. Run evaluation
        results = self.evaluator.evaluate(...)

        # 4. Calculate metrics
        metrics = self.metrics_calculator.compute_metrics(...)

        # 5. Return JSON results
        return json.dumps(results, ensure_ascii=False)
````

Конструкция этого инструмента соответствует трем основным принципам: сначала наследовать базовый класс Tool, чтобы следовать спецификации инструмента HelloAgents, обеспечивая плавную интеграцию с платформой; во-вторых, выполнять строгую проверку параметров, проверять необходимые параметры и предоставлять понятные подсказки об ошибках, улучшая взаимодействие с пользователем; наконец, форматируйте результаты, возвращая строку JSON для удобного анализа и отображения. Благодаря этой модульной конструкции мы внедрили систему оценки, которая проста в использовании и гибка. Пользователи могут напрямую использовать интерфейс инструмента высокого уровня для быстрого выполнения оценки или погрузиться в низкоуровневые компоненты для настройки в соответствии с особыми потребностями.

### 12.2.6 Рекомендации по расширению и оптимизации

Благодаря предыдущему обучению мы научились использовать HelloAgents для оценки BFCL. Следует отметить, что наша текущая реализация представляет собой простую копию, основанную на SimpleAgent, в основном завершающую базовые функции оценки BFCL. В практических приложениях тест BFCL содержит несколько уровней сложности и сценариев. Для достижения более высоких результатов в таблице лидеров необходима дальнейшая оптимизация и расширение.

**(1) Ограничения текущей реализации**

Наша текущая реализация SimpleAgent в основном ориентирована на построение процесса оценки с возможностью улучшения возможностей вызова инструментов. SimpleAgent использует собственный формат вызова инструментов.`[TOOL_CALL:tool_name:parameters]`, что требует активного изучения и использования LLM. В сложных сценариях производительность может не соответствовать агентам, использующим вызов собственных функций. Кроме того, в настоящее время мы тестируем только базовые категории, такие как simple_python. Для более сложных сценариев, таких как множественные, параллельные и нерелевантные сценарии, по-прежнему необходима целевая оптимизация.

**(2) Направления улучшения показателей BFCL**

Чтобы еще больше улучшить оценки BFCL, вы можете начать со следующих направлений. Во-первых, это оптимизация возможностей вызова инструментов агента: рассмотрите возможность использования LLM, которые поддерживают вызов собственных функций (например, GPT-4, Claude и т. д.), или улучшите подсказки, чтобы помочь LLM лучше понять формат вызова инструментов. Во-вторых, это расширение библиотеки инструментов: тесты BFCL включают в себя различные типы функций. Вы можете предварительно реализовать общие типы инструментов на основе характеристик набора тестовых данных, чтобы улучшить охват инструментов агента. В-третьих, это разработка различных стратегий для разных уровней сложности: например, в нескольких сценариях агентам необходимо планировать многоэтапные последовательности вызовов инструментов, в параллельных сценариях им необходимо идентифицировать вызовы инструментов, которые могут выполняться параллельно, в нерелевантных сценариях им нужно судить, действительно ли вызов инструментов необходим.

**(3) Практические рекомендации**

Разработчикам, желающим добиться лучших результатов в BFCL, рекомендуются следующие практические стратегии. Во-первых, начните с простой категории, убедитесь, что основные вызовы одиночных функций работают стабильно — это основа для последующей оптимизации. Затем постепенно тестируйте более сложные категории, такие как множественность, параллель, анализируйте случаи сбоев, находите слабые места агента. Во время оптимизации вы можете обращаться к моделям с высокими оценками в таблице лидеров BFCL, изучать их дизайнерские идеи и методы оптимизации. Между тем, для проверки рекомендуется использовать официальные инструменты оценки, чтобы обеспечить соответствие оптимизированных результатов стандартам таблицы лидеров.

Вот несколько предложений по дальнейшей обработке во время оценки:

**1. Прогрессивная оценка**

Начните с небольших выборок, постепенно увеличивая количество выборок:

```python
# Step 1: Quick test (5 samples)
results_quick = bfcl_tool.run(agent, category="simple_python", max_samples=5)

# Step 2: Medium-scale test (50 samples)
if results_quick['overall_accuracy'] > 0.8:
    results_medium = bfcl_tool.run(agent, category="simple_python", max_samples=50)

# Step 3: Full evaluation (all samples)
if results_medium['overall_accuracy'] > 0.8:
    results_full = bfcl_tool.run(agent, category="simple_python", max_samples=0)
```

**2. Многокатегорийная оценка**

Оценивайте задания разной сложности:

```python
categories = ["simple_python", "multiple", "parallel", "irrelevance"]

for category in categories:
    print(f"\nEvaluating category: {category}")
    results = bfcl_tool.run(agent, category=category, max_samples=10)
    print(f"Accuracy: {results['overall_accuracy']:.2%}")
```

**3. Сравнительная оценка**

Сравните агентов с разными конфигурациями:

```python
# Configuration 1: Default prompt
agent1 = SimpleAgent(name="Agent-Default", llm=llm)
results1 = bfcl_tool.run(agent1, category="simple_python", max_samples=10)

# Configuration 2: Optimized prompt
agent2 = SimpleAgent(name="Agent-Optimized", llm=llm)
# ... Set optimized system prompt ...
results2 = bfcl_tool.run(agent2, category="simple_python", max_samples=10)

# Compare results
print(f"Default configuration accuracy: {results1['overall_accuracy']:.2%}")
print(f"Optimized configuration accuracy: {results2['overall_accuracy']:.2%}")
```

Если ваши результаты оценки хорошие, рассмотрите возможность подачи заявки в официальную таблицу лидеров BFCL!

**Шаг 1. Подготовьте материалы для подачи**

1. Документ с описанием модели
2. Файлы результатов оценки (все категории)
3. Метод доступа к модели (API или ссылка с открытым исходным кодом)

**Шаг 2. Отправьте сообщение на GitHub**

Посетите официальный репозиторий BFCL и отправьте запрос на включение согласно инструкциям:

- Репозиторий: https://github.com/SishirPatil/gorilla.
- Руководство по подаче: см. `CONTRIBUTING.md`

**Шаг 3. Дождитесь проверки**

Команда BFCL рассмотрит вашу заявку и проверит точность результатов. После одобрения ваша модель появится в официальной таблице лидеров!



## 12.3 GAIA: General AI Assistant Capability Evaluation

### 12.3.1 Введение в тест GAIA

GAIA (General AI Assistants) — это тест оценки, запущенный совместно Meta AI и Hugging Face и ориентированный на оценку **общих возможностей AI-помощников**<sup>[2]</sup>. В отличие от BFCL, ориентированного на вызов инструментов, GAIA оценивает комплексную производительность агентов при выполнении реальных задач.

Философия проектирования GAIA такова: **Реальные проблемы часто требуют комплексного применения множества возможностей**. Превосходному ИИ-помощнику нужно не только вызывать инструменты, но и:

- **Многоэтапное рассуждение**: разбивайте сложные проблемы на несколько подзадач.
- **Применение знаний**: используйте встроенные знания и внешние базы знаний.
- **Многомодальное понимание**: обработка нескольких входных данных, таких как текст, изображения и файлы.
- **Просмотр веб-страниц**: получайте самую свежую информацию из Интернета.
- **Операции с файлами**: чтение и обработка файлов в различных форматах.

**(1) Структура набора данных GAIA**

Поняв философию оценки GAIA, давайте углубимся в конкретную структуру набора данных GAIA. GAIA содержит 466 тщательно разработанных задач из реального мира. Эти задачи разделены на три уровня сложности в зависимости от сложности и требуемых шагов рассуждения: от простых задач рассуждения с нулевым шагом до сложных задач, требующих многоэтапного сложного рассуждения, всесторонне охватывающих различные сценарии, с которыми агенты могут столкнуться в практических приложениях, как показано в Таблице 12.3:

<div align="center">
  <p>Таблица 12.3 Распределение уровней сложности набора данных GAIA</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-table-3.png" alt="" width="85%"/>
</div>

Примеры наборов данных GAIA приведены в приведенном ниже фрагменте кода:

```json
{
  "task_id": "gaia_001",
  "Question": "What is the total population of the top 3 most populous cities in California?",
  "Level": 2,
  "Final answer": "12847521",
  "file_name": "",
  "file_path": "",
  "Annotator Metadata": {
    "Steps": [
      "Search for most populous cities in California",
      "Get population data for top 3 cities",
      "Sum the populations"
    ],
    "Number of steps": 3,
    "How long did this take?": "5 minutes",
    "Tools": ["web_search", "calculator"]
  }
}
```

**Описание ключевых полей:**
-`Question`: Описание вопроса
-`Level`: Уровень сложности (1-3)
-`Final answer`: стандартный ответ (может быть числом, текстом или файлом).
-`file_name/file_path`: Вложенный файл (если есть)
-`Annotator Metadata`: Метаданные, предоставленные аннотатором (этапы рассуждения, необходимые инструменты и т. д.).

**(2) Введение в квазиточное совпадение**

GAIA использует алгоритм оценки **Quasi Exact Match**, который является официально определенным стандартом оценки GAIA. Основная идея этого алгоритма: **Сначала нормализуйте ответы, затем выполните точное сопоставление**.

Учитывая прогнозируемый ответ $A_{\text{pred}}$ и стандартный ответ $A_{\text{true}}$, функция квазиточного соответствия определяется как:

$$
\text{Quasi\_Exact\_Match}(A_{\text{pred}}, A_{\text{true}}) = \begin{cases}
1 & \text{if } \mathcal{N}(A_{\text{pred}}) = \mathcal{N}(A_{\text{true}}) \\
0 и \text{иначе}
\end{случаи}
$$

Где $\mathcal{N}(\cdot)$ — функция нормализации, применяющая разные правила в зависимости от типа ответа.

Функция нормализации применяет разные правила в зависимости от типа ответа. Для числовых типов удалите разделители-запятые (`1,000`→`1000`) и символы единиц (`$100`→`100`, `50%`→`50`), например`"$1,234.56"`нормализуется до`"1234.56"`. Для строковых типов преобразуйте их в нижний регистр (`"Apple"`→`"apple"`), удалить статьи (`"the apple"`→`"apple"`), удалите лишние пробелы (`"hello  world"`→`"hello world"`) и удалите конечные знаки препинания (`"hello."`→`"hello"`), например`"The United States"`нормализуется до`"united states"`. Для типов списков разделите элементы запятой, примените нормализацию строк к каждому элементу, отсортируйте их в алфавитном порядке, а затем снова соедините, например`"Paris, London, Berlin"`нормализуется до`"berlin,london,paris"`.

**Примеры нормализации:**

```python
# Numeric answer
Original answer: "$1,234.56"
Normalized: "1234.56"

# String answer
Original answer: "The United States of America"
Normalized: "united states of america"

# List answer
Original answer: "Paris, London, Berlin"
Normalized: "berlin, london, paris"
```

**(3) Показатели оценки GAIA**

GAIA использует следующие показатели для оценки производительности агентов:

**1. Точный коэффициент совпадения**

Коэффициент точного совпадения — это основной показатель GAIA, определяемый как доля образцов с успешным квазиточным совпадением:

$$
\text{Коэффициент точного совпадения} = \frac{1}{N} \sum_{i=1}^{N} \text{Quasi\_Exact\_Match}(A_{\text{pred},i}, A_{\text{true},i})
$$

Где:
- $N$ — общее количество выборок
- $A_{\text{pred},i}$ — предсказанный ответ $i$-й выборки
- $A_{\text{true},i}$ — стандартный ответ $i$-го образца
- $\text{Quasi\_Exact\_Match}(\cdot, \cdot) \in \{0, 1\}$ — функция квазиточного совпадения

**2. Точность по уровням**

Для каждого уровня сложности $\ell \in \{1, 2, 3\}$ рассчитайте точность для этого уровня:

$$
\text{Accuracy}_\ell = \frac{1}{|D_\ell|} \sum_{i \in D_\ell} \text{Quasi\_Exact\_Match}(A_{\text{pred},i}, A_{\text{true},i})
$$

Где $D_\ell$ — набор выборок уровня сложности $\ell$, $|D_\ell|$ — количество выборок на этом уровне.

**3. Скорость снижения уровня сложности**

Измеряет снижение производительности агента по мере увеличения сложности:

$$
\text{Скорость падения}_{\ell \to \ell+1} = \frac{\text{Точность}_\ell - \text{Точность}_{\ell+1}}{\text{Точность}_\ell}
$$

- $\text{Скорость падения}_{1 \to 2}$: Скорость падения с уровня 1 на уровень 2.
- $\text{Drop Rate}_{2 \to 3}$: Скорость падения с уровня 2 на уровень 3.

**4. Среднее количество шагов рассуждения**

Оценивает среднее количество шагов, необходимых агенту для выполнения задач:

$$
\text{Avg Steps} = \frac{1}{N_{\text{correct}}} \sum_{i \in \text{Correct}} \text{steps}_i
$$

Где $N_{\text{correct}}$ — количество правильно ответивших образцов, $\text{steps}_i$ — количество шагов рассуждения для $i$-го образца.

**Метрическая интерпретация:**

- **Точный коэффициент совпадения = 1,0**: все образцы полностью верны.
- **Коэффициент точного совпадения = 0,5**: 50 % образцов верны, 50 % образцов неверны.
- **Скорость падения = 0,3**: увеличение сложности приводит к снижению точности на 30%.
- **Скорость выпадения = 0,0**: увеличение сложности не влияет на точность (идеальный случай).

**Пример оценки:**

Предположим, мы оценили 10 образцов. Результаты можно найти в Таблице 12.4:

<div align="center">
  <p>Таблица 12.4 Распределение уровней сложности набора данных GAIA</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-table-4.png" alt="" width="85%"/>
</div>

Чтобы рассчитать метрики для этого случая, обратитесь к сценарию Python ниже:

```python
# 1. Exact match rate
total_samples = 10
correct_samples = 7  # Samples 1,2,3,5,6,8,9
exact_match_rate = correct_samples / total_samples = 0.70  # 70%

# 2. Level-wise accuracy
level_1_correct = 3  # Samples 1,2,3
level_1_total = 3
level_1_accuracy = 3 / 3 = 1.00  # 100%

level_2_correct = 2  # Samples 5,6
level_2_total = 3
level_2_accuracy = 2 / 3 = 0.67  # 67%

level_3_correct = 2  # Samples 8,9
level_3_total = 4
level_3_accuracy = 2 / 4 = 0.50  # 50%

# 3. Difficulty progression drop rate
drop_rate_1_to_2 = (1.00 - 0.67) / 1.00 = 0.33  # 33%
drop_rate_2_to_3 = (0.67 - 0.50) / 0.67 = 0.25  # 25%

print(f"Exact match rate: {exact_match_rate:.2%}")  # 70.00%
print(f"Level 1 accuracy: {level_1_accuracy:.2%}")  # 100.00%
print(f"Level 2 accuracy: {level_2_accuracy:.2%}")  # 66.67%
print(f"Level 3 accuracy: {level_3_accuracy:.2%}")  # 50.00%
print(f"Level 1→2 drop rate: {drop_rate_1_to_2:.2%}")  # 33.00%
print(f"Level 2→3 drop rate: {drop_rate_2_to_3:.2%}")  # 25.00%
```

**Анализ результатов:**

- **Общая производительность**: 70 % точного соответствия, хорошая производительность.
- **Чувствительность к сложности**: снижение на 33% с уровня 1 до уровня 2, что указывает на значительное ухудшение выполнения задач средней сложности.
- **Граница возможностей**: точность уровня 3 составляет 50 %, что указывает на возможности для улучшения при выполнении сложных задач.

Чем больше процент отбрасывания, тем более очевидно снижение возможностей агента при выполнении сложных задач.

**(4) Официальная системная подсказка GAIA**

GAIA требует использования специального системного приглашения, чтобы гарантировать, что выходные данные модели соответствуют формату оценки:

```python
GAIA_SYSTEM_PROMPT = """You are a general AI assistant. I will ask you a question. Report your thoughts, and finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER].

YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings.

If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise.

If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise.

If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string."""
```

GAIA предъявляет строгие требования к формату ответов: ответы должны быть даны в`FINAL ANSWER: [answer]`формат; для числовых ответов не используйте разделители-запятые и символы единиц; для строковых ответов не используйте артикли и сокращения; для ответов в виде списка используйте запятую и располагайте их в алфавитном порядке.

### 12.3.2 Получение набора данных GAIA

**Важное примечание**: GAIA — это **закрытый набор данных**, для получения разрешения на доступ к HuggingFace требуется предварительное заявление.

**Шаг 1. Подайте заявку на получение разрешения на доступ**

1. Посетите https://huggingface.co/datasets/gaia-benchmark/GAIA.
2. Нажмите кнопку «Запросить доступ».
3. Заполните форму заявки (обычно утверждается в течение нескольких секунд)
4. Получите свой токен HuggingFace: https://huggingface.co/settings/tokens

**Шаг 2. Настройте переменные среды**

Добавьте свой токен HuggingFace в`.env`файл:

```bash
# HuggingFace API configuration
HF_TOKEN=hf_your_token_here
```

**Метод 1: автоматическая загрузка с помощью HelloAgents (рекомендуется)**

HelloAgents автоматически обрабатывает загрузку и кэширование набора данных GAIA:

```python
from hello_agents.evaluation import GAIADataset
import os

# Ensure HF_TOKEN is set, this line is not needed if .env is configured
os.environ["HF_TOKEN"] = "hf_your_token_here"

# Automatically download to ./data/gaia/
dataset = GAIADataset(
    dataset_name="gaia-benchmark/GAIA",
    split="validation",  # or "test"
    level=1  # Optional: 1, 2, 3, None(all)
)
items = dataset.load()

print(f"Loaded {len(items)} test samples")
# Output: Loaded 53 test samples (Level 1)
```

**Принцип работы**:

- При первом запуске использует snapshot_download для загрузки всего набора данных в ./data/gaia/.
- Набор данных содержит 114 файлов (вопросы, изображения, PDF-файлы и т. д.).
- Последующие использования загружаются напрямую с локального компьютера, очень быстро.

**Структура каталогов набора данных**:
```
./data/gaia/
├── 2023/
│   ├── validation/
│   │   ├── metadata.jsonl  (165 questions)
│   │   ├── *.png, *.pdf, *.csv, *.xlsx  (attachment files)
│   └── test/
│       ├── metadata.jsonl  (301 questions)
│       └── ... (attachment files)
├── GAIA.py
└── README.md
```

**Метод 2: Загрузка вручную**

Если вы хотите вручную загрузить набор данных:

```python
from huggingface_hub import snapshot_download
import os

# Set Token
os.environ["HF_TOKEN"] = "hf_your_token_here"

# Download dataset
snapshot_download(
    repo_id="gaia-benchmark/GAIA",
    repo_type="dataset",
    local_dir="./data/gaia",
    token=os.getenv("HF_TOKEN")
)
```

**Просмотр статистики набора данных**:

```python
# View dataset statistics
stats = dataset.get_statistics()
print(f"Total samples: {stats['total_samples']}")
print(f"Level distribution: {stats['level_distribution']}")
# Output:
# Total samples: 165
# Level distribution: {1: 53, 2: 62, 3: 50}
```


### 12.3.3 Реализация оценки GAIA в HelloAgents

Как и в случае с BFCL, мы предлагаем два метода оценки. **Метод 1** рекомендуется.

**Метод 1: Оценка в один клик с использованием GAIAEvaluationTool**

Это самый простой метод, автоматически завершающий загрузку набора данных, выполнение оценки, экспорт результатов и создание отчета:

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import GAIAEvaluationTool

# GAIA official system prompt (from paper)
GAIA_SYSTEM_PROMPT = """You are a general AI assistant. I will ask you a question. Report your thoughts, and finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER].

YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings.

If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise.

If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise.

If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string."""

# 1. Create agent (using GAIA official system prompt)
llm = HelloAgentsLLM()
agent = SimpleAgent(
    name="TestAgent",
    llm=llm,
    system_prompt=GAIA_SYSTEM_PROMPT  # Key: Use GAIA official prompt
)

# 2. Create GAIA evaluation tool
gaia_tool = GAIAEvaluationTool()

# 3. One-click run evaluation
results = gaia_tool.run(
    agent=agent,
    level=1,  # Level 1: Simple tasks
    max_samples=5,  # Evaluate 5 samples
    export_results=True,  # Export GAIA format results
    generate_report=True  # Generate evaluation report
)

# 4. View results
print(f"Exact match rate: {results['exact_match_rate']:.2%}")
print(f"Partial match rate: {results['partial_match_rate']:.2%}")
print(f"Correct: {results['exact_matches']}/{results['total_samples']}")
```

**Результаты запуска:**

```
============================================================
GAIA One-Click Evaluation
============================================================

Configuration:
   Agent: TestAgent
   Difficulty level: 1
   Sample count: 5

============================================================
Step 1: Run HelloAgents Evaluation
============================================================
   Downloading from HuggingFace: gaia-benchmark/GAIA
   📥 Downloading GAIA dataset...
   ✓ Dataset download complete
   ✓ Loaded 165 samples
✅ GAIA dataset loaded
   Data source: gaia-benchmark/GAIA
   Split: validation
   Level: 1
   Sample count: 53

🌟 Starting GAIA evaluation...
   Sample count: 5
   Progress: 5/5
✅ GAIA evaluation complete
   Exact match rate: 80.00%
   Partial match rate: 80.00%

============================================================
Step 2: Export GAIA Format Results
============================================================
✅ GAIA format results exported
   Output file: evaluation_results\gaia_official\gaia_level1_result_20251011_012648.jsonl
   Sample count: 5
   Includes reasoning trace: True
📄 Submission guide generated: evaluation_results\gaia_official\SUBMISSION_GUIDE_20251011_012648.md

============================================================
Step 3: Generate Evaluation Report
============================================================
📄 Report generated: evaluation_reports\gaia_report_20251011_012648.md

============================================================
🎯 Final Results
============================================================
   Exact match rate: 80.00%
   Partial match rate: 80.00%
   Correct: 4/5
```

После завершения оценки автоматически создаются три типа файлов: первый — файл результатов в формате GAIA (`evaluation_results/gaia_official/gaia_level1_result_*.jsonl`), используя формат JSONL (по одному объекту JSON в строке), можно напрямую использовать для отправки в таблицу лидеров GAIA; второй — файл руководства по отправке (`evaluation_results/gaia_official/SUBMISSION_GUIDE_*.md`), содержащий подробные инструкции по отправке, описание формата файла результата и примечания; наконец-то отчет об оценке (`evaluation_reports/gaia_report_*.md`), содержащий сводку результатов оценки, подробные показатели, сведения об образцах и диаграммы визуализации.

**Примечание**. Если вы обнаружите, что полученные результаты оценки неудовлетворительны (например, низкая точность), это нормально. Хотя уровень 1 представляет собой одношаговые задачи на рассуждение, агентам по-прежнему необходимы возможности вызова инструментов (например, поисковой системы, калькулятора и т. д.), чтобы правильно отвечать на вопросы. Наш текущий SimpleAgent в основном используется для демонстрации процесса оценки, но есть возможности для улучшения возможностей вызова инструментов.

**Метод 2: использование набора данных + оценщика (гибкая настройка)**

Если вам нужен более детальный контроль, вы можете напрямую использовать низкоуровневые компоненты:

```python
from hello_agents.evaluation import GAIADataset, GAIAEvaluator

# 1. Load dataset
dataset = GAIADataset(level=1)
items = dataset.load()
print(f"Loaded {len(items)} samples")

# 2. Create evaluator
evaluator = GAIAEvaluator(dataset=dataset, level=1)

# 3. Run evaluation
results = evaluator.evaluate(agent, max_samples=5)

# 4. Export GAIA format results
evaluator.export_to_gaia_format(
    results,
    "gaia_results.jsonl",
    include_reasoning=True
)
```

Созданный отчет об оценке (`gaia_report_*.md`) может ссылаться на файл ниже:

```markdown
# GAIA Evaluation Report

**Generated**: 2025-10-11 01:26:48

## 📊 Evaluation Overview

- **Agent**: TestAgent
- **Difficulty Level**: 1
- **Total Samples**: 2
- **Exact Matches**: 1
- **Partial Matches**: 1
- **Exact Match Rate**: 50.00%
- **Partial Match Rate**: 50.00%

## 📈 Detailed Metrics

### Level-wise Accuracy

- **Level 1**: 50.00% exact / 50.00% partial (1/2)

## 📝 Sample Details (First 10)

| Task ID | Level | Predicted Answer | Correct Answer | Exact Match | Partial Match |
|---------|-------|------------------|----------------|-------------|---------------|
| e1fc63a2-da7a-432f-be78-7c4a95598703 | 1 | 24000 | 17 | ❌ | ❌ |
| 8e867cd7-cff9-4e6c-867a-ff5ddc2550be | 1 | 3 | 3 | ✅ | ✅ |

## 📊 Accuracy Visualization

Exact match: █████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░ 50.00%
Partial match: █████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░ 50.00%


## 💡 Recommendations

- ⚠️ Average performance, needs improvement.
- 💡 Suggest checking tool usage and multi-step reasoning capabilities.
```

**Сгенерированные результаты в формате GAIA (`gaia_level1_result_*.jsonl`):**

```json
{"task_id": "e1fc63a2-da7a-432f-be78-7c4a95598703", "model_answer": "24000", "reasoning_trace": "24000"}
{"task_id": "8e867cd7-cff9-4e6c-867a-ff5ddc2550be", "model_answer": "3", "reasoning_trace": "3"}
```

### 12.3.4 Отправка результатов в официальную таблицу лидеров GAIA

После проведения оценки с помощью GAIAEvaluationTool в файле генерируются файлы, необходимые для отправки, и подробные инструкции по отправке.`evaluation_results/gaia_official/`каталог.

1. **Файл результатов формата GAIA**: `gaia_level1_result_*.jsonl`
   ```json
   {"task_id": "xxx", "model_answer": "answer", "reasoning_trace": "reasoning process"}
   {"task_id": "yyy", "model_answer": "answer", "reasoning_trace": "reasoning process"}
   ```

2. **Файл руководства по отправке**: `SUBMISSION_GUIDE_*.md`

Откройте автоматически созданный`SUBMISSION_GUIDE_*.md`файл, который содержит полное руководство по подаче:

В частности, откройте браузер и посетите:
```
https://huggingface.co/spaces/gaia-benchmark/leaderboard
```

Как показано на рисунке 12.4, заполните информацию в форме подачи:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-4.png" alt="" width="85%"/>
  <p>Рисунок 12.4 Схема процесса оценки GAIA</p>
</div>

Перед отправкой вы можете вручную проверить сгенерированный файл JSONL:

```python
import json

# Read result file
with open("evaluation_results/gaia_official/gaia_level1_result_*.jsonl", "r") as f:
    for line in f:
        result = json.loads(line)
        print(f"Task ID: {result['task_id']}")
        print(f"Answer: {result['model_answer']}")
        print(f"Reasoning: {result['reasoning_trace']}")
        print("-" * 50)
```

### 12.3.5 Детали реализации основного компонента

Реализация системы оценки GAIA аналогична BFCL, но имеет некоторые специальные конструкции для общей оценки возможностей.

**(1) GAIADataset: мультимодальный загрузчик данных**

Особенностью набора данных GAIA является то, что он содержит мультимодальные данные (текст, файлы, изображения и т. д.):

````python
class GAIADataset:
    """GAIA dataset loader

    Supports loading GAIA dataset from HuggingFace (gated dataset)
    """

    def __init__(
        self,
        level: Optional[int] = None,
        split: str = "validation",
        local_data_dir: Optional[str] = None
    ):
        self.level = level
        self.split = split
        self.local_data_dir = local_data_dir or "./data/gaia"
        self.data = []

    def load(self) -> List[Dict[str, Any]]:
        """Load dataset"""
        # Download from HuggingFace
        items = self._load_from_huggingface()

        # Filter by level
        if self.level:
            items = [item for item in items if item.get("level") == self.level]

        self.data = items
        return items

    def _load_from_huggingface(self) -> List[Dict[str, Any]]:
        """Download GAIA dataset from HuggingFace"""
        from huggingface_hub import snapshot_download
        import json

        # Download dataset
        repo_id = "gaia-benchmark/GAIA"
        local_dir = snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=self.local_data_dir,
            local_dir_use_symlinks=False
        )

        # Load JSONL file
        data_file = Path(local_dir) / "2023" / self.split / "metadata.jsonl"
        items = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                items.append(self._standardize_item(item))

        return items
````

**(2) GAIAEvaluator: реализация официального алгоритма оценки GAIA**

При оценке GAIA используется алгоритм **Quasi Exact Match**, требующий специальной нормализации ответов и логики сопоставления:

````python
class GAIAEvaluator:
    """GAIA evaluator

    Implements GAIA official Quasi Exact Match evaluation algorithm
    """

    def evaluate(self, agent: Any, max_samples: Optional[int] = None) -> Dict[str, Any]:
        """Execute evaluation"""
        dataset_items = self.dataset.load()

        if max_samples:
            dataset_items = dataset_items[:max_samples]

        results = []
        for i, item in enumerate(dataset_items, 1):
            # 1. Construct prompt
            prompt = self._build_prompt(item["question"], item)

            # 2. Call agent
            response = agent.run(prompt)

            # 3. Extract answer (GAIA format: FINAL ANSWER: [answer])
            predicted_answer = self._extract_answer(response)

            # 4. Normalize answer (GAIA official rules)
            normalized_pred = self._normalize_answer(predicted_answer)
            normalized_truth = self._normalize_answer(item["final_answer"])

            # 5. Quasi exact match
            exact_match = (normalized_pred == normalized_truth)

            results.append({
                "task_id": item["task_id"],
                "predicted": predicted_answer,
                "expected": item["final_answer"],
                "exact_match": exact_match,
                "level": item.get("level", 0)
            })

        return self._format_results(results)
````

GAIA использует специальные правила нормализации для обработки различных типов ответов:

```python
def _normalize_answer(self, answer: str) -> str:
    """Normalize answer string (GAIA official normalization rules)

    Rules:
    1. Numbers: Remove comma separators and unit symbols
    2. Strings: Remove articles, convert to lowercase, remove extra spaces
    3. Lists: Comma-separated, sorted alphabetically
    """
    if not answer:
        return ""

    answer = answer.strip()

    # Check if it's a comma-separated list
    if ',' in answer:
        parts = [self._normalize_single_answer(p.strip()) for p in answer.split(',')]
        parts.sort()  # GAIA requires alphabetical sorting
        return ','.join(parts)
    else:
        return self._normalize_single_answer(answer)

def _normalize_single_answer(self, answer: str) -> str:
    """Normalize single answer (answer without commas)"""
    answer = answer.strip().lower()

    # Remove common articles
    articles = ['the', 'a', 'an']
    words = answer.split()
    if words and words[0] in articles:
        words = words[1:]
        answer = ' '.join(words)

    # Remove currency symbols and percent signs
    answer = answer.replace('$', '').replace('%', '').replace('€', '').replace('£', '')

    # Remove comma separators in numbers
    answer = re.sub(r'(\d),(\d)', r'\1\2', answer)

    # Remove extra spaces
    answer = ' '.join(answer.split())

    # Remove trailing punctuation
    answer = answer.rstrip('.,;:!?')

    return answer
```

GAIA требует, чтобы выходной формат модели был`FINAL ANSWER: [answer]`:

```python
def _extract_answer(self, response: str) -> str:
    """Extract answer from response (GAIA format)

    GAIA requires answer format: FINAL ANSWER: [answer]
    """
    # First try to extract GAIA official format answer
    final_answer_pattern = r'FINAL ANSWER:\s*(.+?)(?:\n|$)'
    match = re.search(final_answer_pattern, response, re.IGNORECASE | re.MULTILINE)
    if match:
        answer = match.group(1).strip()
        # Remove possible brackets
        answer = answer.strip('[]')
        return answer

    # Fallback: Look for other answer markers
    answer_patterns = [
        r'答案[：:]\s*(.+)',
        r'最终答案[：:]\s*(.+)',
        r'Final answer[：:]\s*(.+)',
        r'Answer[：:]\s*(.+)',
    ]

    for pattern in answer_patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # If no marker found, return last non-empty line
    lines = response.strip().split('\n')
    for line in reversed(lines):
        line = line.strip()
        if line and not line.startswith('#'):
            return line

    return response.strip()
```

После завершения оценки можно экспортировать в формат JSONL, требуемый официальным представителем GAIA:

```python
def export_to_gaia_format(
    self,
    results: Dict[str, Any],
    output_path: Union[str, Path],
    include_reasoning: bool = True
) -> None:
    """Export to GAIA official format (JSONL)

    GAIA required format:
    {"task_id": "xxx", "model_answer": "answer", "reasoning_trace": "reasoning process"}
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results.get("detailed_results", []):
            entry = {
                "task_id": result["task_id"],
                "model_answer": result["predicted"]
            }

            if include_reasoning:
                entry["reasoning_trace"] = result.get("response", result["predicted"])

            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
```

**(3) GAIAEvaluationTool: инструмент оценки в один клик**

GAIAEvaluationTool инкапсулирует полный процесс оценки, обеспечивая функциональность оценки одним щелчком мыши:

````python
class GAIAEvaluationTool(Tool):
    """GAIA evaluation tool

    Provides one-click evaluation functionality:
    1. Run HelloAgents evaluation
    2. Export GAIA format results
    3. Generate evaluation report
    4. Generate submission guide
    """

    def run(
        self,
        agent: Any,
        level: Optional[int] = None,
        max_samples: Optional[int] = None,
        local_data_dir: Optional[str] = None,
        export_results: bool = True,
        generate_report: bool = True
    ) -> Dict[str, Any]:
        """Execute GAIA one-click evaluation"""
        # Step 1: Run HelloAgents evaluation
        results = self._run_evaluation(agent, level, max_samples, local_data_dir)

        # Step 2: Export GAIA format results
        if export_results:
            self._export_results(results)

        # Step 3: Generate evaluation report
        if generate_report:
            self.generate_report(results)

        return results
````

GAIAEvaluationTool автоматически генерирует отчет об оценке:

```python
def generate_report(
    self,
    results: Dict[str, Any],
    output_file: Optional[Union[str, Path]] = None
) -> str:
    """Generate evaluation report"""
    report = f"""# GAIA Evaluation Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 Evaluation Overview

- **Agent**: {results.get("agent_name", "Unknown")}
- **Difficulty Level**: {results.get("level_filter") or 'All'}
- **Total Samples**: {results.get("total_samples", 0)}
- **Exact Matches**: {results.get("exact_matches", 0)}
- **Exact Match Rate**: {results.get("exact_match_rate", 0):.2%}

## 📈 Detailed Metrics

### Level-wise Accuracy

{self._format_level_metrics(results.get("level_metrics", {}))}

## 📝 Sample Details (First 10)

{self._format_sample_details(results.get("detailed_results", [])[:10])}

## 📊 Accuracy Visualization

{self._format_visualization(results.get("exact_match_rate", 0))}

## 💡 Recommendations

{self._format_suggestions(results.get("exact_match_rate", 0))}
"""

    # Save report
    if output_file is None:
        output_dir = Path("./evaluation_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"gaia_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    return report
```

## 12.4 Оценка качества генерации данных

При разработке систем искусственного интеллекта высококачественные обучающие данные являются основой производительности системы. В этом разделе рассказывается, как использовать платформу HelloAgents для оценки качества сгенерированных данных на примере создания математических задач в стиле AIME (American Invitational Mathematics Examination)<sup>[9]</sup>.

AIME — это соревнование по математике средней сложности, проводимое Математической ассоциацией Америки (MAA), занимающее промежуточное положение между AMC 10/12 и Математической олимпиадой США (USAMO). Задачи AIME имеют отличительные характеристики: ответом каждой задачи является целое число от 0 до 999, задачи охватывают несколько математических областей, включая алгебру, геометрию, теорию чисел, комбинаторику и вероятность, требуют многоэтапных рассуждений, но не требуют сложной теории и имеют умеренную сложность (эквивалент задач AIME 6–9). Эти характеристики делают задачи AIME идеальным эталоном для оценки качества генерации математических задач: унифицированный формат ответов облегчает автоматическую оценку, а умеренная сложность подходит для крупномасштабной генерации. Мы используем`TianHongZXY/aime-1983-2025`набор данных HuggingFace в качестве эталона, который содержит более 900 реальных проблем AIME с 1983 по 2025 год, предоставляя богатые эталонные образцы для нашей генерации и оценки.

### 12.4.1 Обзор методов оценки

При оценке качества генерации данных мы используем три взаимодополняющих метода оценки: судья LLM, процент побед и ручная проверка. Есть две важные причины для выбора этих трех методов. Во-первых, с методологической точки зрения, это широко используемые автоматизированные схемы оценки в текущей области агентов и общепринятые практики во многих научных работах, имеющие широкое признание и практическое обоснование. Во-вторых, с точки зрения применимости, эти три метода естественным образом подходят для нашего сценария оценки: судья LLM и процент побед используются для оценки качества генерации задач (многомерная оценка по правильности, ясности, сопоставлению трудностей и т. д.), тогда как ручная проверка используется для оценки качества генерации ответов (проверка точности ответов с помощью экспертов), такое разделение труда очень разумно и легко для понимания.

Ниже мы подробно представляем конкретную реализацию этих трех методов оценки. Ход реализации всего случая показан на рисунке 12.5:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-5.png" alt="" width="85%"/>
  <p>Рисунок 12.5 Блок-схема оценки качества генерации данных</p>
</div>

**(1) Оценка судьи LLM**

**Мотивация проектирования**: при оценке качества генерации данных нам необходимо быстро и последовательно оценить качество большого количества сгенерированных проблем. Традиционная ручная оценка, хотя и точна, является дорогостоящей и неэффективной, что затрудняет удовлетворение требований крупномасштабной генерации данных. LLM Judge, используя большие языковые модели в качестве судей, может автоматически оценивать качество сгенерированных данных по нескольким измерениям, что не только значительно повышает эффективность оценки, но и обеспечивает согласованность стандартов оценки. Что еще более важно, LLM Judge может предоставить подробные причины выставления оценок и предложения по улучшению, помогая нам понять сильные и слабые стороны сгенерированных данных и указывая направления для последующей оптимизации.

В нашей реализации LLM Judge оценивает качество задач AIME по четырем ключевым измерениям:

<div align="center">
  <p>Таблица 12.5. Размеры оценки судьями LLM задач AIME</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-table-5.png" alt="" width="85%"/>
</div>

После получения оценок по четырем измерениям нам необходимо объединить эти оценки в общие показатели оценки. Мы определяем три ключевых показателя для измерения уровня качества создаваемых проблем:

**Показатели оценки**:

**1. Средняя оценка**: подсчитайте среднюю оценку всех проблем по четырем измерениям, отражающую общий уровень качества создаваемых проблем.
$$
\text{Средний балл} = \frac{1}{N} \sum_{i=1}^{N} \frac{\sum_{d=1}^{4} S_{i,d}}{4}
$$

**2. Проходной балл**: подсчитайте долю задач со средним баллом 3,5 или выше, что отражает базовую гарантию качества создаваемых задач.

$$
\text{Проходной балл} = \frac{|\{i : \text{Score}_i \geq 3.5\}|}{N}
$$

**3. Оценка «отлично»**: подсчитайте долю задач со средним баллом 4,5 или выше, что отражает долю созданных задач высокого качества.

$$
\text{Отличная ставка} = \frac{|\{i : \text{Score}_i \geq 4,5\}|}{N}
$$

Где:
- $N$ — общее количество оцененных задач.
- $S_{i,d}$ — оценка $i$-й задачи по $d$-му измерению (1-5 баллов)
- $\text{Score}_i$ — средний балл $i$-й задачи (средний балл по четырем измерениям)

Эти три показателя отражают качество генерации с разных точек зрения: средний балл показывает общий уровень, процент проходимости обеспечивает базовое качество, отличный показатель измеряет качество вывода.

**(2) Оценка процента побед**

**Мотивация дизайна**: Хотя LLM Judge может обеспечить многомерную абсолютную оценку, нам также нужен относительный показатель оценки, чтобы измерить разрыв в качестве между сгенерированными и реальными проблемами. Оценка процента побед посредством парного сравнения позволяет LLM напрямую судить о том, что лучше между сгенерированными и реальными проблемами. Это относительное сравнение больше соответствует привычкам человека в суждениях, чем абсолютная оценка, и позволяет легче обнаружить относительные преимущества и недостатки возникающих проблем. В идеале, если качество сгенерированных задач близко к реальным, процент побед должен составлять около 50 % (т. е. как сгенерированные, так и реальные проблемы имеют коэффициент выигрыша по 50 %). Этот показатель прост и интуитивно понятен и позволяет быстро оценить общий уровень качества системы генерации.

В нашей реализации оценка процента выигрышей осуществляется по схеме, показанной на рис. 12.6:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-6.png" alt="" width="85%"/>
  <p>Рисунок 12.6 Блок-схема оценки качества генерации данных</p>
</div>

При оценке попарного сравнения каждое сравнение дает три возможных результата: выигрыш в сгенерированной проблеме (Победа), выигрыш в реальной проблеме (Проигрыш) или ничья (Ничья). Мы оцениваем качество сгенерированных задач, посчитав пропорции этих трех результатов:

**Показатели оценки**:

**1. Процент побед**: доля сгенерированных проблем, признанных лучшими, что отражает преимущества сгенерированных проблем по сравнению с реальными проблемами.

$$
\text{Процент побед} = \frac{\text{Выигрыши}}{\text{Всего сравнений}}
$$

**2. Коэффициент потерь**: доля реальных проблем, оцененных как лучшие, что отражает недостатки созданных проблем по сравнению с реальными проблемами.

$$
\text{Коэффициент потерь} = \frac{\text{Потери}}{\text{Всего сравнений}}
$$

**3. Ничья**: доля оценивается как эквивалентное качество, отражающее сходство между сгенерированными и реальными проблемами.

$$
\text{Связной коэффициент} = \frac{\text{Связи}}{\text{Общее количество сравнений}}
$$

Где «Общее количество сравнений» — это общее количество сравнений, «Выигрыши», «Проигрыши» и «Ничьи» — это количество сгенерированных проблемных побед, проигрышей и ничьих соответственно. Эти три показателя удовлетворяют следующим критериям: процент побед + коэффициент проигрышей + коэффициент ничьей = 100%.

**Идеальный результат**: процент побед ≈ 50% (что указывает на качество генерации, близкое к реальным проблемам). Если процент побед значительно ниже 50%, это означает, что качество сгенерированных проблем уступает реальным проблемам и стратегия генерации требует оптимизации; Если процент побед значительно превышает 50%, это может указывать на то, что сгенерированные проблемы в некоторых аспектах превосходят реальные проблемы, или что в стандартах оценки существует предвзятость.

**(3) Ручная проверка**

**Мотивация при проектировании**: Хотя LLM Judge и Winrate могут автоматически оценивать качество задач, для математических задач, требующих строгого логического рассуждения, ручная проверка по-прежнему необходима. Особенно при оценке качества генерации ответов необходимы эксперты для проверки точности ответов, полноты шагов решения и строгости математических рассуждений. Кроме того, ручная проверка может выявить проблемы, которые автоматическая оценка может пропустить, например субъективные факторы, такие как инновации в проблемах и интерес. Чтобы повысить эффективность и удобство ручной проверки, мы разработали веб-интерфейс на основе Gradio, позволяющий проверяющим удобно просматривать проблемы, оценивать, комментировать статус и добавлять комментарии, что значительно снижает барьер для ручной проверки.

В нашей реализации ручная проверка проводится в следующие этапы:

1. Прочитать задачу, ответ, решение
2. Оценка (1-5 баллов): правильность, ясность, сложность соответствия, полнота.
3. Статус аннотации:
   - ✅ одобрено (принято)
   - ❌ отклонено (отклонено)
   - 🔄 Needs_revision (нужна доработка)
4. Добавить комментарии

### 12.4.2 Архитектура системы

Система генерации и оценки данных имеет модульную конструкцию:

```
data_generation/
├── aime_generator.py              # AIME problem generator
├── human_verification_ui.py       # Manual verification interface
├── run_complete_evaluation.py     # Complete evaluation flow
│
├── generated_data/                # Generated data
│   ├── aime_generated_XXXXXX.json
│   └── generation_report_XXXXXX.md
│
└── evaluation_results/            # Evaluation results
    └── XXXXXX/
        ├── llm_judge/
        ├── win_rate/
        └── comprehensive_report.md
```

Система содержит четыре основных компонента: во-первых, это AIMEGenerator (генератор задач), использующий структуру HelloAgents для генерации задач в стиле AIME, поддерживающий пакетную генерацию и сохранение прогресса, а также автоматическую обработку ограничений скорости API; во-вторых, LLMJudgeTool (инструмент оценки LLM Judge), обеспечивающий четырехмерную оценку качества, автоматически генерирующий результаты JSON и отчеты Markdown; третий — WinRateTool (инструмент оценки процента выигрышей), рассчитывающий процент выигрышей, коэффициент проигрышей и коэффициент ничьей посредством оценки попарного сравнения; наконец, это HumanVerificationUI (интерфейс ручной проверки), основанный на веб-интерфейсе Gradio, поддерживающий оценку и аннотацию статуса.

### 12.4.3 Реализация генератора задач AIME

```python
class AIMEGenerator:
    """AIME Problem Generator"""

    def __init__(
        self,
        llm: HelloAgentsLLM = None,
        delay_seconds: float = 1.0,
        use_reference_examples: bool = True,
        reference_dataset: str = "TianHongZXY/aime-1983-2025"
    ):
        self.llm = llm or HelloAgentsLLM()
        self.agent = SimpleAgent(
            name="AIME Generator",
            llm=self.llm,
            system_prompt="You are a professional mathematics competition problem designer."
        )
        self.delay_seconds = delay_seconds
        self.use_reference_examples = use_reference_examples

        # Load reference examples from 900+ AIME problems (1983-2025)
        if use_reference_examples:
            dataset = load_dataset(reference_dataset, split="test")
            self.reference_examples = list(dataset)
```

Наша цель — создать набор данных аналогичного стиля, поэтому мы случайным образом выбираем эталонные примеры из более чем 900 реальных задач AIME (1983–2025 гг.).

Создание подсказки по созданию дизайна (на английском языке):

```python
GENERATION_PROMPT = """You are a professional mathematics competition problem designer, skilled in creating AIME (American Invitational Mathematics Examination) style problems.

【Reference Example】(For style reference only, please generate a completely different problem)
Problem: {example_problem}
Answer: {example_answer}

AIME Problem Characteristics:
1. Answer: An integer between 0 and 999
2. Topics: Algebra, Geometry, Number Theory, Combinatorics, Probability, etc.
3. Style: Requires multi-step reasoning, but no advanced theory
4. Difficulty: Medium to hard (similar to AIME problems 6-9)

Please generate a **completely different** AIME-style mathematics problem, including:
1. Problem statement (clear and complete, different from the reference)
2. Answer (an integer between 0 and 999, different from the reference)
3. Detailed solution (including all reasoning steps)
4. Topic classification (Algebra/Geometry/Number Theory/Combinatorics/Probability)

Please output in the following JSON format:
{
    "problem": "Problem statement in English",
    "answer": 123,
    "solution": "Detailed solution steps in English",
    "topic": "Algebra"
}
"""
```

Мы решили создавать задачи на английском языке по четырем важным причинам: во-первых, это соответствие реальным проблемам AIME (AIME — это соревнование по английскому языку, создание задач на английском языке более разумно), во-вторых, обеспечение справедливости оценки (оценка судьи LLM более справедлива, когда английский или английский), в-третьих, содействие интернационализации (английские задачи могут использоваться более широко) и, наконец, избежание проблем с переводом (не нужно беспокоиться о точности китайско-английского перевода).

Реализация пакетной генерации:

```python
def generate_and_save(self, num_problems: int = 30, output_dir: str = "data_generation/generated_data"):
    """Generate and save problems with intelligent delay"""
    # Clean old checkpoints
    for file in os.listdir(output_dir):
        if file.startswith("checkpoint_") and file.endswith(".json"):
            os.remove(os.path.join(output_dir, file))

    # Generate with tqdm progress bar
    with tqdm(total=num_problems, desc="Generating AIME problems", unit="problem") as pbar:
        last_call_time = 0

        for i in range(num_problems):
            # Ensure minimum delay between API calls
            if last_call_time > 0:
                elapsed = time.time() - last_call_time
                if elapsed < self.delay_seconds:
                    wait_time = self.delay_seconds - elapsed
                    time.sleep(wait_time)

            # Generate problem (randomly select reference example)
            start_time = time.time()
            problem = self.generate_single()
            last_call_time = time.time()
            generation_time = last_call_time - start_time

            # Update progress bar
            pbar.set_postfix({
                "topic": problem.get('topic', 'N/A'),
                "answer": problem.get('answer', 'N/A'),
                "time": f"{generation_time:.1f}s"
            })
            pbar.update(1)

    return generated_data_path
```

Поддержка математических формул LaTeX:

Сгенерированные задачи AIME содержат математические формулы LaTeX (например,`$\frac{a}{b}$`, `$\sqrt{x}$`), требующий специальной обработки анализа JSON:

```python
def _parse_response(self, response: str) -> Dict[str, Any]:
    """Parse LLM response (supports LaTeX mathematical formulas)"""
    import re

    # Extract JSON part
    if "```json» в ответ:
        json_str = ответ.split("```json")[1].split("```")[0].strip()
    еще:
        json_str = ответ.полоса()

попробуйте:
        проблемные_данные = json.loads(json_str)
    кроме json.JSONDecodeError:
        # Исправить проблему с выходом LaTeX: преобразовать \frac в \\frac
        # Регулярное выражение: найти неэкранированную обратную косую черту
        фиксированный_json_str = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', json_str)
        проблемные_данные = json.loads(fixed_json_str)

вернуть данные_проблемы
```

Backslashes in LaTeX formulas (such as `\frac`, `\sqrt`) are illegal escape characters in JSON, causing parsing failure:
```
Недопустимый \escape: строка 4, столбец 185 (символ 375).
```

By using regular expressions to replace unescaped backslashes with double backslashes, making them legal in JSON.

### 12.4.4 LLM Judge Evaluation Tool

LLM Judge tool uses LLM as judge to conduct multi-dimensional evaluation of generated problems.

```питон
класс LLMJudgeTool(Инструмент):
    """Инструмент оценки судей LLM"""

def run(self, params: Dict[str, Any]) -> str:
        """Провести оценку судьи LLM"""
        # 1. Загрузка сгенерированных данных
        gen_dataset = AIDataset(dataset_type="generated", data_path=params["generated_data_path"])
        gen_problems = gen_dataset.load()

# 2. Загрузка справочных данных (AIME 2025)
        ref_dataset = AIDataset(dataset_type="real", год=2025)
        ref_problems = ref_dataset.load()

# 3. Создать оценщик
        evaluator = LLMJudgeEvaluator(llm=self.llm, Judge_model=params.get("judge_model", "gpt-4o"))

# 4. Запустите оценку
        результаты = evaluator.evaluate_batch(gen_problems, max_samples=params.get("max_samples"))

# 5. Сохранить результаты
        evaluator.export_results(результаты, файл_результата)

# 6. Создать отчет
        self._generate_report(результаты, файл_отчета)

return json.dumps({"статус": "успех", "метрики": результаты["метрики"]})
```

**Evaluation Prompt**:

```питон
EVALUATION_PROMPT = """Пожалуйста, оцените качество следующей математической задачи AIME.

Проблема:
{проблема}

Ответ: {ответ}

Решение:
{решение}

Пожалуйста, оцените по следующим 4 параметрам (1–5 баллов):

1. **Правильность**: правильна ли математическая логика, верен ли ответ.
2. **Ясность**: ясна ли постановка задачи, легко ли понять решение?
3. **Соответствие сложности**: соответствует ли сложность стандартам AIME (от средней до высокой)
4. **Полнота**. Являются ли этапы решения завершенными, включает ли оно необходимое обоснование?

Пожалуйста, выведите данные в следующем формате JSON:
{
    «правильность»: 5,
    «ясность»: 4,
    «difficulty_match»: 4,
    «полнота»: 5,
    "comments": "Причина оценки"
}
"""
```

**Evaluation Report Example**:

```уценка
# Отчет об оценке судьи LLM

## Общий балл

- **Средний общий балл**: 4,2/5,0
- **Процент сдачи**: 85,0% (≥3,5 баллов)
- **Отличный рейтинг**: 40,0% (≥4,5 баллов)

## Оценки измерений

| Размерность | Средний балл | Рейтинг |
|------|--------|------|
| Корректность | 4,3/5,0 | Хорошо ⭐⭐⭐⭐ |
| Ясность | 4,1/5,0 | Хорошо ⭐⭐⭐⭐ |
| Матч сложности | 4.0/5.0 | Хорошо ⭐⭐⭐⭐ |
| Полнота | 4,4/5,0 | Хорошо ⭐⭐⭐⭐ |
```

### 12.4.5 Win Rate Evaluation Tool

Win Rate tool evaluates the quality of generated data relative to real problems through pairwise comparison.

```питон
класс WinRateTool(Инструмент):
    """Инструмент оценки винрейта"""

def run(self, params: Dict[str, Any]) -> str:
        """Оценка процента побед"""
        # 1. Загрузка сгенерированных данных
        gen_dataset = AIDataset(dataset_type="generated", data_path=params["generated_data_path"])
        gen_problems = gen_dataset.load()

# 2. Загрузка справочных данных (AIME 2025)
        ref_dataset = AIDataset(dataset_type="real", год=2025)
        ref_problems = ref_dataset.load()

# 3. Создать оценщик
        evaluator = WinRateEvaluator(llm=self.llm, Judge_model=params.get("judge_model", "gpt-4o"))

# 4. Запустите оценку
        результаты = evaluator.evaluate_win_rate(gen_problems, ref_problems, num_comparisons=params.get("num_comparisons"))

# 5. Сохранить результаты и сообщить
        evaluator.export_results(результаты, файл_результата)
        self._generate_report(результаты, файл_отчета)

return json.dumps({"статус": "успех", "метрики": результаты["метрики"]})
```

AIDataset is responsible for loading generated data and AIME real problem data, supporting two data types:

```питон
класс AIDataset:
    """Загрузчик набора данных AI

Поддерживает два типа данных:
    1. сгенерировано: сгенерированные данные (формат JSON).
    2. реальные: реальные проблемы AIME (загружается с HuggingFace)
    """

защита __init__(
        сам,
        dataset_type: str = "сгенерировано",
        путь_данных: Необязательный[str] = Нет,
        год: Необязательно[int] = Нет
    ):
        self.dataset_type = dataset_type
        self.data_path = путь_к данным
        self.year = год # Только для реального типа, по умолчанию 2025 год.

def load(self) -> List[Dict[str, Any]]:
        """Загрузить набор данных"""
        если self.dataset_type == "сгенерировано":
            вернуть self._load_generated_data()
        elif self.dataset_type == "реальный":
            вернуть self._load_real_data()

def _load_real_data(self) -> List[Dict[str, Any]]:
        """Загрузить реальные проблемы AIME 2025 из HuggingFace"""
        из humgingface_hub импортировать снимок_загрузки

# Используйте набор данных AIME 2025
        repo_id = "math-ai/aime25"

# Загрузить набор данных
        local_dir = snapshot_download(
            repo_id=repo_id,
            repo_type="набор данных"
        )

# Читаем файл JSONL
        data_file = list(Path(local_dir).glob("*.jsonl"))[0]
        данные = []
        с open(data_file, 'r',coding='utf-8') как f:
            для строки в f:
                если линия.strip():
                    data.append(json.loads(строка))

# Унифицировать формат данных (AIME 2025 использует имена полей в нижнем регистре)
        проблемы = []
        для idx, элемент в перечислении (данные):
            проблема = {
                "problem_id": item.get("id", f"aime_2025_{idx}"),
                "проблема": item.get("проблема", ""),
                "ответ": item.get("ответ", ""),
                "solution": item.get("solution", ""), # AIME 2025 не имеет поля решения
            }
            проблемы.append(проблема)

проблемы с возвратом
```

We choose to use only AIME 2025 dataset for four reasons: first is data timeliness (2025 is the latest AIME competition data), second is simplified maintenance (maintaining only one dataset, code is more concise), third is unified format (JSONL format, field names unified to lowercase), and finally is sufficient representativeness (30 problems are enough to evaluate generation quality).

**Comparison Prompt**:

```питон
COMPARISON_PROMPT = """Пожалуйста, сравните качество следующих двух математических задач AIME и решите, какая из них лучше.

【Проблема А – сгенерированная проблема】
Проблема: {problem_a}
Ответ: {answer_a}
Решение: {solution_a}

【Проблема B – настоящая проблема AIME】
Проблема: {problem_b}
Ответ: {answer_b}
Решение: {solution_b}

Пожалуйста, сравните по следующим аспектам:
1. Строгость математической логики
2. Ясность постановки задачи
3. Разумность сложности
4. Полнота решения.

Пожалуйста, выведите данные в следующем формате JSON:
{
    «победитель»: «А», «Б» или «Ничья»,
    "reason": "Причина решения"
}
"""
```

**Evaluation Report Example**:

```уценка
# Отчет об оценке процента побед

## Статистика выигрышей

| Метрическая | Значение | Процент |
|------|------|--------|
| Сгенерированные данные выигрывают | 9 раз | 45,0% |
| Победа AIME «Реальные проблемы» | 8 раз | 40,0% |
| Галстук | 3 раза | 15,0% |

**Процент побед**: 45,0%

✅ **Хорошо**: качество полученных данных близко к эталонным (разрыв <10%).
```

### 12.4.6 Manual Verification Interface

Use Gradio to create Web interface, supporting manual verification of generated problems.

```питон
класс HumanVerificationUI:
    """Интерфейс ручной проверки"""

def launch(self, доля: bool = False):
        """Запустить интерфейс Gradio"""
        с gr.Blocks(title="Проверка вручную проблем AIME") в качестве демонстрации:
            gr.Markdown("# 🎯 Система проверки руководства по проблемам AIME")

с gr.Row():
                с gr.Column(scale=2):
                    # Проблемная область отображения
                    проблемный_текст = gr.Textbox(label="Описание проблемы", строк=5, интерактивный=False)
                    ответ_текст = gr.Textbox(label="Ответ", интерактивный=False)
                    Solution_text = gr.Textbox(label="Процесс решения", строк=10, интерактивный=False)

с gr.Column(масштаб=1):
                    # Зона подсчета очков
                    корректность_слайдер = gr.Slider(1, 5, значение=3, шаг=1, метка="Правильность")
                    ясность_слайдер = gr.Slider(1, 5, значение=3, шаг=1, label="Ясность")
                    сложность_слайдер = gr.Slider(1, 5, значение=3, шаг=1, label="Соответствие сложности")
                    Completeness_slider = gr.Slider(1, 5, значение=3, шаг=1, label="Полнота")

# Выбор статуса
                    status_radio = gr.Radio(
                        choice=["одобрено", "отклонено", "needs_revision"],
                        значение = «одобрено»,
                        метка="Статус"
                    )

# Кнопка подтверждения
                    verify_btn = gr.Button(" ✅ Отправить подтверждение",variant="primary")

demo.launch(share=share, server_name="127.0.0.1", server_port=7860)
```

**Usage Method**:

```бить
# Запускаем интерфейс ручной проверки
python data_generation/human_verification_ui.py data_ogenic/generated_data/aime_generated_XXXXXX.json

# Откройте браузер и посетитеhttp://127.0.0.1:7860
```

The final effect can be referenced in Рис. 12.7. For problem correctness, manual review is best:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/12-figures/12-7.png" alt="" width="85%"/>
  <p>Рис. 12.7 AIME Problem Manual Verification Page</p>
</div>

**Verification Process**:

1. Open verification interface in browser
2. Read problem, answer, solution
3. Score from 4 dimensions (1-5 points)
4. Select verification status (approved/rejected/needs_revision)
5. Add comments (optional)
6. Click "Submit Verification"
7. View next problem

**Verification Result Saving**:

Verification results are automatically saved as `<data_path>_verifications.json`:

```JSON
{
  "gen_aime_1": {
    "problem_id": "gen_aime_1",
    "баллы": {
      «правильность»: 5,
      «ясность»: 4,
      «difficulty_match»: 4,
      "полнота": 5
    },
    "total_score": 4,5,
    "статус": "одобрено",
    "comments": "Качество задачи очень хорошее, логика строгая",
    "verified_at": "2025-01-10T12:00:00"
  }
}
```

### 12.4.7 Complete Evaluation Flow

Integrate all evaluation methods into a complete flow.

```питон
защита run_complete_evaluation(
    число_проблем: int = 30,
    задержка_секунды: с плавающей запятой = 3,0
):
    """
    Запустите полный процесс оценки

Аргументы:
        num_problems: Количество проблем, которые нужно сгенерировать.
        задержание_секунд: задержка между каждым поколением (в секундах), избегайте ограничения скорости API.
    """
    # Шаг 1: Создайте проблемы AIME
    генератор = AIMEGenerator(delay_секунды=delay_секунды)
    сгенерированный_путь_данных = генератор.генерировать_и_сохранить(
        num_problems=num_problems,
        output_dir="генерация_данных/сгенерированные_данные"
    )

# Шаг 2: Оценка
    # Создать каталог результатов оценки
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Assessment_dir = f"data_generation/evaluation_results/{timestamp}"
    os.madeirs(evaluation_dir, Exist_ok=True)
    os.madeirs(os.path.join(evaluation_dir, "llm_judge"), Exist_ok=True)
    os.madeirs(os.path.join(evaluation_dir, "win_rate"), Exist_ok=True)

# Создать LLM
    llm = ПриветАгентыLLM()

# Шаг 2.1: Оценка судьи LLM
    llm_judge_result = Нет
    попробуйте:
        llm_judge_tool = LLMJudgeTool(llm=llm)
        llm_judge_result_json = llm_judge_tool.run({
            «сгенерированный_путь_данных»: сгенерированный_путь_данных,
            «reference_year»: 2025,
            "max_samples": num_problems,
            «output_dir»: os.path.join(evaluation_dir, «llm_judge»),
            "judge_model": "gpt-4o"
        })
        llm_judge_result = json.loads(llm_judge_result_json)
    кроме исключения как e:
        print(f"❌ Оценка судьи LLM не удалась: {e}")

# Шаг 2.2: Оценка процента побед
    win_rate_result = Нет
    попробуйте:
        win_rate_tool = WinRateTool(llm=llm)
        win_rate_result_json = win_rate_tool.run({
            «сгенерированный_путь_данных»: сгенерированный_путь_данных,
            «reference_year»: 2025,
            "количество_сравнений": мин(количество_проблем, 20),
            «output_dir»: os.path.join(evaluation_dir, «win_rate»),
            "judge_model": "gpt-4o"
        })
        win_rate_result = json.loads(win_rate_result_json)
    кроме исключения как e:
        print(f"❌ Не удалось оценить процент побед: {e}")

# Шаг 3: Создайте подробный отчет
    complex_report_path = Нет
    если llm_judge_result или win_rate_result:
        комплексный_репорт_путь = os.path.join(evaluation_dir, "comprehensive_report.md")
        отчет =generate_comprehensive_report(
            сгенерированный_путь_данных,
            llm_judge_result,
            win_rate_result
        )
        с open(comprehensive_report_path, 'w',coding='utf-8') как f:
            f.write(отчет)

вернуть {
        «сгенерированный_путь_данных»: сгенерированный_путь_данных,
        "llm_judge_result": llm_judge_result,
        "win_rate_result": win_rate_result,
        "comprehensive_report_path": всеобъемлющий_report_path
    }
```

**Run Method**:

```бить
# Базовое использование (задержка по умолчанию 3 секунды)
python data_generation/run_complete_evaluation.py 30

# Пользовательская задержка (рекомендуется 3-5 секунд, избегайте ограничения скорости API)
python data_generation/run_complete_evaluation.py 30 3.0

# Объяснение параметра:
# - 30: Количество проблем, которые нужно создать
# - 3.0: Задержка между каждым поколением (секунды)

# Объяснение:
# - Фаза генерации: случайным образом выберите эталонные примеры из более чем 900 реальных задач AIME (1983-2025 гг.).
# - Этап оценки: сравнение качества с реальными проблемами AIME 2025.
# - Источник набора данных: math-ai/aime25 (формат JSONL)
```

**Output Example**:

```
============================================================================
🚀 Полный процесс создания и оценки данных AIME
============================================================================

Конфигурация:
  - Количество проблем, которые нужно создать: 30
  - Задержка API: 3,0 секунды/проблема
  - Справочные данные поколения: TianHongZXY/aime-1983-2025 (более 900 проблем)
  - Ссылка на оценку: реальные проблемы AIME 2025.

============================================================================
📝 Шаг 1: Создайте проблемы AIME
============================================================================
📚 Загрузите набор данных о реальных проблемах AIME: TianHongZXY/aime-1983-2025.
   ✓ Загружено 963 справочных задачи

🎯 Начните создавать проблемы AIME
   Целевое количество: 30
   Модель поколения: gpt-4o
   Настройка задержки: 3,0 секунды/проблема.

Создание проблем с AIME: 100%|██████████| 30/30 [01:30<00:00, 3,00 с/задача, тема=Алгебра, ответ=123, время=3,0 с]

✅Шаг 1 выполнен! Сгенерированные данные сохраняются по адресу: data_generated/generated_data/aime_generated_20250110_120000.json.

🎯 Шаг 2.1: Оценка судьи LLM (по сравнению с AIME 2025)

✅ Оценка судьи LLM завершена!
   Средний общий балл: 4,2/5,0
   Процент прохождения: 85,0%

🏆 Шаг 2.2: Оценка процента побед (по сравнению с AIME 2025)

✅ Оценка выигрыша завершена!
   Вероятность выигрыша: 45,0%

============================================================================
📊 Шаг 3: Создайте подробный отчет
============================================================================

✅ Комплексный отчет сохранен: data_generation/evaluation_results/20250110_120000/comprehensive_report.md

============================================================================
🎉 Полный процесс оценки завершен!
============================================================================

📁 Выходные файлы:
   - Сгенерированные данные: data_generated/generated_data/aime_generated_20250110_120000.json.
   - Каталог результатов оценки: data_generation/evaluation_results/20250110_120000.
   - Отчет судьи LLM: data_generation/evaluation_results/20250110_120000/llm_judge/llm_judge_report_20250110_120000.md
   - Отчет о проценте побед: data_generation/evaluation_results/20250110_120000/win_rate/win_rate_report_20250110_120000.md
   - Комплексный отчет: data_generation/evaluation_results/20250110_120000/comprehensive_report.md

💡 Следующие шаги:
   1. Просмотрите подробный отчет: data_generation/evaluation_results/20250110_120000/comprehensive_report.md.
   2. Запустите проверку вручную: python data_generation/human_verification_ui.py data_generation/generated_data/aime_generated_20250110_120000.json
```

### 12.4.8 Comprehensive Evaluation Report

The system automatically generates comprehensive evaluation reports, summarizing all evaluation results. Below is an example report:

```уценка
# Комплексный отчет AIME по созданию и оценке данных

## 1. Основная информация

- **Время генерации**: 10 января 2025 г., 12:00:00.
- **Количество созданных проблем**: 30
- **Справочный год AIME**: 2025 г.

## 2. Статистика формирования данных

### Распределение тем

| Тема | Количество | Пропорция |
|------|------|------|
| Алгебра | 10 | 33,3% |
| Геометрия | 8 | 26,7% |
| Теория чисел | 7 | 23,3% |
| Комбинаторика | 3 | 10,0% |
| Вероятность | 2 | 6,7% |

## 3. Результаты оценки судей LLM

### Общий балл

- **Средний общий балл**: 4,2/5,0
- **Процент сдачи**: 85,0% (≥3,5 баллов)
- **Отличный рейтинг**: 40,0% (≥4,5 баллов)

### Оценки измерений

| Размерность | Средний балл | Рейтинг |
|------|--------|------|
| Корректность | 4,3/5,0 | Хорошо ⭐⭐⭐⭐ |
| Ясность | 4,1/5,0 | Хорошо ⭐⭐⭐⭐ |
| Матч сложности | 4.0/5.0 | Хорошо ⭐⭐⭐⭐ |
| Полнота | 4,4/5,0 | Хорошо ⭐⭐⭐⭐ |

## 4. Результаты оценки процента выигрышей

### Статистика выигрышей

| Метрическая | Значение | Процент |
|------|------|--------|
| Сгенерированные данные выигрывают | 9 раз | 45,0% |
| Победа AIME «Реальные проблемы» | 8 раз | 40,0% |
| Галстук | 3 раза | 15,0% |

**Процент побед**: 45,0%

✅ **Хорошо**: качество полученных данных близко к эталонным (разрыв <10%).

## 5. Комплексное заключение

По результатам оценки LLM Judge и WinRate:

1. **Оценка судьи LLM**: Среднее качество сгенерированных данных — **4,2/5,0**.
2. **Оценка процента побед**: Процент выигрышей сгенерированных данных относительно реальных проблем AIME 2025 составляет **45,0%**

✅ **Вывод**: Качество сгенерированных данных **отличное**, достигая или превосходя реальный уровень проблемы AIME. Может использоваться для практических целей.

## 6. Предложения по улучшению

- ✅ Продолжать поддерживать текущую стратегию генерации
- ✅ Можно рассмотреть возможность увеличения количества генерации
- ✅ Рекомендую ручную проверку для обеспечения качества

## 7. Следующие шаги

1. **Проверка вручную**: Запустите`python data_generation/human_verification_ui.py <data_path>`для ручной проверки
2. **Просмотреть подробные результаты**:
   - Подробный отчет судьи LLM
   - Подробный отчет о проценте побед
3. **Использование данных**: если качество удовлетворительное, сгенерированные данные можно использовать для обучения или тестирования.
```

Основываясь на практическом опыте использования, суммируйте следующее содержание:

При создании данных используйте подходящее время задержки (2–3 секунды), чтобы избежать ограничений скорости API, включите сохранение контрольных точек, чтобы избежать потерь из-за прерываний, сначала тестируйте небольшими пакетами (10), чтобы подтвердить отсутствие проблем перед крупномасштабной генерацией, и регулярно проверяйте качество генерации, чтобы вовремя корректировать подсказки. В стратегии оценки рекомендуется сочетать методы LLM Judge и Winrate, где LLM Judge используется для абсолютной оценки качества, Winrate для сравнения относительного качества и ручная проверка для окончательного контроля качества. В отношении стандартов качества рекомендуется средний балл судьи LLM выше 4,0/5,0, процент побед выше 45 % (близко к 50 %), процент успешных попыток выше 80 % и процент успешных проверок вручную выше 90 %. При итеративной оптимизации корректируйте подсказки для генерации на основе результатов оценки, анализируйте общие проблемы в задачах с низкой оценкой, ссылайтесь на преимущества задач с высокой оценкой и постоянно совершенствуйте стратегию генерации.

Изучив этот раздел, мы научились использовать платформу HelloAgents для оценки качества генерации данных, включая три метода: оценку LLM Judge, оценку процента побед и ручную проверку. Эта комплексная система оценки может гарантировать высокое качество генерируемых данных, обеспечивая надежную поддержку данных для обучения и тестирования систем искусственного интеллекта.

Для оценки LLM Judge и Win Rank HelloAgents также интегрировал инструменты и предоставил полный пример кода. Если вас интересуют конкретные детали реализации этих двух методов оценки, вы также можете обратиться к примеру кода.

## 12.5 Краткое содержание главы

В этой главе мы создали полную систему оценки производительности для платформы HelloAgents. Давайте рассмотрим основной изученный материал:

**(1) Обзор системы оценки**

Мы создали трехуровневую систему оценки, всесторонне охватывающую различные аспекты возможностей агентов. Во-первых, это оценка возможностей вызова инструментов (BFCL), в которой основное внимание уделяется оценке точности вызова функций агента, включая четыре категории простых, множественных, параллельных и нерелевантных, с использованием технологии сопоставления AST для точной оценки. Во-вторых, это общая оценка возможностей (GAIA), оценивающая возможности агента по комплексному решению проблем, включая три уровня сложности с 466 реальными проблемами, с упором на многоэтапное рассуждение, использование инструментов, обработку файлов и другие возможности. В-третьих, это оценка качества генерации данных (AIME), оценка качества данных, генерируемых LLM, с использованием методов LLM Judge и Win Rank, поддержка ручной проверки и создание комплексных отчетов, обеспечивающая соответствие сгенерированных данных эталонным стандартам качества данных.

**(2) Основные технические моменты**

В технической реализации мы приняли шесть основных технических моментов. Во-первых, это модульная конструкция, система оценки имеет трехуровневую архитектуру: уровень данных (набор данных, отвечающий за загрузку данных и управление ими), уровень оценки (оценщик, отвечающий за выполнение потока оценки) и уровень метрик (метрики, отвечающие за расчет различных метрик оценки). Во-вторых, это инкапсуляция инструментов: все функции оценки инкапсулируются как инструменты, могут напрямую вызываться агентами, интегрироваться в рабочие процессы или использоваться через унифицированный интерфейс. В-третьих, это технология сопоставления AST, использующая сопоставление абстрактного синтаксического дерева для вызовов функций, более интеллектуальная, чем простое сопоставление строк, способная игнорировать порядок параметров, распознавать эквивалентные выражения и игнорировать различия в формате. В-четвертых, это мультимодальная поддержка: оценка GAIA поддерживает текстовые вопросы, вложенные файлы, входные изображения и другие мультимодальные данные. В-пятых, это оценка LLM Judge, использующая LLM в качестве судьи для оценки качества сгенерированных данных, обеспечивающая многомерную оценку (правильность, ясность, соответствие сложности, полнота), автоматизированный процесс оценки, подробные отчеты об оценке и поддержку пользовательских параметров и стандартов оценки. В-шестых, это оценка сравнения выигрышей, оценивающая качество генерации посредством парного сравнения (сгенерированные данные и справочные данные), LLM определяет, что лучше, и рассчитывает статистику выигрышей, близкое к 50% указывает на эквивалентное качество.

**(3) Инструкции по продлению**

Основываясь на системе оценки, описанной в этой главе, вы можете развиваться в четырех направлениях. Во-первых, это добавление новых тестов оценки, возможность ссылаться на шаблоны реализации BFCL и GAIA, реализация трех компонентов Dataset, Evaluator, Metrics и инкапсуляция в качестве инструмента для использования. Во-вторых, это пользовательские метрики оценки, добавление новых методов расчета метрик в класс Metrics, разработка метрик в соответствии с конкретными сценариями приложений. В-третьих, это интеграция в поток CI/CD, автоматический запуск оценки при фиксации кода, установка пороговых значений производительности для предотвращения снижения производительности, создание отчетов об оценке и их архивирование. В-четвертых, это расширение оценки генерации данных, поддержка большего количества типов данных (код, диалог, документы и т. д.), добавление большего количества измерений оценки (инновации, разнообразие и т. д.), интеграция большего количества справочных наборов данных, поддержка оценки сравнения нескольких моделей.

**Поздравляем с завершением главы 12!** 🎉

Оценка — важная часть разработки агента, она позволяет нам:

- Объективно измеряйте возможности агента
- Обнаруживайте и устраняйте проблемы
- Постоянно совершенствовать системы

В следующей главе мы рассмотрим, как применить платформу HelloAgents к реальным проектам.

**Продолжайте!** 💪

## Упражнения

> **Подсказка**: некоторые упражнения не имеют стандартных ответов и направлены на развитие у учащихся всестороннего понимания и практических навыков в оценке эффективности работы агентов.

1. В этой главе представлены несколько критериев оценки агентов. Пожалуйста, проанализируйте:

   - В разделе 12.1.2 были представлены BFCL, GAIA, AgentBench и другие тесты оценки. Пожалуйста, сравните BFCL и GAIA: какие основные возможности агентов они оценивают соответственно? Почему BFCL использует алгоритм сопоставления AST, а GAIA использует Quasi Exact Match? Каковы преимущества и недостатки этих двух методов оценки?
   - Предположим, вы хотите построить «интеллектуальную систему обслуживания клиентов», которой необходимо оценить следующие возможности: (1) точность понимания намерений пользователя; (2) корректность вызова серверных API; (3) дружелюбие и профессионализм ответов; (4) устойчивость в исключительных ситуациях. Пожалуйста, выберите или разработайте соответствующие показатели и методы оценки для каждой возможности.
   - В разделе 12.1.1 было упомянуто, что оценка агентов сталкивается с тремя основными проблемами: «неопределенность результатов», «разнообразие стандартов оценки» и «высокая стоимость оценки». Пожалуйста, предложите конкретные решения для каждой проблемы и проанализируйте осуществимость и ограничения решений.

2. BFCL (Berkeley Function Calling Leaderboard) — важный ориентир для оценки возможностей вызова инструментов. Основываясь на содержании раздела 12.2, пожалуйста, глубоко подумайте:

> **Подсказка**: это практический вопрос, рекомендуется реальная работа.

   - В алгоритме сопоставления AST, описанном в разделе 12.2.3, мы оцениваем корректность вызовов функций путем сравнения абстрактных синтаксических деревьев. Пожалуйста, проанализируйте: почему сопоставление AST более подходит, чем простое сопоставление строк? В каких ситуациях сопоставление AST может привести к ошибочным оценкам (ложноположительные или ложноотрицательные результаты)? Как улучшить алгоритм сопоставления AST, чтобы повысить точность?
   - Набор данных BFCL содержит четыре категории: простые, множественные, параллельные и нерелевантные. Разработайте 2–3 новых тестовых образца для каждой категории, требующих возможности тестировать граничные случаи или сценарии, подверженные ошибкам, в этой категории.
   - Пожалуйста, расширьте оценщик BFCL на основе кода из раздела 12.2.4, добавив следующие функции: (1) поддержка оценки порядка выполнения вызовов инструментов (для нескольких вызовов инструментов с зависимостями); (2) оценить эффективность вызова инструментов (например, использовалось ли минимальное количество вызовов); (3) создать подробный отчет об анализе ошибок (например, какие типы ошибок наиболее распространены).

3. GAIA (General AI Assistants) оценивает комплексные возможности агента. В соответствии с содержанием раздела 12.3 выполните следующую практику расширения:

> **Подсказка**: это практический вопрос, рекомендуется реальная работа.

   - В разделе 12.3.2 были введены три уровня сложности GAIA (уровень 1/2/3). Пожалуйста, проанализируйте: каковы различия между этими тремя уровнями по сложности задач, требуемым возможностям, стандартам оценки и т. д.? Если разрабатывается уровень 4 (сверхвысокая сложность), какие типы задач он должен включать?
   - GAIA использует алгоритм «Квазиточное совпадение» для оценки правильности ответов. Пожалуйста, проанализируйте: как этот метод обрабатывает разнообразие ответов (например, «42», «сорок два», «42,0» следует считать правильными)? В каких ситуациях квазиточное совпадение может оказаться недостаточным? Пожалуйста, разработайте более интеллектуальный алгоритм сопоставления ответов, который сможет обрабатывать семантически эквивалентные ответы.
   - Пожалуйста, внедрите «пользовательский набор оценок GAIA» на основе кода из раздела 12.3.4: выберите конкретную область (например, медицинскую, юридическую, финансовую), разработайте 10 реальных вопросов и реализуйте полный поток оценки. Требуйте, чтобы вопросы охватывали различные уровни сложности, а также предоставляли стандартные ответы и критерии оценки.

4. LLM Judge — это новый метод использования больших языковых моделей для оценки. Основываясь на содержании раздела 12.4, пожалуйста, подробно проанализируйте:

   - В разделе 12.4.2 мы использовали GPT-4 в качестве критерия для оценки качества ответа агента. Пожалуйста, проанализируйте: какие преимущества имеет LLM Judge по сравнению с традиционным сопоставлением правил или расчетом показателей? Какие потенциальные предубеждения или ограничения у него есть (например, предпочтение определенных стилей ответов, чувствительность к длине)?
   - Разработка критериев оценки судей LLM имеет решающее значение. Разработайте подробные критерии оценки (включая параметры оценки, веса, примеры) для следующих трех различных сценариев оценки: (1) оценка качества генерации кода; (2) оценка качества творческого письма; (3) оценка качества технической документации.
   - В разделе 12.4.3 было упомянуто, что для оценки «в стиле жюри» можно использовать несколько судей LLM. Пожалуйста, разработайте «систему оценки с участием нескольких судей»: используя 3-5 разных LLM (таких как GPT-4, Claude, Qwen) в качестве судей, как суммировать их баллы? Как разрешать разногласия между судьями? Как обнаружить и отфильтровать ненормальные оценки?

5. Практическое применение оценки агентов должно учитывать множество аспектов. Пожалуйста, подумайте:

   - В реальных проектах оценка часто требует баланса между «стоимостью оценки» и «качеством оценки». Пожалуйста, разработайте «стратегию многоуровневой оценки»: (1) быстрая оценка (низкая стоимость, для ежедневной итерации разработки); (2) стандартная оценка (средняя стоимость, для предварительной версии); (3) комплексная оценка (высокая стоимость крупных обновлений или публичного выпуска). Какие элементы оценки должен включать каждый уровень? Как спроектировать поток оценки?
   - Производительность агента может меняться со временем (например, изменения в зависимых внешних API, изменения в потребностях пользователей). Пожалуйста, разработайте «систему непрерывной оценки»: способную периодически автоматически запускать оценку, отслеживать тенденции изменения производительности агентов и вовремя предупреждать, когда производительность снижается. Какие компоненты должна включать в себя эта система? Как разработать правила оповещений?
   - Результаты оценки должны быть четко представлены различным аудиториям (например, разработчикам, менеджерам по продуктам, пользователям). Пожалуйста, разработайте «систему создания отчетов об оценке»: способную автоматически генерировать отчеты с разным уровнем детализации в зависимости от типа аудитории. Какие технические подробности должны включать отчеты разработчиков? Какие бизнес-показатели должны освещаться в отчетах менеджера по продукту? Как следует упростить и визуализировать пользовательские отчеты?

## Ссылки

[1] Патил С.Г., Чжан Т., Ван Х. и Гонсалес Дж. Э. (2023). Gorilla: большая языковая модель, связанная с массивными API. Препринт arXiv arXiv:2305.15334.

[2] Цинь Ю., Лян С., Е Ю., Чжу К., Ян Л., Лу Ю., ... и Сунь М. (2023). ToolLLM: использование больших языковых моделей для освоения более 16 000 реальных API. Препринт arXiv arXiv:2307.16789.

[3] Ли, М., Чжао, Ю., Ю, Б., Сун, Ф., Ли, Х., Ю, Х., ... и Ли, Ю. (2023). Api-bank: Комплексный тест для фильмов с инструментальными дополнениями. Препринт arXiv arXiv:2304.08244.

[4] Миалон Г., Десси Р., Ломели М., Налмпантис К., Пасунуру Р., Раиляну Р., ... и Сиалом Т. (2023). GAIA: эталон для помощников общего назначения по искусственному интеллекту. Препринт arXiv arXiv:2311.12983.

[5] Лю, X., Ю, Х., Чжан, Х., Сюй, Ю., Лэй, X., Лай, Х., ... и Чжан, Д. (2023). AgentBench: Оценка LLM как агентов. Препринт arXiv arXiv:2308.03688.

[6] Чжоу С., Сюй Ф.Ф., Чжу Х., Чжоу Х., Ло Р., Шридхар А., ... и Нойбиг Г. (2023). WebArena: реалистичная веб-среда для создания автономных агентов. Препринт arXiv arXiv:2307.13854.

[7] Чан, К.М., Чен, В., Су, Ю., Ю, Дж., Сюэ, В., Чжан, С., ... и Лю, З. (2023). ChatEval: К лучшим оценщикам на основе LLM посредством многоагентных дебатов. Препринт arXiv arXiv:2308.07201.

[8] Чжоу, Х., Чжу, Х., Матур, Л., Чжан, Р., Ю, Х., Ци, З., ... и Нойбиг, Г. (2023). SOTOPIA: Интерактивная оценка социального интеллекта языковых агентов. Препринт arXiv arXiv:2310.11667.

[9] Математическая ассоциация Америки. (2024). Американский пригласительный экзамен по математике (AIME). Получено изhttps://www.maa.org/math-competitions/invitational-competitions/aime

