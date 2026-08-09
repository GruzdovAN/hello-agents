# Глава 14. Агент автоматизированного глубокого исследования

В проекте помощника по поездкам в главе 13 мы узнали, как применить HelloAgents к мультиагентному продукту. В этой главе мы продолжим двигаться вперед, сосредоточив внимание на **наукоемких приложениях**: **создании помощника агента, который может автоматически выполнять глубокие исследовательские задачи.**

По сравнению с планированием путешествий сложность глубоких исследований заключается в постоянном расхождении информации, быстром обновлении фактов и высоких требованиях пользователей к источникам цитирования. Чтобы предоставлять достоверные исследовательские отчеты, нам необходимо снабдить агентов тремя основными возможностями:

**(1) Анализ проблем**: разложите открытые темы пользователей на извлекаемые операторы запроса.

**(2) Многораундовый сбор информации**. Постоянно анализируйте материалы, комбинируя различные поисковые API, а также дедупликатируйте и интегрируйте их.

**(3) Размышление и обобщение**: выявите пробелы в знаниях на основе результатов этапов, решите, продолжать ли поиск, и создайте структурированные резюме.

## 14.1 Обзор проекта и архитектурный дизайн

### 14.1.1 Почему нам нужен ассистент по глубоким исследованиям

В эпоху информационного взрыва нам необходимо каждый день быстро разбираться в новых технологиях, концепциях или событиях. Традиционные методы исследования имеют несколько болевых точек. Во-первых, это **информационная перегрузка**. Поисковые системы выдают тысячи результатов, и вам нужно переходить по ссылкам одну за другой и читать много контента, чтобы найти полезную информацию. Во-вторых, это **отсутствие структуры**. Даже если вы найдете соответствующую информацию, эта информация часто фрагментирована и не имеет систематической организации. Наконец, это **повторяющийся труд**. Каждый раз, когда вы исследуете новую тему, вам необходимо повторять процесс «поиск → чтение → обобщение → систематизация».

Это проблема, которую должен решить научный сотрудник. Это не просто инструмент поиска, а помощник исследователя, который может автономно планировать, выполнять и обобщать.

**Основная ценность помощника по глубоким исследованиям:**

1. **Экономьте время**: сократите 1–2 часа исследовательской работы до 5–10 минут.
2. **Повышение качества**: систематический исследовательский процесс, позволяющий не пропустить важную информацию.
3. **Отслеживаемость**: записывайте все результаты поиска и источники для облегчения проверки и цитирования.
4. **Расширяемость**: легко добавляйте новые поисковые системы, источники данных и инструменты анализа.

### 14.1.2 Обзор технической архитектуры

В этой системе по-прежнему используется классическая **архитектура разделения клиентской и серверной частей**, как показано на рис. 14.1.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-1.png" alt="" width="85%"/>
  <p>Рисунок 14.1 Техническая архитектура Deep Research Assistant</p>
</div>

Система спроектирована с четырехуровневой архитектурой:

**Внешний уровень (Vue3+TypeScript)**: полноэкранный модальный диалоговый интерфейс, визуализация результатов Markdown.

**Верхний уровень (FastAPI)**: маршрутизация API (`/research/stream`)

**Уровень агентов (HelloAgents)**: три специализированных агента (TODO Planner, Task Summarizer, Report Writer) + два основных инструмента (SearchTool, NoteTool).

**Уровень внешнего обслуживания**: поисковые системы + поставщики LLM.

Давайте посмотрим, как полный запрос на исследование проходит через систему, как показано на рисунке 14.2:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-2.png" alt="" width="85%"/>
  <p>Рисунок 14.2. Процесс потока данных Deep Research Assistant</p>
</div>

1. **Ввод пользователя**: пользователь вводит тему исследования во внешнем интерфейсе.
2. **Внешняя отправка**: внешний интерфейс подключается к `/research/stream` через SSE.
3. **Верхний сервер получает**: FastAPI получает запрос и создает состояние исследования.
4. **Фаза планирования**: вызывает агента по планированию исследований, разбивается на 3 подзадачи.
5. **Фаза выполнения**: каждая подзадача выполняется одна за другой.
   - Используйте SearchTool для поиска
   - Вызов агента суммирования задач для подведения итогов
   - Используйте NoteTool для записи результатов
6. **Этап отчета**: вызов агента по созданию отчетов, объединение всех сводок.
7. **Возврат в поток**: перенос прогресса и результатов на внешний интерфейс через SSE.
8. **Внешний интерфейс**: внешний интерфейс обновляет статус задачи, индикатор выполнения, журналы и отчеты в режиме реального времени.

Структура каталогов проекта следующая:

```
helloagents-deepresearch/
├── backend/                    # Back-end code
│   ├── src/
│   │   ├── agent.py           # Core coordinator
│   │   ├── main.py            # FastAPI entry
│   │   ├── models.py          # Data models
│   │   ├── prompts.py         # Prompt templates
│   │   ├── config.py          # Configuration management
│   │   └── services/          # Service layer
│   │       ├── planner.py     # Planning service
│   │       ├── summarizer.py  # Summarization service
│   │       ├── reporter.py    # Report service
│   │       └── search.py      # Search service
│   ├── .env                   # Environment variables
│   ├── pyproject.toml         # Dependency management
│   └── workspace/             # Research notes
│
└── frontend/                   # Front-end code
    ├── src/
    │   ├── App.vue            # Main component
    │   ├── components/        # UI components
    │   │   └── ResearchModal.vue
    │   └── composables/       # Composable functions
    │       └── useResearch.ts
    ├── package.json           # npm dependencies
    └── vite.config.ts         # Build configuration
```

### 14.1.3 Быстрый опыт: запуск проекта за 5 минут

Прежде чем углубляться в детали реализации, давайте сначала запустим проект, чтобы увидеть конечный результат. Таким образом, вы получите интуитивное понимание всей системы.

Проверить версии можно следующими командами:

```bash
python --version  # Should show Python 3.10.x or higher
node --version    # Should show v16.x.x or higher
npm --version     # Should show 8.x.x or higher
```

**(1) Запустите серверную часть**

```bash
# 1. Enter back-end directory
cd helloagents-deepresearch/backend

# 2. Install dependencies
# Method 1: Using uv (recommended, faster Python package manager)
uv sync

# Method 2: Using pip
pip install -e .

# 3. Configure environment variables
cp .env.example .env

# 4. Edit .env file, fill in your API keys
# Open .env file with your favorite editor
# At minimum, configure:
# - LLM_PROVIDER (e.g., openai, deepseek, qwen)
# - LLM_API_KEY (your LLM API key)
# - SEARCH_API (e.g., duckduckgo, tavily)

# 5. Start back-end
python src/main.py
```

Если все в порядке, вы увидите вывод, похожий на:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**(2) Запустите интерфейс**

Откройте новое окно терминала:

```bash
# 1. Enter front-end directory
cd helloagents-deepresearch/frontend

# 2. Install dependencies
npm install

# 3. Start front-end
npm run dev
```

Если все в порядке, вы увидите вывод, похожий на:

```
  VITE v5.0.0  ready in 500 ms

  ➜  Local:   http://localhost:5174/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**(3) Начать исследование**

Откройте браузер и посетите`http://localhost:5174`. Вы увидите центрированную карту ввода, как показано на рис. 14.3. Введите тему исследования, например`What kind of organization is Datawhale?`, выберите поисковую систему (если настроено несколько) и нажмите кнопку «Начать исследование».

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-3.png" alt="" width="85%"/>
  <p>Рисунок 14.3 Страница поиска Deep Research Assistant</p>
</div>

Как показано на рисунке 14.4, система автоматически развернется в полноэкранный режим, при этом информация об исследовании будет отображаться слева, а ход исследования и результаты будут отображаться в режиме реального времени справа. Весь процесс исследования занимает около 1-3 минут, в зависимости от сложности темы и скорости ответа поисковой системы.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-4.png" alt="" width="85%"/>
  <p>Рис. 14.4 Deep Research Assistant Expanded Research</p>
</div>

После завершения исследования вы увидите:

- **Список задач**: отображаются все подзадачи и их статус.
- **Журнал прогресса**: показывает все операции в процессе исследования.
- **Итоговый отчет**: структурированный отчет Markdown, содержащий сводку всех подзадач и ссылки на источники.

Теперь вы успешно запустили помощника по глубоким исследованиям и имеете интуитивное понимание системы.

## 14.2 Парадигма исследования, основанного на TODO

### 14.2.1 Что такое исследование, управляемое TODO

Традиционные поисковые системы могут ответить только на отдельные вопросы, тогда как глубокие исследования должны ответить на ряд связанных вопросов. Парадигма исследования, основанная на TODO, разбивает сложные темы исследования на несколько подзадач (TODO), выполняет их одну за другой и интегрирует результаты.

Основная идея этой парадигмы: **Преобразовать сложную задачу «исследования» в процесс «планирование → выполнение → интеграция»**.

Давайте разберемся в этой трансформации на примере. Предположим, вы хотите изучить вопрос «Что за организация представляет собой Datawhale?». Традиционный метод поиска:

```
User input: What kind of organization is Datawhale?
Search engine: Returns 10-20 links
User: Click on links one by one, read content, take notes
Result: Fragmented information, lacking systematization
```

Проблема этого подхода заключается в том, что каждая ссылка охватывает только один аспект темы, не имеет систематической структуры и требует ручной организации и обобщения.

**Подход, основанный на TODO: систематические исследования**

```
User input: What kind of organization is Datawhale?

System planning:
  ├─ TODO 1: Basic information about Datawhale (organizational positioning)
  ├─ TODO 2: Main projects of Datawhale (core content)
  ├─ TODO 3: Community culture of Datawhale (values)
  └─ TODO 4: Influence of Datawhale (social contribution)

System execution:
  For each TODO:
    1. Search for relevant materials
    2. Summarize key information
    3. Record source citations

System integration:
  Generate structured report:
    ├─ Part 1: Organizational positioning (from TODO 1)
    ├─ Part 2: Core content (from TODO 2)
    ├─ Part 3: Values (from TODO 3)
    ├─ Part 4: Social contribution (from TODO 4)
    └─ References: All source citations
```

Преимущества этого подхода заключаются в том, что он разбивает сложные темы на четкие подвопросы, записывает результаты поиска и резюме для каждой подзадачи для облегчения отслеживания, а систематический процесс исследования позволяет избежать пропуска важной информации. Также легко добавлять новые подзадачи или регулировать порядок выполнения.

Полная исследовательская система, основанная на TODO, содержит три основных элемента:

**(1) Интеллектуальный планировщик (TODO Planner)**: отвечает за разложение тем исследования на подзадачи. Хорошему планировщику необходимо понимать ключевые аспекты и цели исследования темы, разложить тему на 3-5 подзадач (слишком мало не окроет все, слишком много будет избыточно) и разработать подходящие поисковые запросы для каждой подзадачи.

**(2) Исполнитель задач**: отвечает за выполнение каждой подзадачи. Исполнителю необходимо использовать поисковые системы для получения актуальных материалов, извлечения ключевой информации и удаления лишнего контента, сохраняя при этом все цитаты на источники для удобства проверки.

**(3) Составитель отчетов**: отвечает за интеграцию результатов всех подзадач. Генератору необходимо организовать контент в логическом порядке, объединить повторяющуюся информацию и добавить ссылки на источники для каждой точки зрения.

В нашем случае процесс исследования, основанный на TODO, показан на рисунке 14.5:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-5.png" alt="" width="85%"/>
  <p>Рисунок 14.5. Процесс исследования, основанный на TODO</p>
</div>

Весь процесс линейный, но каждый этап имеет четкие входы и выходы. Такая конструкция упрощает понимание и отладку системы.

### 14.2.2 Трехэтапный процесс исследования

Процесс исследования, основанный на TODO, разделен на три этапа: планирование, выполнение и отчетность. За каждый этап отвечает специальный агент.

**(1) Этап 1: Планирование**

Цель этапа планирования – декомпозиция темы исследования на 3-5 подзадач. Система получает на вход тему исследования и текущую дату и выводит список подзадач в формате JSON. Каждая подзадача содержит три поля: title (название задачи), Intent (намерение исследования) и query (поисковый запрос).

Агент по планированию исследований применяет различные стратегии декомпозиции на основе характеристик темы, обычно начиная с базовых концепций, затем понимания технического состояния, практического применения и тенденций развития, а также проведения сравнительного анализа, когда это необходимо. Например, для вопроса «Какая организация представляет собой Datawhale?» агент планирования может сгенерировать следующие подзадачи:

```json
[
  {
    "title": "Basic information about Datawhale",
    "intent": "Understand Datawhale's organizational positioning, founding time, development history",
    "query": "Datawhale organization introduction history 2024"
  },
  {
    "title": "Main projects of Datawhale",
    "intent": "Understand Datawhale's core open source projects and tutorials",
    "query": "Datawhale projects tutorials open source 2024"
  },
  ...
]
```

Хороший план должен быть всеобъемлющим, логически ясным, содержать точные запросы и соответствующее количество пунктов.

**(2) Этап 2: Исполнение**

На этапе исполнения каждая подзадача выполняется поочередно, осуществляя поиск и обобщение соответствующих материалов. Система получает на входе список подзадач и конфигурацию поисковой системы и выводит сводку (формат Markdown) и список цитирования источников для каждой подзадачи. Процесс выполнения следующий:

По каждой подзадаче исполнитель:

1. **Поиск материалов**: используйте настроенную поисковую систему для выполнения поиска.

   ```python
   search_results = search_tool.run({
       "input": task.query,
       "backend": "tavily",
       "mode": "structured",
       "max_results": 5
   })
   ```

2. **Получите результаты поиска**: извлеките заголовок, URL-адрес и фрагмент.

   ```json
   {
     "results": [
       {
         "title": "What is a Multimodal Model?",
         "url": "https://example.com/multimodal-model",
         "snippet": "A multimodal model is an AI model that can process multiple types of data..."
       },
       ...
     ]
   }
   ```

3. **Агент суммирования вызовов**: суммируйте результаты поиска.

   ```python
   summary = summarizer_agent.run(
       task=task,
       search_results=search_results
   )
   ```

4. **Сводка записи и источники**: Сохранить в NoteTool.

   ```python
   note_tool.run({
       "action": "create",
       "title": task.title,
       "content": f"## {task.title}\n\n{summary}\n\n## Sources\n{sources}",
       "tags": ["research", "summary"]
   })
   ```

Агент суммирования задач будет извлекать основные точки зрения из каждого результата поиска, объединять аналогичную информацию, сохранять важные цифры, даты, имена и другие ключевые данные, а также добавлять ссылки на источники для каждой точки зрения. Например, для результатов поиска «Основная информация о Datawhale» агент суммирования может сгенерировать:

```markdown
## Basic Information about Datawhale

Datawhale is an open source organization focused on data science and AI, founded in 2018[1]. The organization's core mission is "for the learner, grow together with learners", committed to building a pure learning community[2].

**Core Positioning:**

1. **Open Source Education Platform**: Provides high-quality AI and data science learning resources[1]
2. **Learner Community**: Gathers tens of thousands of AI learners and practitioners[3]
3. **Knowledge Sharing**: Advocates open source spirit, all content is completely free and open[2]

**Development History:**

- **2018**: Datawhale was founded, released first open source tutorial[1]
- **2020**: Became one of the leading AI learning communities in China[3]
- **2024**: Released 50+ open source projects, impacting 100,000+ learners[4]

## Sources

[1] https://github.com/datawhalechina
[2] https://datawhale.club/about
[3] https://www.zhihu.com/org/datawhale
[4] https://datawhale.cn
```

Во время выполнения система будет передавать информацию о ходе выполнения во внешний интерфейс в режиме реального времени:

```json
{
  "type": "status",
  "message": "Searching: Basic information about Datawhale"
}
```

```json
{
  "type": "status",
  "message": "Summarizing search results..."
}
```

```json
{
  "type": "task",
  "task": {
    "id": 1,
    "title": "Basic information about Datawhale",
    "status": "completed"
  }
}
```

**(3) Этап 3: Отчетность**

Целью этапа отчетности является объединение сводных данных всех подзадач и создание итогового отчета. Система получает на вход сводку всех подзадач и темы исследования и выводит итоговый отчет в формате Markdown. Отчет состоит из пяти частей: заголовок, обзор, подробный анализ каждой подзадачи, резюме и ссылки. Например, для вопроса «Какая организация представляет собой Datawhale?» окончательный отчет может быть таким:

```markdown
# What Kind of Organization is Datawhale?

## Overview

This report systematically researched the open source organization Datawhale, covering four aspects: basic information, main projects, community culture, and influence.

## 1. Basic Information about Datawhale

Datawhale is an open source organization focused on data science and AI, founded in 2018...

(Insert summary of subtask 1 here)

## 2. Main Projects of Datawhale

Datawhale has released multiple high-quality open source tutorials, including Hello-Agents, Joyful-Pandas, etc...

(Insert summary of subtask 2 here)
...
## Summary

Through this research, we learned about Datawhale's organizational positioning, core projects, community culture, and social contributions. Datawhale is a pure learning community that has made important contributions to AI education.

## References

[1] https://github.com/datawhalechina
[2] https://datawhale.club/about
...
```

Агент формирования отчетов организует контент в логическом порядке подзадач, добавит краткий обзор в начале, объединит повторяющуюся информацию, унифицирует формат Markdown и упорядочит все ссылки на источники в разделе ссылок.

## 14.3 Проектирование агентской системы

### 14.3.1 Отдел ответственности агентов

В Deep Research Assistant мы разработали трех специализированных агентов, каждый из которых отвечает за определенную задачу. Это делает каждого агента простым, легким для понимания и обслуживания.

In Chapter 7, we learned how to use`SimpleAgent`для создания агентов. Философия дизайна`SimpleAgent`is simple and direct: each time the`run()`вызывается метод, Агент анализирует вопрос пользователя, решает, следует ли вызывать инструменты, а затем возвращает результат. Этот дизайн очень эффективен при решении простых задач, но при решении сложных задач, таких как глубокие исследования, нам необходимо продолжать использовать подход к многоагентному сотрудничеству.

Как показано в Таблице 14.1, три агента отвечают соответственно за планирование, обобщение и составление отчетов.

<div align="center">
  <p>Таблица 14.1 Responsibility Division of Three Agents</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-table-1.png" alt="" width="85%"/>
</div>

Давайте подробно представим дизайн каждого агента.

**Агент 1: Эксперт по планированию исследований (TODO Planner)**

**Ответственность**: разбейте темы исследования на 3–5 подзадач.

**Философия дизайна**. Основная задача специалиста по планированию исследований — понять тему исследования пользователя, проанализировать ключевые аспекты темы, а затем сгенерировать ряд подзадач. Этот процесс аналогичен этапу «мозгового штурма», который проводят исследователи-люди перед началом исследования.

**Быстрый дизайн**:

```python
todo_planner_instructions = """
You are a research planning expert. Your task is to decompose the user's research topic into 3-5 subtasks.

Current date: {current_date}

Research topic: {research_topic}

Please analyze this research topic and decompose it into 3-5 subtasks. Each subtask should:
1. Cover an important aspect of the topic
2. Have a clear research objective
3. Be able to find relevant materials through search engines

Please return the subtask list in JSON format, each subtask containing:
- title: Task title (concise and clear)
- intent: Task intent (why research this)
- query: Search query (query string for search engines, can use English for better search results)

Example output:
[
  {{
    "title": "What is a multimodal model",
    "intent": "Understand the basic concepts of multimodal models to lay the foundation for subsequent research",
    "query": "multimodal model definition concept 2024"
  }},
  ...
]

Please ensure:
1. Number of subtasks is between 3-5
2. Subtasks have logical relationships (e.g., from basics to applications, from current status to trends)
3. Search queries can accurately find relevant materials
4. Only return JSON, do not include other text
"""
```

**Ключевые моменты разработки**: приглашение включает текущую дату для получения самой последней информации, явно требует вывода в формате JSON для удобства анализа, помогает агенту понять ожидаемый результат с помощью примеров и подчеркивает такие ограничения, как количество подзадач и логические связи.

**Код реализации**:

ToolAwareSimpleAgent здесь является расширением SimpleAgent. Об этом можно узнать в разделе 14.3.2, здесь углубляться не нужно.

```python
class PlanningService:
    def __init__(self, llm: HelloAgentsLLM):
        self._agent = ToolAwareSimpleAgent(
            name="TODO Planner",
            system_prompt="You are a research planning expert",
            llm=llm,
            tool_call_listener=self._on_tool_call
        )

    def plan_todo_list(self, state: SummaryState) -> List[TodoItem]:
        prompt = todo_planner_instructions.format(
            current_date=get_current_date(),
            research_topic=state.research_topic,
        )

        response = self._agent.run(prompt)
        tasks_payload = self._extract_tasks(response)

        todo_items = []
        for idx, item in enumerate(tasks_payload, start=1):
            task = TodoItem(
                id=idx,
                title=item["title"],
                intent=item["intent"],
                query=item["query"],
            )
            todo_items.append(task)

        return todo_items

    def _extract_tasks(self, response: str) -> List[dict]:
        """Extract JSON from Agent response"""
        # Use regex to extract JSON part
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            raise ValueError("Unable to extract JSON from response")
```

**Агент 2: Эксперт по суммированию задач (Сумматор задач)**

**Обязанности**: обобщать результаты поиска, извлекать ключевую информацию.

**Философия дизайна**. Основная задача специалиста по обобщению задач — прочитать результаты поиска, извлечь ключевую информацию и представить ее в структурированном виде. Этот процесс аналогичен тому, как люди-исследователи делают заметки после прочтения литературы.

**Быстрый дизайн**:

```python
task_summarizer_instructions = """
You are a task summarization expert. Your task is to summarize search results and extract key information.

Task title: {task_title}
Task intent: {task_intent}
Search query: {task_query}

Search results:
{search_results}

Please carefully read the above search results, extract key information, and return a summary in Markdown format.

The summary should include:
1. **Core Viewpoints**: Core viewpoints and conclusions from search results
2. **Key Data**: Important numbers, dates, names, etc.
3. **Source Citations**: Add source citations for each viewpoint (using [1], [2], etc.)

Please ensure:
1. Summary is concise and clear, avoiding redundancy
2. Retain important details and data
3. Add source citations for each viewpoint
4. Use Markdown format (headings, lists, bold, etc.)

Example output:
## Core Viewpoints

Multimodal models are AI models that can process multiple types of data[1]. Unlike traditional unimodal models, multimodal models can simultaneously understand text, images, audio, etc.[2].

**Key Features:**
- Cross-modal understanding[1]
- Unified representation[3]
- End-to-end training[2]

## Sources

[1] https://example.com/source1
[2] https://example.com/source2
[3] https://example.com/source3
"""
```

**Ключевые моменты разработки**: подсказка включает название задачи, намерение, запрос и другой контекст, чтобы помочь агенту понять задачу, явно требует вывода, включающего основные точки зрения, ключевые данные и цитаты из источников, подчеркивает добавление цитат из источников для каждой точки зрения и помогает агенту понять ожидаемый формат вывода с помощью примеров.

**Код реализации**:

```python
class SummarizationService:
    def __init__(self, llm: HelloAgentsLLM):
        self._agent = ToolAwareSimpleAgent(
            name="Task Summarizer",
            system_prompt="You are a task summarization expert",
            llm=llm,
            tool_call_listener=self._on_tool_call
        )

    def summarize_task(
        self,
        task: TodoItem,
        search_results: List[dict]
    ) -> str:
        # Format search results
        formatted_sources = self._format_sources(search_results)

        prompt = task_summarizer_instructions.format(
            task_title=task.title,
            task_intent=task.intent,
            task_query=task.query,
            search_results=formatted_sources,
        )

        summary = self._agent.run(prompt)
        return summary

    def _format_sources(self, search_results: List[dict]) -> str:
        """Format search results"""
        formatted = []
        for idx, result in enumerate(search_results, start=1):
            formatted.append(
                f"[{idx}] {result['title']}\n"
                f"URL: {result['url']}\n"
                f"Snippet: {result['snippet']}\n"
            )
        return "\n".join(formatted)
```

**Агент 3: Эксперт по написанию отчетов (составитель отчетов)**

**Обязанности**: интеграция сводных данных по всем подзадачам и составление итогового отчета.

**Философия дизайна**. Основная задача эксперта по написанию отчета — объединить краткое изложение всех подзадач в структурированный отчет. Этот процесс аналогичен тому, как люди-исследователи пишут отчеты об исследованиях после завершения всех исследований.

**Быстрый дизайн**:

```python
report_writer_instructions = """
You are a report writing expert. Your task is to integrate the summaries of all subtasks and generate a structured research report.

Research topic: {research_topic}

Subtask summaries:
{task_summaries}

Please integrate all the above subtask summaries and generate a structured research report.

The report should include:
1. **Title**: Research topic
2. **Overview**: Briefly introduce the research topic and report structure (2-3 paragraphs)
3. **Detailed Analysis of Each Subtask**: Organize in logical order (using level-2 headings)
4. **Summary**: Summarize the main findings of the research (1-2 paragraphs)
5. **References**: All source citations (grouped by subtask)

Please ensure:
1. Report structure is clear and logically coherent
2. Eliminate duplicate information
3. Retain all source citations
4. Use Markdown format

Example output:
# Latest Advances in Multimodal Large Models

## Overview

This report systematically researched the latest advances in multimodal large models...

## 1. What is a Multimodal Model

(Insert summary of subtask 1 here)

## 2. What are the Latest Multimodal Models

(Insert summary of subtask 2 here)

...

## Summary

Through this research, we learned about...

## References

### Task 1: What is a Multimodal Model
[1] https://example.com/source1
...
"""
```

**Ключевые моменты**: в подсказке явно требуется, чтобы отчет включал заголовок, обзор, подробный анализ, резюме, ссылки и другие структуры, подчеркивается организация контента в логическом порядке, требуется объединение повторяющейся информации для устранения избыточности и сохраняются все ссылки на источники.

**Код реализации**:

```python
class ReportingService:
    def __init__(self, llm: HelloAgentsLLM):
        self._agent = ToolAwareSimpleAgent(
            name="Report Writer",
            system_prompt="You are a report writing expert",
            llm=llm,
            tool_call_listener=self._on_tool_call
        )

    def generate_report(
        self,
        research_topic: str,
        task_summaries: List[Tuple[TodoItem, str]]
    ) -> str:
        # Format subtask summaries
        formatted_summaries = self._format_summaries(task_summaries)

        prompt = report_writer_instructions.format(
            research_topic=research_topic,
            task_summaries=formatted_summaries,
        )

        report = self._agent.run(prompt)
        return report

    def _format_summaries(
        self,
        task_summaries: List[Tuple[TodoItem, str]]
    ) -> str:
        """Format subtask summaries"""
        formatted = []
        for idx, (task, summary) in enumerate(task_summaries, start=1):
            formatted.append(
                f"## Task {idx}: {task.title}\n"
                f"Intent: {task.intent}\n\n"
                f"{summary}\n"
            )
        return "\n".join(formatted)
```

### 14.3.2 Проект ToolAwareSimpleAgent

В главе 7 мы реализовали`SimpleAgent`, который является основным агентом платформы HelloAgents. Но в качестве помощника по глубоким исследованиям нам нужен агент, который может **записывать вызовы инструментов**. Вот где`ToolAwareSimpleAgent`происходит от.

В Deep Research Assistant нам необходимо записать статус вызова инструмента каждого агента для:

1. **Отладка**: просмотрите, какие инструменты вызывал агент и какие параметры были переданы.
2. **Журналирование**: записывайте все операции в процессе исследования.
3. **Анализ**: анализ поведения агента.
4. **Отображение прогресса**: показывает в режиме реального времени, что делает агент.

`SimpleAgent`сам по себе не поддерживает прослушивание вызовов инструментов, поэтому нам необходимо его расширить.

`ToolAwareSimpleAgent`добавляет`tool_call_listener`параметр поверх`SimpleAgent`. Это функция обратного вызова, которая вызывается каждый раз при вызове инструмента.

**Пример использования:**

```python
from hello_agents import ToolAwareSimpleAgent

def tool_listener(call_info):
    print(f"Agent: {call_info['agent_name']}")
    print(f"Tool: {call_info['tool_name']}")
    print(f"Parameters: {call_info['parsed_parameters']}")
    print(f"Result: {call_info['result']}")

agent = ToolAwareSimpleAgent(
    name="Research Assistant",
    system_prompt="You are a research assistant",
    llm=llm,
    tool_call_listener=tool_listener
)
```

`ToolAwareSimpleAgent`наследует от`SimpleAgent`и переопределяет`_execute_tool_call`метод:

```python
class ToolAwareSimpleAgent(SimpleAgent):
    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: HelloAgentsLLM,
        tool_registry: Optional[ToolRegistry] = None,
        tool_call_listener: Optional[Callable] = None,
    ):
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            llm=llm,
            tool_registry=tool_registry,
        )
        self._tool_call_listener = tool_call_listener

    def _execute_tool_call(self, tool_name: str, parameters: str) -> str:
        """Execute tool call and notify listener"""
        # Parse parameters
        parsed_parameters = self._parse_parameters(parameters)

        # Call tool
        result = super()._execute_tool_call(tool_name, parameters)

        # Notify listener
        if self._tool_call_listener:
            self._tool_call_listener({
                "agent_name": self.name,
                "tool_name": tool_name,
                "parsed_parameters": parsed_parameters,
                "result": result,
            })

        return result
```

В Deep Research Assistant мы используем`ToolAwareSimpleAgent`для записи всех вызовов инструментов агента:

```python
class DeepResearchAgent:
    def __init__(self, config: Configuration):
        self.config = config
        self.llm = HelloAgentsLLM(...)

        # Create tool call listener
        def tool_listener(call_info):
            self._emit_event({
                "type": "tool_call",
                "agent": call_info["agent_name"],
                "tool": call_info["tool_name"],
                "parameters": call_info["parsed_parameters"],
            })

        # Create three Agents, all using the same listener
        self.planner = PlanningService(self.llm, tool_listener)
        self.summarizer = SummarizationService(self.llm, tool_listener)
        self.reporter = ReportingService(self.llm, tool_listener)
```

Таким образом, все вызовы инструментов агента записываются и передаются во внешний интерфейс через SSE и отображаются пользователю в режиме реального времени.

### 14.3.3 Режим совместной работы агентов

Три агента имеют отношения **последовательного сотрудничества**, как показано на рис. 14.6.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-6.png" alt="" width="85%"/>
  <p>Рисунок 14.6 Процесс совместной работы агентов</p>
</div>

Характеристики режима последовательного сотрудничества:

1. **Линейный процесс**: агенты выполняются в фиксированном порядке.
2. **Очистить ввод и вывод**: ввод каждого агента берется из вывода предыдущего агента.
3. **Нет параллелизма**: одновременно работает только один агент.

`DeepResearchAgent`является основным координатором всей системы, отвечающим за планирование работы трех агентов:

```python
class DeepResearchAgent:
    def run(self, research_topic: str) -> str:
        # 1. Planning stage
        self._emit_event({"type": "status", "message": "Planning research tasks..."})
        todo_list = self.planner.plan_todo_list(research_topic)
        self._emit_event({"type": "tasks", "tasks": todo_list})

        # 2. Execution stage
        task_summaries = []
        for task in todo_list:
            self._emit_event({
                "type": "status",
                "message": f"Researching: {task.title}"
            })

            # Search
            search_results = self.search_service.search(task.query)

            # Summarize
            summary = self.summarizer.summarize_task(task, search_results)
            task_summaries.append((task, summary))

            self._emit_event({
                "type": "task_completed",
                "task_id": task.id
            })

        # 3. Reporting stage
        self._emit_event({"type": "status", "message": "Generating report..."})
        report = self.reporter.generate_report(research_topic, task_summaries)
        self._emit_event({"type": "report", "content": report})

        return report
```

## 14.4 Интеграция системы инструментов

### 14.4.1 Расширение SearchTool

В главе 7 мы реализовали базовую версию`SearchTool`, интегрируя поисковые системы Tavily и SerpApi, демонстрируя дизайнерскую идею поиска по нескольким источникам. В этой главе мы еще больше расширили возможности`SearchTool`, добавление DuckDuckGo, Perplexity, SearXNG и других поисковых систем, а также реализация расширенного режима (объединение нескольких поисковых систем). Поиск — основная функция Deep Research Assistant, и эти расширения позволяют системе адаптироваться к различным сценариям использования и потребностям.

Как показано в Таблице 14.2, добавленные на этот раз поисковые системы имеют разные характеристики и применимые сценарии.

<div align="center">
  <p>Таблица 14.2. Сравнение нескольких поисковых систем</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-table-2.png" alt="" width="85%"/>
</div>

О том, как продлить отдельно, мы больше не будем говорить. Для реализации вы можете обратиться к исходному коду и вариантам расширения в главе 7.`SearchTool`предоставляет единый интерфейс поиска. Независимо от того, какая поисковая система используется, метод вызова один и тот же.

В глубоком исследовательском помощнике выбираем поисковую систему через файл конфигурации:

```python
# config.py
class SearchAPI(str, Enum):
    TAVILY = "tavily"
    DUCKDUCKGO = "duckduckgo"
    PERPLEXITY = "perplexity"
    SEARXNG = "searxng"
    ADVANCED = "advanced"

class Configuration(BaseModel):
    search_api: SearchAPI = SearchAPI.DUCKDUCKGO
    # ...
```

```python
# .env
SEARCH_API=tavily
```

Таким образом, пользователи могут выбрать поисковую систему, изменив`.env`файл без изменения кода.

The result returned by`SearchTool`представляет собой словарь, содержащий:

- `results`: список результатов поиска, каждый результат содержит заголовок, URL-адрес и фрагмент.
- `backend`: используемая поисковая система
- `ответ`: ответ, сгенерированный ИИ (только в Perplexity)
- `notices`: информация для уведомлений (например, ограничения API, ошибки и т. д.).

Вот некоторые особые случаи.

Результаты поиска могут содержать повторяющиеся URL-адреса, нам необходимо выполнить дедупликацию:

```python
def deduplicate_sources(sources: List[dict]) -> List[dict]:
    """Remove duplicate URLs"""
    seen_urls = set()
    unique_sources = []

    for source in sources:
        if source["url"] not in seen_urls:
            seen_urls.add(source["url"])
            unique_sources.append(source)

    return unique_sources
```

Результаты поиска могут содержать большое количество текста, нам нужно ограничить количество токенов для каждого источника:

```python
def limit_source_tokens(source: dict, max_tokens: int = 2000) -> dict:
    """Limit the number of tokens for a source"""
    snippet = source["snippet"]

    # Simple token estimation: 1 token is approximately 4 characters
    max_chars = max_tokens * 4

    if len(snippet) > max_chars:
        snippet = snippet[:max_chars] + "..."

    return {
        **source,
        "snippet": snippet
    }
```

### 14.4.2 Использование NoteTool

В Deep Research Assistant мы используем`NoteTool`продолжать исследовательский прогресс.`NoteTool`— это встроенный инструмент, интегрированный в главу 9, используемый для создания, чтения, обновления и удаления заметок.

В процессе исследования нам необходимо записывать результаты поиска, резюме и окончательный отчет об исследовании для каждой подзадачи. Эту информацию необходимо сохранить на диск, чтобы при прерывании исследования можно было продолжить с последнего прогресса, а также было удобно просматривать все операции в процессе исследования и анализировать качество и эффективность исследования.

`NoteTool`сохраняет заметки в указанном каталоге рабочей области, причем каждая заметка представляет собой файл Markdown. Имя файла заметки — это идентификатор задачи, а содержимое включает название задачи, намерение задачи, поисковый запрос, результаты поиска и сводку.

Окончательно сгенерированный стиль файла будет иметь следующую древовидную структуру:

```
workspace/
├── notes/
│   ├── 1.md  # Notes for task 1
│   ├── 2.md  # Notes for task 2
│   ├── 3.md  # Notes for task 3
│   └── ...
└── reports/
    └── final_report.md  # Final report
```

В Deep Research Assistant мы используем`NoteTool`фиксировать ход исследования каждой подзадачи:

```python
class NotesService:
    def __init__(self, workspace: str):
        self.note_tool = NoteTool(workspace=workspace)

    def save_task_summary(
        self,
        task: TodoItem,
        search_results: List[dict],
        summary: str
    ):
        """Save task summary"""
        # Format note content
        content = self._format_note_content(
            task=task,
            search_results=search_results,
            summary=summary
        )

        # Create note
        self.note_tool.run({
            "action": "create",
            "title": f"Task {task.id}: {task.title}",
            "content": content,
            "tags": ["research", "summary"]
        })

    def _format_note_content(
        self,
        task: TodoItem,
        search_results: List[dict],
        summary: str
    ) -> str:
        """Format note content"""
        content = f"# Task {task.id}: {task.title}\n\n"
        content += f"## Task Information\n\n"
        content += f"- **Intent**: {task.intent}\n"
        content += f"- **Query**: {task.query}\n\n"

        content += f"## Search Results\n\n"
        for idx, result in enumerate(search_results, start=1):
            content += f"[{idx}] {result['title']}\n"
            content += f"URL: {result['url']}\n"
            content += f"Snippet: {result['snippet']}\n\n"

        content += f"## Summary\n\n{summary}\n"

        return content
```

### 14.4.3 Управление инструментами ToolRegistry

`ToolRegistry`— это реестр инструментов платформы HelloAgents, который также поддерживается в главе 7 и используется для управления регистрацией и вызовом всех инструментов. В Deep Research Assistant мы используем`ToolRegistry`управлять`SearchTool`и`NoteTool`.

Прежде чем создавать Агента, нам необходимо сначала зарегистрировать инструменты:

```python
from hello_agents import ToolAwareSimpleAgent
from hello_agents.tools import ToolRegistry
from hello_agents.tools import SearchTool
from hello_agents.tools import NoteTool

# Create tools
search_tool = SearchTool(backend="hybrid")
note_tool = NoteTool(workspace="./workspace/notes")

# Create registry
registry = ToolRegistry()

# Register tools
registry.register_tool(search_tool)
registry.register_tool(note_tool)

# Create Agent
agent = ToolAwareSimpleAgent(
    name="Research Assistant",
    system_prompt="You are a research assistant",
    llm=llm,
    tool_registry=registry
)
```

Когда агенту необходимо вызвать инструмент, он генерирует инструкцию вызова инструмента, как показано на рисунке 14.7.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-7.png" alt="" width="85%"/>
  <p>Рисунок 14.7 Процесс вызова инструмента</p>
</div>

**Процесс вызова инструмента**:

1. **Агент генерирует инструкцию**: Агент генерирует инструкцию по вызову инструмента, например `[TOOL_CALL:search_tool:{"input": "Datawhale Organization", "backend": "tavily"}]`
2. **Инструкция анализа**: ToolRegistry анализирует инструкцию, извлекает имя и параметры инструмента.
3. **Найти инструмент**: ToolRegistry находит соответствующий инструмент по имени инструмента.
4. **Вызов инструмента**: вызов метода run инструмента с передачей параметров.
5. **Возврат результата**: инструмент возвращает результат выполнения.
6. **Форматировать результат**: отформатируйте результат как строку и верните его агенту.

## 14.5 Реализация сервисного уровня

В этом разделе будет подробно представлена ​​реализация основных служб, включая PlanningService, SummarizationService, ReportingService и SearchService. Эти сервисы являются мостом, соединяющим агентов и инструменты, отвечающие за конкретную бизнес-логику.

### 14.5.1 Служба планирования задач

`PlanningService`отвечает за вызов агента по планированию исследования для разложения темы исследования на подзадачи. Это первый и наиболее важный шаг всего исследовательского процесса.

**(1) Подход к реализации**

Его основные обязанности:

1. **Подсказка по планированию сборки**: Подсказка по сборке на основе темы исследования и текущей даты.
2. **Агент планирования звонков**: вызовите агента TODO Planner, чтобы создать список подзадач.
3. **Разобрать ответ JSON**: извлечь список подзадач в формате JSON из ответа агента.
4. **Проверьте формат подзадачи**: убедитесь, что каждая подзадача содержит обязательные поля (заголовок, намерение, запрос).

```python
import re
import json
from typing import List, Callable, Optional
from datetime import datetime

from hello_agents import HelloAgentsLLM
from hello_agents import ToolAwareSimpleAgent
from models import TodoItem, SummaryState
from prompts import todo_planner_instructions

class PlanningService:
    """Task planning service"""

    def __init__(
        self,
        llm: HelloAgentsLLM,
        tool_call_listener: Optional[Callable] = None
    ):
        self._llm = llm
        self._tool_call_listener = tool_call_listener

        # Create planning Agent
        self._agent = ToolAwareSimpleAgent(
            name="TODO Planner",
            system_prompt="You are a research planning expert, skilled at decomposing complex research topics into clear subtasks.",
            llm=llm,
            tool_call_listener=tool_call_listener
        )

    def plan_todo_list(self, state: SummaryState) -> List[TodoItem]:
        """Plan TODO list

        Args:
            state: Research state, containing research topic

        Returns:
            Subtask list
        """
        # Build Prompt
        prompt = todo_planner_instructions.format(
            current_date=self._get_current_date(),
            research_topic=state.research_topic,
        )

        # Call Agent
        response = self._agent.run(prompt)

        # Parse JSON
        tasks_payload = self._extract_tasks(response)

        # Validate and create TodoItem
        todo_items = []
        for idx, item in enumerate(tasks_payload, start=1):
            # Validate required fields
            if not all(key in item for key in ["title", "intent", "query"]):
                raise ValueError(f"Task {idx} is missing required fields")

            task = TodoItem(
                id=idx,
                title=item["title"],
                intent=item["intent"],
                query=item["query"],
            )
            todo_items.append(task)

        return todo_items

    def _get_current_date(self) -> str:
        """Get current date"""
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_tasks(self, response: str) -> List[dict]:
        """Extract JSON from Agent response

        The Agent's response may contain extra text, such as:
        "Okay, I will plan the following tasks for you:\n[{...}, {...}]\nThese tasks cover..."

        We need to extract the JSON part.
        """
        # Method 1: Use regex to extract JSON array
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON parsing failed: {e}")

        # Method 2: If no JSON array is found, try to parse the entire response directly
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("Unable to extract JSON from response")
```

**(2) Анализ и проверка JSON**

JSON, возвращаемый агентом, может содержать дополнительный текст или ошибки формата, поэтому нам нужна надежная логика синтаксического анализа:

**Распространенные проблемы**:

1. **Содержит дополнительный текст**: агент может добавлять пояснительный текст до и после JSON.
2. **Ошибки формата**: в JSON могут отсутствовать кавычки, запятые и т. д.
3. **Отсутствуют поля**. В некоторых подзадачах могут отсутствовать обязательные поля.

**Решения**:

1. **Используйте регулярное выражение**: извлеките часть JSON.
2. **Несколько стратегий анализа**: сначала попробуйте извлечь массив JSON, а затем попробуйте выполнить анализ напрямую.
3. **Проверка полей**: убедитесь, что каждая подзадача содержит обязательные поля.

**Пример**:

```python
# Agent response example 1: Contains extra text
response1 = """
Okay, I will plan the following tasks for you:

[
  {
    "title": "What is a multimodal model",
    "intent": "Understand basic concepts",
    "query": "multimodal model definition"
  },
  {
    "title": "Latest multimodal models",
    "intent": "Understand technical status",
    "query": "latest multimodal models 2024"
  }
]

These tasks cover the basic information and core projects of the Datawhale organization.
"""

# Extract JSON
tasks1 = service._extract_tasks(response1)
# Result: [{"title": "Basic information about Datawhale", ...}, ...]

# Agent response example 2: Pure JSON
response2 = """
[
  {"title": "Basic information about Datawhale", "intent": "Understand organizational positioning", "query": "Datawhale organization introduction"},
  {"title": "Main projects of Datawhale", "intent": "Understand core content", "query": "Datawhale projects tutorials 2024"}
]
"""

# Extract JSON
tasks2 = service._extract_tasks(response2)
# Result: [{"title": "What is a multimodal model", ...}, ...]
```

**(3) Планирование оценки качества**

Хороший план должен соответствовать следующим критериям:

1. **Комплексное освещение**: охватите все важные аспекты темы.
2. **Четкая логика**: четкие логические связи между подзадачами.
3. **Точные запросы**. Поисковые запросы позволяют точно находить релевантные материалы.
4. **Соответствующее количество**: 3–5 подзадач.

Мы можем добавить метод оценки:

```python
def evaluate_plan(self, todo_items: List[TodoItem]) -> dict:
    """Evaluate planning quality

    Returns:
        Evaluation results, including score and suggestions
    """
    score = 100
    suggestions = []

    # Check quantity
    if len(todo_items) < 3:
        score -= 20
        suggestions.append("Too few subtasks, may miss important information")
    elif len(todo_items) > 5:
        score -= 10
        suggestions.append("Too many subtasks, may have redundancy")

    # Check query quality
    for task in todo_items:
        if len(task.query.split()) < 2:
            score -= 10
            suggestions.append(f"Query for task '{task.title}' is too simple")

    # Check logical relationships
    # (More complex logic checks can be added here)

    return {
        "score": score,
        "suggestions": suggestions
    }
```

### 14.5.2 Служба обобщения

`SummarizationService`отвечает за вызов агента суммирования задач для суммирования результатов поиска. Это основное звено исследовательского процесса, определяющее качество исследования.

Его обязанности:

1. **Форматировать результаты поиска**: форматировать результаты поиска в читаемый текст.
2. **Подсказка по сбору сводных данных**: Подсказка по сборке на основе информации о задаче и результатов поиска.
3. **Вызов агента суммирования вызовов**: вызов агента суммирования задач для создания сводки.
4. **Извлечение цитат из источников**: Извлечение цитат из резюме.

Основной код:

```python
from typing import List, Callable, Optional, Tuple

from hello_agents import HelloAgentsLLM
from hello_agents import ToolAwareSimpleAgent
from models import TodoItem
from prompts import task_summarizer_instructions

class SummarizationService:
    """Summarization service"""

    def __init__(
        self,
        llm: HelloAgentsLLM,
        tool_call_listener: Optional[Callable] = None
    ):
        self._llm = llm
        self._tool_call_listener = tool_call_listener

        # Create summarization Agent
        self._agent = ToolAwareSimpleAgent(
            name="Task Summarizer",
            system_prompt="You are a task summarization expert, skilled at extracting key information from search results.",
            llm=llm,
            tool_call_listener=tool_call_listener
        )

    def summarize_task(
        self,
        task: TodoItem,
        search_results: List[dict]
    ) -> Tuple[str, List[str]]:
        """Summarize task

        Args:
            task: Task information
            search_results: Search results list

        Returns:
            (Summary text, source URL list)
        """
        # Format search results
        formatted_sources = self._format_sources(search_results)

        # Build Prompt
        prompt = task_summarizer_instructions.format(
            task_title=task.title,
            task_intent=task.intent,
            task_query=task.query,
            search_results=formatted_sources,
        )

        # Call Agent
        summary = self._agent.run(prompt)

        # Extract source URLs
        source_urls = [result["url"] for result in search_results]

        return summary, source_urls

    def _format_sources(self, search_results: List[dict]) -> str:
        """Format search results

        Format search results into readable text, including:
        - Serial number
        - Title
        - URL
        - Snippet
        """
        formatted = []
        for idx, result in enumerate(search_results, start=1):
            formatted.append(
                f"[{idx}] {result['title']}\n"
                f"URL: {result['url']}\n"
                f"Snippet: {result['snippet']}\n"
            )
        return "\n".join(formatted)
```

### Проектирование структуры отчета

Итоговый отчет должен включать следующие части:

## Ссылки

### Задача 1: Что такое мультимодальная модель
-https://example.com/multimodal-model-definition
...

### Задача 2: Каковы новейшие мультимодальные модели
-https://example.com/gpt4v
...
...

### 14.5.3 Служба создания отчетов

`ReportingService`отвечает за вызов агента формирования отчетов для интеграции сводных данных всех подзадач. Это последний этап исследовательского процесса, на котором создается окончательный отчет об исследовании.

Его обязанности:

1. **Форматировать сводку подзадач**. Форматируйте все сводки подзадач в едином формате.
2. **Подсказка о создании отчета**: подсказка о создании отчета на основе темы исследования и сводки подзадач.
3. **Вызов агента по созданию отчетов**: вызов агента по созданию отчетов для создания окончательного отчета.
4. **Организация цитирования**. Организуйте все ссылки на источники в разделе «Ссылки».

**Реализация основного кода**:

```python
from typing import List, Callable, Optional, Tuple

from hello_agents import HelloAgentsLLM
from hello_agents import ToolAwareSimpleAgent
from models import TodoItem
from prompts import report_writer_instructions

class ReportingService:
    """Report generation service"""

    def __init__(
        self,
        llm: HelloAgentsLLM,
        tool_call_listener: Optional[Callable] = None
    ):
        self._llm = llm
        self._tool_call_listener = tool_call_listener

        # Create report Agent
        self._agent = ToolAwareSimpleAgent(
            name="Report Writer",
            system_prompt="You are a report writing expert, skilled at integrating information and generating structured reports.",
            llm=llm,
            tool_call_listener=tool_call_listener
        )

    def generate_report(
        self,
        research_topic: str,
        task_summaries: List[Tuple[TodoItem, str, List[str]]]
    ) -> str:
        """Generate final report

        Args:
            research_topic: Research topic
            task_summaries: Subtask summary list, each element is (task, summary, source URL list)

        Returns:
            Final report (Markdown format)
        """
        # Format subtask summaries
        formatted_summaries = self._format_summaries(task_summaries)

        # Build Prompt
        prompt = report_writer_instructions.format(
            research_topic=research_topic,
            task_summaries=formatted_summaries,
        )

        # Call Agent
        report = self._agent.run(prompt)

        return report

    def _format_summaries(
        self,
        task_summaries: List[Tuple[TodoItem, str, List[str]]]
    ) -> str:
        """Format subtask summaries

        Format all subtask summaries into a unified format, including:
        - Task serial number
        - Task title
        - Task intent
        - Summary content
        - Source URLs
        """
        formatted = []
        for idx, (task, summary, source_urls) in enumerate(task_summaries, start=1):
            formatted.append(
                f"## Task {idx}: {task.title}\n\n"
                f"**Intent**: {task.intent}\n\n"
                f"{summary}\n\n"
                f"**Sources**:\n"
            )
            for url in source_urls:
                formatted.append(f"- {url}\n")
            formatted.append("\n")

        return "".join(formatted)
```

### 14.5.4 Служба планирования поиска

`SearchService`отвечает за планирование поисковых систем, выполнение поиска и возврат результатов. Это мост, соединяющий агентов и SearchTool. Здесь мы не приняли обычную форму, когда SimpleAgent напрямую вызывает инструменты, а вместо этого возвращаем результаты выполнения SearchTool Агенту через промежуточный уровень, что делает Агента более ориентированным на обработку полученной информации.

Его обязанности:

1. **Поисковая система по расписанию**: выберите поисковую систему в зависимости от конфигурации.
2. **Выполнить поиск**: вызовите SearchTool для выполнения поиска.
3. **Результаты процесса**: дедупликация, ограничение токенов, форматирование.
4. **Обработка ошибок**: обработка ситуаций сбоя поиска.

Основной код:

```python
from typing import List, Optional
import logging

from hello_agents.tools import SearchTool
from config import Configuration

logger = logging.getLogger(__name__)

class SearchService:
    """Search scheduling service"""

    def __init__(self, config: Configuration):
        self.config = config

        # Create SearchTool
        self.search_tool = SearchTool(backend="hybrid")

    def search(
        self,
        query: str,
        max_results: int = 5
    ) -> List[dict]:
        """Execute search

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            Search results list
        """
        try:
            # Call SearchTool
            raw_response = self.search_tool.run({
                "input": query,
                "backend": self.config.search_api.value,
                "mode": "structured",
                "max_results": max_results
            })

            # Extract results
            results = raw_response.get("results", [])

            # Process results
            results = self._deduplicate_sources(results)
            results = self._limit_source_tokens(results)

            logger.info(f"Search successful: {query}, returned {len(results)} results")

            return results

        except Exception as e:
            logger.error(f"Search failed: {query}, error: {e}")
            return []

    def _deduplicate_sources(self, sources: List[dict]) -> List[dict]:
        """Remove duplicate URLs"""
        seen_urls = set()
        unique_sources = []

        for source in sources:
            url = source.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)

        return unique_sources

    def _limit_source_tokens(
        self,
        sources: List[dict],
        max_tokens_per_source: int = 2000
    ) -> List[dict]:
        """Limit the number of tokens per source"""
        limited_sources = []

        for source in sources:
            snippet = source.get("snippet", "")

            # Simple token estimation: 1 token is approximately 4 characters
            max_chars = max_tokens_per_source * 4

            if len(snippet) > max_chars:
                snippet = snippet[:max_chars] + "..."

            limited_sources.append({
                **source,
                "snippet": snippet
            })

        return limited_sources
```

Выберите поисковую систему на основе конфигурации, как показано на рисунке 14.8:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-8.png" alt="" width="85%"/>
  <p>Рисунок 14.8. Процесс планирования поисковой системы</p>
</div>

**Логика планирования**:

1. **Чтение конфигурации**: чтение конфигурации `SEARCH_API` из файла `.env`.
2. **Выберите систему**: выберите поисковую систему в зависимости от конфигурации (tavily, DuckDuckgo, Perplexity и т. д.).
3. **Выполнить поиск**: вызовите SearchTool для выполнения поиска.
4. **Результаты процесса**: дедупликация, ограничение токенов, форматирование.
5. **Возврат результатов**: возврат обработанных результатов поиска.

Чтобы повысить эффективность и сократить расходы, мы можем добавить кэширование результатов поиска:

```python
import hashlib
import json
from pathlib import Path

class SearchService:
    def __init__(self, config: Configuration):
        self.config = config
        self.search_tool = SearchTool(backend="hybrid")

        # Cache directory
        self.cache_dir = Path("./cache/search")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def search(
        self,
        query: str,
        max_results: int = 5,
        use_cache: bool = True
    ) -> List[dict]:
        """Execute search (with cache)"""
        # Generate cache key
        cache_key = self._generate_cache_key(query, max_results)
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Try to read from cache
        if use_cache and cache_file.exists():
            logger.info(f"Reading search results from cache: {query}")
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        # Execute search
        results = self._execute_search(query, max_results)

        # Save to cache
        if use_cache and results:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        return results

    def _generate_cache_key(self, query: str, max_results: int) -> str:
        """Generate cache key"""
        # Generate MD5 hash using query and max results
        content = f"{query}_{max_results}_{self.config.search_api.value}"
        return hashlib.md5(content.encode()).hexdigest()
```

С помощью четырех основных служб (PlanningService, SummarizationService, ReportingService, SearchService) мы построили полный процесс исследования. Каждая из этих служб выполняет свои обязанности и сотрудничает через понятные интерфейсы, обеспечивая автоматизацию процесса от темы исследования до окончательного отчета.

## 14.6 Проектирование внешнего взаимодействия

В предыдущих разделах мы реализовали полную серверную систему. В этом разделе будет подробно описан дизайн внешнего интерфейса, включая полноэкранный модальный диалоговый интерфейс, отображение прогресса в реальном времени и визуализацию результатов исследования.

### 14.6.1 Дизайн пользовательского интерфейса полноэкранного модального диалогового окна

Помощник по глубоким исследованиям использует полноэкранный модальный диалоговый дизайн пользовательского интерфейса, который имеет следующие преимущества:

1. **Опыт погружения**: полноэкранный режим, отсутствие отвлекающих факторов и сосредоточенность на исследованиях.
2. **Четкая иерархия**: главная страница и страница исследования разделены и имеют четкую иерархию.
3. **Легко закрыть**: нажмите кнопку закрытия или нажмите клавишу ESC, чтобы вернуться на главную страницу.
4. **Адаптивный дизайн**: адаптируется к экранам разных размеров.

Как показано на рисунке 14.9, полноэкранное модальное диалоговое окно состоит из следующих частей:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-9.png" alt="" width="85%"/>
  <p>Рисунок 14.9 Пользовательский интерфейс полноэкранного модального диалогового окна</p>
</div>

**Компоненты пользовательского интерфейса**:

1. **Верхняя панель**: содержит тему исследования и кнопку закрытия.
2. **Область прогресса**: показывает текущий прогресс исследований (планирование, выполнение, отчетность).
3. **Область контента**: отображаются результаты исследования (формат Markdown).
4. **Нижняя панель**: показывает информацию о статусе (например, «Исследование...», «Завершено»).

Соответствующая реализация Vue выглядит следующим образом (ResearchModal.vue):

```vue
<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <!-- Top bar -->
      <div class="modal-header">
        <h2>{{ researchTopic }}</h2>
        <button @click="close" class="close-button">
          <svg><!-- Close icon --></svg>
        </button>
      </div>

      <!-- Progress area -->
      <div class="progress-section">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: progressPercentage + '%' }"
          ></div>
        </div>
        <div class="progress-text">{{ progressText }}</div>
      </div>

      <!-- Content area -->
      <div class="content-section">
        <div v-if="isLoading" class="loading-spinner">
          <div class="spinner"></div>
          <p>Researching, please wait...</p>
        </div>

        <div v-else class="markdown-content" v-html="renderedMarkdown"></div>
      </div>

      <!-- Bottom bar -->
      <div class="modal-footer">
        <span class="status-text">{{ statusText }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { marked } from 'marked'

interface Props {
  isOpen: boolean
  researchTopic: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

// State
const isLoading = ref(true)
const progressPercentage = ref(0)
const progressText = ref('Preparing...')
const statusText = ref('Researching...')
const markdownContent = ref('')

// Render Markdown
const renderedMarkdown = computed(() => {
  return marked(markdownContent.value)
})

// Close modal
const close = () => {
  emit('close')
}

// Listen for ESC key
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    close()
  }
}

// Add keyboard listener on mount
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    document.addEventListener('keydown', handleKeydown)
  } else {
    document.removeEventListener('keydown', handleKeydown)
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
...
</style>
```

Чтобы адаптироваться к разным размерам экрана, добавляем медиа-запросы:

```css
/* Tablet devices */
@media (max-width: 768px) {
  .modal-container {
    width: 95vw;
    height: 95vh;
  }

  .modal-header,
  .progress-section,
  .content-section,
  .modal-footer {
    padding: 15px 20px;
  }
}

/* Mobile devices */
@media (max-width: 480px) {
  .modal-container {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .modal-header h2 {
    font-size: 18px;
  }
}
```

### 14.6.2 Отображение прогресса в реальном времени

Ассистент по глубоким исследованиям использует SSE для отображения прогресса в реальном времени. SSE — это технология принудительной отправки сервером, которая позволяет серверу активно отправлять данные клиенту, что также объясняется в главе о протоколе.

Как показано на рисунке 14.10, процесс SSE включает следующие этапы:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/14-figures/14-10.png" alt="" width="85%"/>
  <p>Рисунок 14.10 Процесс SSE</p>
</div>

**Описание процесса**:

1. **Клиент инициирует запрос**: отправьте POST-запрос в `/api/research`, содержащий тему исследования.
2. **Сервер устанавливает соединение SSE**: возвращает ответ `text/event-stream`.
3. **Сервер способствует прогрессу**: Периодически продвигайте прогресс исследований (планирование, выполнение, отчетность).
4. **Клиент получает информацию о ходе выполнения**: прослушивайте события SSE, обновляйте пользовательский интерфейс.
5. **Исследование завершено**: сервер отправляет окончательный отчет и закрывает соединение.

Если вы хотите использовать SSE во внешних и внутренних проектах, вам также необходимо выполнить следующие настройки.

**Верхняя конечная точка FastAPI SSE**:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import json

app = FastAPI()

async def research_stream(topic: str) -> AsyncGenerator[str, None]:
    """Research streaming generator

    Generate SSE format data:
    data: {"type": "progress", "data": {...}}

    """
    try:
        # 1. Planning stage
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'planning', 'percentage': 10, 'text': 'Planning research tasks...'})}\n\n"

        # Call PlanningService
        todo_items = await planning_service.plan_todo_list(topic)

        yield f"data: {json.dumps({'type': 'plan', 'data': [item.dict() for item in todo_items]})}\n\n"

        # 2. Execution stage
        task_summaries = []
        for idx, task in enumerate(todo_items, start=1):
            # Update progress
            percentage = 10 + (idx / len(todo_items)) * 70
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'executing', 'percentage': percentage, 'text': f'Researching task {idx}/{len(todo_items)}: {task.title}'})}\n\n"

            # Search
            search_results = await search_service.search(task.query)

            # Summarize
            summary, source_urls = await summarization_service.summarize_task(task, search_results)

            task_summaries.append((task, summary, source_urls))

            # Push task summary
            yield f"data: {json.dumps({'type': 'task_summary', 'task_id': task.id, 'summary': summary})}\n\n"

        # 3. Reporting stage
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'reporting', 'percentage': 90, 'text': 'Generating final report...'})}\n\n"

        # Generate report
        report = await reporting_service.generate_report(topic, task_summaries)

        # Push final report
        yield f"data: {json.dumps({'type': 'report', 'data': report})}\n\n"

        # Complete
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'completed', 'percentage': 100, 'text': 'Research complete!'})}\n\n"

    except Exception as e:
        # Error handling
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.post("/api/research")
async def research(request: ResearchRequest):
    """Research endpoint (SSE)"""
    return StreamingResponse(
        research_stream(request.topic),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**Внешний интерфейс с использованием EventSource для получения SSE**:

```typescript
// composables/useResearch.ts
import { ref } from 'vue'

export function useResearch() {
  const isLoading = ref(false)
  const progressPercentage = ref(0)
  const progressText = ref('')
  const markdownContent = ref('')
  const error = ref<string | null>(null)

  const startResearch = (topic: string) => {
    isLoading.value = true
    error.value = null

    // Create EventSource
    const eventSource = new EventSource(`/api/research?topic=${encodeURIComponent(topic)}`)

    // Listen for messages
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'progress':
          progressPercentage.value = data.percentage
          progressText.value = data.text
          break

        case 'plan':
          // Display planning results
          console.log('Planning results:', data.data)
          break

        case 'task_summary':
          // Append task summary to Markdown
          markdownContent.value += `\n\n## Task ${data.task_id}\n\n${data.summary}`
          break

        case 'report':
          // Display final report
          markdownContent.value = data.data
          break

        case 'error':
          error.value = data.message
          eventSource.close()
          isLoading.value = false
          break

        case 'completed':
          eventSource.close()
          isLoading.value = false
          break
      }
    }

    // Error handling
    eventSource.onerror = (err) => {
      console.error('SSE error:', err)
      error.value = 'Connection failed, please retry'
      eventSource.close()
      isLoading.value = false
    }
  }

  return {
    isLoading,
    progressPercentage,
    progressText,
    markdownContent,
    error,
    startResearch,
  }
}
```

**Использование в компоненте**:

```vue
<script setup lang="ts">
import { useResearch } from '@/composables/useResearch'

const {
  isLoading,
  progressPercentage,
  progressText,
  markdownContent,
  error,
  startResearch
} = useResearch()

const handleStartResearch = (topic: string) => {
  startResearch(topic)
}
</script>
```

### 14.6.3 Визуализация результатов исследования

Результаты исследований отображаются в формате Markdown, включая заголовки, абзацы, списки, цитаты и другие элементы. Мы используем`marked`библиотека для преобразования Markdown в HTML и добавления собственных стилей.

**Рендеринг уценки**:

```typescript
import { marked } from 'marked'

// Configure marked
marked.setOptions({
  breaks: true,  // Support line breaks
  gfm: true,     // Support GitHub Flavored Markdown
})

// Render
const renderedHtml = marked(markdownContent.value)
```

Отчеты об исследованиях содержат большое количество ссылок на источники, с которыми необходимо обращаться особым образом:

```markdown
## References

### Task 1: Basic Information about Datawhale
- [Datawhale GitHub](https://github.com/datawhalechina)
- [Datawhale Official Website](https://datawhale.club)

### Task 2: Main Projects of Datawhale
- [Hello-Agents Tutorial](https://github.com/datawhalechina/Hello-Agents)
...
```

Благодаря полноэкранному модальному диалоговому интерфейсу, отображению прогресса SSE в реальном времени и визуализации результатов Markdown мы создали удобный интерфейс. Пользователи могут наглядно видеть ход исследований и просматривать результаты исследований в красивом формате.

## 14.7 Краткое содержание главы

В этой главе мы с нуля создали полную автоматизированную систему агентов глубоких исследований. Давайте рассмотрим основные моменты:

**(1) Парадигма исследования, основанного на TODO**

Мы предложили новую исследовательскую парадигму — исследование, основанное на TODO. Эта парадигма разлагает сложные темы исследования на выполнимые подзадачи и завершает исследование в три этапа:

- **Этап планирования**: разбейте тему исследования на 3–5 подзадач, каждая подзадача содержит заголовок, цель и поисковый запрос.
- **Этап выполнения**: выполнение поиска и обобщения для каждой подзадачи, генерация структурированных знаний.
- **Этап отчетности**: интеграция сводных данных по всем подзадачам и создание итогового отчета об исследовании.

Преимущества этой парадигмы:

1. **Высокая управляемость**: каждая подзадача имеет четкие цели и объем.
2. **Надежное качество**: выделенные агенты обеспечивают качество на каждом этапе.
3. **Простота отладки**: можно отлаживать каждую подзадачу отдельно.
4. **Хорошая масштабируемость**: можно легко добавлять новые или изменять существующие подзадачи.

**(2) Трехагентная система взаимодействия**

Мы разработали трех специализированных Агентов, каждый из которых выполняет свои обязанности:

- **TODO Planner (эксперт по планированию исследований)**: отвечает за разложение тем исследования на подзадачи.
- **Суммаризатор задач (эксперт по суммированию задач)**: отвечает за обобщение результатов поиска для каждой подзадачи.
- **Составитель отчетов (эксперт по написанию отчетов)**: отвечает за интеграцию сводных данных всех подзадач и создание итогового отчета.

Плюсами данной конструкции являются:

1. **Четкие обязанности**: каждый агент фокусируется на конкретной задаче.
2. **Оптимизация подсказок**: можно настроить специальные подсказки для каждого агента.
3. **Простота обслуживания**: изменение одного агента не влияет на другие агенты.
4. **Гарантия качества**: каждый агент является «экспертом» в своей области.

**(3) Дизайн ToolAwareSimpleAgent**

Мы продлили`SimpleAgent`платформы HelloAgents и реализовано`ToolAwareSimpleAgent`. Этот агент имеет возможность прослушивания вызовов инструментов и может:

- **Прослушивание вызовов инструментов**: прослушивайте каждый вызов инструмента с помощью функций обратного вызова.
- **Обратная связь в режиме реального времени**. Передавайте информацию о вызовах инструментов на внешний интерфейс в режиме реального времени.
- **Поддержка отладки**: записывайте все вызовы инструментов для упрощения отладки.

Этот агент интегрирован в структуру HelloAgents и может быть повторно использован в других проектах.

**(4) Интеграция системы инструментов**

Мы полностью использовали систему инструментов платформы HelloAgents:

- **SearchTool**: расширен для поддержки большего количества поисковых систем (Tavily, DuckDuckGo, Perplexity и т. д.).
- **NoteTool**: сохранение прогресса исследований, поддержка восстановления и аудита.
- **ToolRegistry**: единое управление всеми инструментами, поддержка пользовательских расширений.

Благодаря дизайну на основе конфигурации пользователи могут легко переключать поисковые системы без изменения кода.

**(5) Реализация основного сервиса**

Мы реализовали четыре основных сервиса, соединяющих агентов и инструменты:

- **PlanningService**: агент планирования звонков, анализ JSON, проверка формата.
- **SummarizationService**: вызов агента суммирования, обработка результатов поиска, извлечение источников.
- **ReportingService**: вызов агента отчетов, интеграция сводок, создание отчета.
- **SearchService**: поисковые системы по расписанию, результаты обработки, ухудшение ошибок, кэширование результатов.

Каждая из этих служб выполняет свои обязанности и сотрудничает через понятные интерфейсы, обеспечивая автоматизацию процесса от темы исследования до окончательного отчета.

**(6) Дизайн внешнего взаимодействия**

Мы разработали удобный интерфейс:

- **Полноэкранное модальное диалоговое окно**: эффект погружения, четкая иерархия.
- **Прогресс SSE в реальном времени**: отображение прогресса исследований в реальном времени, удобство для пользователей.
- **Визуализация уценки**: красивый формат, понятная структура.

С помощью стека технологий Vue 3 + TypeScript + SSE мы реализовали современное веб-приложение.

Эти знания применимы не только к научным сотрудникам, но также могут быть применены к другим приложениям искусственного интеллекта. Мы надеемся, что читатели смогут изучить больше возможностей на основе этой главы и создать более мощные системы искусственного интеллекта.

В следующей главе мы построим мультиагентную систему в сочетании с игровым движком — Cyber ​​Town, исследуя сложные модели взаимодействия и сотрудничества между агентами. Следите за обновлениями!

