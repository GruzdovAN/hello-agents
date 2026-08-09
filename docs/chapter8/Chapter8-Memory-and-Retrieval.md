# Глава 8. Память и поиск

В предыдущих главах мы построили базовую архитектуру платформы HelloAgents, реализовав различные парадигмы агентов и системы инструментов. Однако нашему фреймворку по-прежнему не хватает важнейшей возможности: **памяти**. Если агент не может помнить предыдущие взаимодействия или учиться на историческом опыте, его производительность будет сильно ограничена в непрерывных разговорах или сложных задачах.

В этой главе в HelloAgents будут добавлены две основные возможности на основе платформы, созданной в главе 7: **Система памяти** и **Поколение с расширенным поиском (RAG)**. Мы примем подход «расширение структуры + популяризация знаний», глубоко понимая теоретические основы памяти и RAG в процессе построения и, в конечном итоге, внедряя агентную систему с полными возможностями памяти и извлечения знаний.


## 8.1 От когнитивной науки к памяти агента

### 8.1.1 Вдохновение от систем человеческой памяти

Прежде чем создавать систему памяти агента, давайте сначала поймем с точки зрения когнитивной науки, как люди обрабатывают и хранят информацию. Человеческая память — это многоуровневая когнитивная система, которая не только хранит информацию, но также классифицирует и систематизирует информацию на основе важности, времени и контекста. Когнитивная психология предоставляет классическую теоретическую основу для понимания структуры и процессов памяти<sup>[1]</sup>, как показано на рис. 8.1.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-1.png" alt="Human Memory System Structure" width="85%"/>
  <p>Рисунок 8.1. Иерархическая структура системы памяти человека.</p>
</div>

Согласно исследованиям когнитивной психологии, человеческую память можно разделить на следующие уровни:

1. **Сенсорная память**: очень короткая продолжительность (0,5–3 секунды), огромная емкость, отвечающая за временное хранение всей информации, полученной органами чувств.
2. **Рабочая память**: кратковременная (15–30 секунд), ограниченная емкость (7±2 элемента), отвечает за обработку информации в текущих задачах.
3. **Долговременная память**: Длительная продолжительность (может длиться всю жизнь), почти неограниченная емкость, далее делится на:
   - **Процедурная память**: навыки и привычки (например, езда на велосипеде).
   - **Декларативная память**: Знания, которые можно выразить на языке, которые далее делятся на:
     - **Семантическая память**: общие знания и понятия (например, «Париж — столица Франции»).
     - **Эпизодические воспоминания**: личный опыт и события (например, «содержание вчерашней встречи»).

### 8.1.2 Зачем агентам нужна память и RAG

Опираясь на устройство систем человеческой памяти, мы можем понять, почему агентам также нужны аналогичные возможности памяти. Важной характеристикой человеческого интеллекта является способность запоминать прошлый опыт, учиться на нем и применять этот опыт в новых ситуациях. Точно так же по-настоящему интеллектуальному агенту также необходимы возможности памяти. Агенты, использующие LLM, обычно сталкиваются с двумя фундаментальными ограничениями: **забывание состояния разговора** и **ограничения встроенных знаний**.

(1) Ограничение 1: забывание разговора из-за безгражданства

Современные модели больших языков, хотя и мощные, разработаны так, чтобы быть **апатридами**. Это означает, что каждый пользовательский запрос (или вызов API) представляет собой независимое, несвязанное вычисление. Сама модель не «запоминает» автоматически содержание предыдущего разговора. Это приносит несколько проблем:

1. **Потеря контекста**. При длительных разговорах важная информация может быть потеряна из-за ограничений контекстного окна.
2. **Отсутствие персонализации**: агент не может запомнить предпочтения, привычки или конкретные потребности пользователя.
3. **Ограниченная способность к обучению**: Невозможно учиться и совершенствоваться на основе прошлых успехов или неудач.
4. **Проблемы с последовательностью**: могут давать противоречивые ответы в многоходовых беседах.

Давайте разберемся в этой проблеме на конкретном примере:

```python
# How to use Agent from Chapter 7
from hello_agents import SimpleAgent, HelloAgentsLLM

agent = SimpleAgent(name="Learning Assistant", llm=HelloAgentsLLM())

# First conversation
response1 = agent.run("My name is Zhang San, I'm learning Python and have mastered basic syntax")
print(response1)  # "Great! Python basic syntax is an important foundation for programming..."
 
# Second conversation (new session, such as after restarting the program and creating a new Agent)
agent = SimpleAgent(name="Learning Assistant", llm=HelloAgentsLLM())
response2 = agent.run("Do you remember my learning progress?")
print(response2)  # "Sorry, I don't know your learning progress..."
```

Обратите внимание, что`SimpleAgent`из главы 7 временно сохраняет текущий диалог в`_history`внутри одного и того же экземпляра, поэтому последовательные ходы в одном и том же процессе и экземпляре могут нести недавний контекст. Однако эта история представляет собой лишь временный список сообщений. Он не сохраняется между сеансами и не поддерживает долгосрочное извлечение, забывание или консолидацию.

Чтобы решить эту проблему, в нашу структуру необходимо ввести систему памяти.

(2) Ограничение 2: ограничения встроенных знаний модели.

Помимо забывания истории разговоров, еще одним основным ограничением студентов LLM является то, что их знания **статичны и ограничены**. Эти знания полностью основаны на данных их обучения, что приводит к ряду проблем:

1. **Своевременность знаний**: для крупных моделей указана дата окончания сбора обучающих данных, и они не могут получить доступ к самой последней информации.
2. **Знания, специфичные для предметной области**: общим моделям может не хватать достаточной глубины в конкретных областях.
3. **Фактическая точность**: Уменьшите галлюцинации модели за счет проверки поиска.
4. **Объяснимость**: предоставьте источники информации, чтобы повысить достоверность ответа.

Чтобы преодолеть это ограничение, появилась технология RAG. Его основная идея — получить наиболее релевантную информацию из внешней базы знаний (например, документов, баз данных, API) до того, как модель сгенерирует ответ, и предоставить эту информацию в качестве контекста модели.

### 8.1.3 Проектирование архитектуры системы памяти и RAG

Основываясь на основе структуры, заложенной в главе 7, и вдохновении когнитивной науки, мы разработали многоуровневую архитектуру системы памяти и RAG, как показано на рисунке 8.2. Эта архитектура не только опирается на иерархическую структуру систем человеческой памяти, но также полностью учитывает масштабируемость инженерной реализации. При реализации мы проектируем память и RAG как два независимых инструмента:`memory_tool`отвечает за хранение и поддержание информации о взаимодействии во время разговоров, в то время как`rag_tool`отвечает за извлечение соответствующей информации из пользовательских баз знаний в качестве контекста и может автоматически сохранять важные результаты поиска в системе памяти.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-2.png" alt="HelloAgents Memory and RAG System Architecture" width="95%"/>
  <p>Рисунок 8.2 Общая архитектура памяти HelloAgents и системы RAG</p>
</div>

Система памяти имеет четырехуровневую архитектуру:

```
HelloAgents Memory System
├── Infrastructure Layer
│   ├── MemoryManager - Memory manager (unified scheduling and coordination)
│   ├── MemoryItem - Memory data structure (standardized memory items)
│   ├── MemoryConfig - Configuration management (system parameter settings)
│   └── BaseMemory - Memory base class (common interface definition)
├── Memory Types Layer
│   ├── WorkingMemory - Working memory (temporary information, TTL management)
│   ├── EpisodicMemory - Episodic memory (specific events, time series)
│   ├── SemanticMemory - Semantic memory (abstract knowledge, graph relationships)
│   └── PerceptualMemory - Perceptual memory (multimodal data)
├── Storage Backend Layer
│   ├── QdrantVectorStore - Vector storage (high-performance semantic retrieval)
│   ├── Neo4jGraphStore - Graph storage (knowledge graph management)
│   └── SQLiteDocumentStore - Document storage (structured persistence)
└── Embedding Service Layer
    ├── DashScopeEmbedding - Tongyi Qianwen embedding (cloud API)
    ├── LocalTransformerEmbedding - Local embedding (offline deployment)
    └── TFIDFEmbedding - TFIDF embedding (lightweight fallback)
```

Система RAG фокусируется на приобретении и использовании внешних знаний:

```
HelloAgents RAG System
├── Document Processing Layer
│   ├── DocumentProcessor - Document processor (multi-format parsing)
│   ├── Document - Document object (metadata management)
│   └── Pipeline - RAG pipeline (end-to-end processing)
├── Embedding Layer
│   └── Unified Embedding Interface - Reuses memory system's embedding service
├── Vector Storage Layer
│   └── QdrantVectorStore - Vector database (namespace isolation)
└── Intelligent Q&A Layer
    ├── Multi-strategy Retrieval - Vector retrieval + MQE + HyDE
    ├── Context Construction - Intelligent fragment merging and truncation
    └── LLM-Enhanced Generation - Accurate Q&A based on context
```

### 8.1.4 Цели обучения и быстрый опыт

Давайте сначала посмотрим на основное содержание обучения главы 8:

```
hello-agents/
├── hello_agents/
│   ├── memory/                   # Memory system module
│   │   ├── base.py               # Basic data structures (MemoryItem, MemoryConfig, BaseMemory)
│   │   ├── manager.py            # Memory manager (unified coordination and scheduling)
│   │   ├── embedding.py          # Unified embedding service (DashScope/Local/TFIDF)
│   │   ├── types/                # Memory type implementations
│   │   │   ├── working.py        # Working memory (TTL management, pure in-memory)
│   │   │   ├── episodic.py       # Episodic memory (event sequence, SQLite+Qdrant)
│   │   │   ├── semantic.py       # Semantic memory (knowledge graph, Qdrant+Neo4j)
│   │   │   └── perceptual.py     # Perceptual memory (multimodal, SQLite+Qdrant)
│   │   ├── storage/              # Storage backend implementations
│   │   │   ├── qdrant_store.py   # Qdrant vector storage (high-performance vector retrieval)
│   │   │   ├── neo4j_store.py    # Neo4j graph storage (knowledge graph management)
│   │   │   └── document_store.py # SQLite document storage (structured persistence)
│   │   └── rag/                  # RAG system
│   │       ├── pipeline.py       # RAG pipeline (end-to-end processing)
│   │       └── document.py       # Document processor (multi-format parsing)
│   └── tools/builtin/            # Extended built-in tools
│       ├── memory_tool.py        # Memory tool (Agent memory capability)
│       └── rag_tool.py           # RAG tool (intelligent Q&A capability)
└──
```

**Быстрое начало: установка HelloAgents Framework**

Чтобы читатели могли быстро освоить всю функциональность этой главы, мы предоставляем устанавливаемый непосредственно пакет Python. Вы можете установить версию, соответствующую этой главе, с помощью следующих команд:

```bash
# If you encounter model unavailability in version 0.2.0, please refer to issue#320 or switch to version 0.2.9 for testing.
pip install "hello-agents[all]==0.2.0"
python -m spacy download zh_core_web_sm
python -m spacy download en_core_web_sm
```

Кроме того, вам необходимо настроить базу данных графов, базу данных векторов, LLM и API решения для внедрения в`.env`. В руководстве Qdrant используется для векторной базы данных, Neo4J для графовой базы данных, а платформа Bailian предпочтительна для встраивания. Если API недоступен, вы можете переключиться на решение модели локального развертывания.

```bash
# ================================
# Qdrant Vector Database Configuration - Get API key: https://cloud.qdrant.io/
# ================================
# Use Qdrant cloud service (recommended)
QDRANT_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your_qdrant_api_key_here

# Or use local Qdrant (requires Docker)
# QDRANT_URL=http://localhost:6333
# QDRANT_API_KEY=

# Qdrant collection configuration
QDRANT_COLLECTION=hello_agents_vectors
QDRANT_VECTOR_SIZE=384
QDRANT_DISTANCE=cosine
QDRANT_TIMEOUT=30

# ================================
# Neo4j Graph Database Configuration - Get API key: https://neo4j.com/cloud/aura/
# ================================
# Use Neo4j Aura cloud service (recommended)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# Or use local Neo4j (requires Docker)
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USERNAME=neo4j
# NEO4J_PASSWORD=hello-agents-password

# Neo4j connection configuration
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_LIFETIME=3600
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_TIMEOUT=60

# ==========================
# Embedding Configuration Example - Get from Alibaba Cloud Console: https://dashscope.aliyun.com/
# ==========================
# - If empty, dashscope defaults to text-embedding-v3; local defaults to sentence-transformers/all-MiniLM-L6-v2
EMBED_MODEL_TYPE=dashscope
EMBED_MODEL_NAME=
EMBED_API_KEY=
EMBED_BASE_URL=
```

Обучение в этой главе можно проводить двумя способами:

1. **Экспериментальное обучение**: установите платформу напрямую с помощью pip, запустите пример кода и быстро освойте различные функции.
2. **Глубокое обучение**: следуйте содержанию главы, реализуйте каждый компонент с нуля и глубоко поймите философию проектирования платформы и детали реализации.

Мы рекомендуем выбрать путь обучения «сначала опыт, а затем внедрение». В этой главе мы предоставляем полные тестовые файлы. Вы можете переписать основные функции и запустить тесты, чтобы проверить правильность вашей реализации.

Следуя принципам проектирования, установленным в главе 7, мы инкапсулируем память и возможности RAG как стандартные инструменты, а не создаем новые классы агентов. Прежде чем начать, давайте потратим 30 секунд на создание агента с памятью и возможностями RAG с помощью Hello-агентов!

```python
# Configure the LLM API in .env in the same folder
from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import MemoryTool, RAGTool

# Create LLM instance
llm = HelloAgentsLLM()

# Create Agent
agent = SimpleAgent(
    name="Intelligent Assistant",
    llm=llm,
    system_prompt="You are an AI assistant with memory and knowledge retrieval capabilities"
)

# Create tool registry
tool_registry = ToolRegistry()

# Add memory tool
memory_tool = MemoryTool(user_id="user123")
tool_registry.register_tool(memory_tool)

# Add RAG tool
rag_tool = RAGTool(knowledge_base_path="./knowledge_base")
tool_registry.register_tool(rag_tool)

# Configure tools for Agent
agent.tool_registry = tool_registry

# Start conversation
response = agent.run("Hello! Please remember my name is Zhang San, I am a Python developer")
print(response)
```

Если все настроено правильно, вы увидите следующее содержимое:

```bash
[OK] SQLite database tables and indexes created
[OK] SQLite document storage initialized: ./memory_data\memory.db
INFO:hello_agents.memory.storage.qdrant_store:✅ Successfully connected to Qdrant cloud service: https://0c517275-2ad0-4442-8309-11c36dc7e811.us-east-1-1.aws.cloud.qdrant.io:6333
INFO:hello_agents.memory.storage.qdrant_store:✅ Using existing Qdrant collection: hello_agents_vectors
INFO:hello_agents.memory.types.semantic:✅ Embedding model ready, dimension: 1024
INFO:hello_agents.memory.types.semantic:✅ Qdrant vector database initialization complete
INFO:hello_agents.memory.storage.neo4j_store:✅ Successfully connected to Neo4j cloud service: neo4j+s://851b3a28.databases.neo4j.io
INFO:hello_agents.memory.types.semantic:✅ Neo4j graph database initialization complete
INFO:hello_agents.memory.storage.neo4j_store:✅ Neo4j index creation complete
INFO:hello_agents.memory.types.semantic:✅ Neo4j graph database initialization complete
INFO:hello_agents.memory.types.semantic:🏥 Database health status: Qdrant=✅, Neo4j=✅
INFO:hello_agents.memory.types.semantic:✅ Loaded Chinese spaCy model: zh_core_web_sm
INFO:hello_agents.memory.types.semantic:✅ Loaded English spaCy model: en_core_web_sm
INFO:hello_agents.memory.types.semantic:📚 Available language models: Chinese, English
INFO:hello_agents.memory.types.semantic:Enhanced semantic memory initialization complete (using Qdrant+Neo4j professional databases)
INFO:hello_agents.memory.manager:MemoryManager initialization complete, enabled memory types: ['working', 'episodic', 'semantic']
✅ Tool 'memory' registered.
INFO:hello_agents.memory.storage.qdrant_store:✅ Successfully connected to Qdrant cloud service: https://0c517275-2ad0-4442-8309-11c36dc7e811.us-east-1-1.aws.cloud.qdrant.io:6333
INFO:hello_agents.memory.storage.qdrant_store:✅ Using existing Qdrant collection: rag_knowledge_base
✅ RAG tool initialization successful: namespace=default, collection=rag_knowledge_base
✅ Tool 'rag' registered.
Hello, Zhang San! Nice to meet you. As a Python developer, you must be passionate about programming. If you have any technical questions or need to discuss Python-related topics, feel free to reach out to me anytime. I'll do my best to help you. Is there anything I can help you with right now?
```

## 8.2 Система памяти: предоставление агентам памяти

### 8.2.1 Рабочий процесс системы памяти

Прежде чем перейти к этапу реализации кода, нам необходимо сначала определить рабочий процесс системы памяти. Этот рабочий процесс ссылается на модель памяти в когнитивной науке и сопоставляет каждый когнитивный этап с конкретными техническими компонентами и операциями. Понимание этой взаимосвязи отображения поможет нам в последующей реализации кода.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-3.png" alt="Memory Formation Process" width="90%"/>
  <p>Рисунок 8.3 Когнитивный процесс формирования памяти</p>
</div>

Как показано на рисунке 8.3, согласно исследованиям когнитивной науки, формирование памяти человека проходит следующие этапы:

1. **Кодирование**: преобразование воспринимаемой информации в сохраняемую форму.
2. **Хранение**: Сохранение закодированной информации в системе памяти.
3. **Извлечение**: извлечение соответствующей информации из памяти по мере необходимости.
4. **Консолидация**: преобразование кратковременной памяти в долговременную.
5. **Забывание**: удаление неважной или устаревшей информации.

Основываясь на этом вдохновении, мы разработали полную систему памяти для HelloAgents. Его основная идея состоит в том, чтобы имитировать то, как человеческий мозг обрабатывает различные типы информации, разделяя память на несколько специализированных модулей и создавая интеллектуальный механизм управления. На рисунке 8.4 подробно показан рабочий процесс этой системы, включая ключевые ссылки, такие как добавление памяти, извлечение, консолидация и забывание.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-4.png" alt="Memory System Workflow" width="95%"/>
  <p>Рис. 8.4 Полный рабочий процесс системы памяти HelloAgents</p>
</div>

Наша система памяти состоит из четырех различных типов модулей памяти, каждый из которых оптимизирован для конкретных сценариев применения и жизненного цикла:

Во-первых, это **Рабочая память**, которая играет роль «краткосрочной памяти» агента и в основном используется для хранения контекстной информации текущего разговора. Для обеспечения высокоскоростного доступа и ответа его емкость намеренно ограничена (например, 50 элементов по умолчанию), а его жизненный цикл привязан к одному сеансу, автоматически очищающемуся после завершения сеанса.

Во-вторых, это **Эпизодическая память**, которая отвечает за долговременное хранение конкретных событий взаимодействия и опыта обучения агента. В отличие от рабочей памяти, эпизодическая память содержит богатую контекстную информацию и поддерживает ретроспективный поиск по временным рядам или темам, служа основой для «обзора» агента и изучения прошлого опыта.

Конкретным событиям соответствует **Семантическая память**, которая хранит более абстрактные знания, понятия и правила. Например, для хранения здесь подходят пользовательские предпочтения, полученные в ходе разговоров, инструкции, которым необходимо следовать в течение длительного времени, или точки знания домена. Эта часть памяти имеет высокую стойкость и важность и является ядром для агента для формирования «системы знаний» и выполнения ассоциативных рассуждений.

Наконец, чтобы взаимодействовать со все более богатыми мультимедийными возможностями, мы представили **Перцептивную память**. Этот модуль специально обрабатывает мультимодальную информацию, такую ​​как изображения и аудио, и поддерживает кросс-модальный поиск. Его жизненный цикл динамически управляется в зависимости от важности информации и доступного места для хранения.

### 8.2.2 Быстрый опыт: начните работу с функциями памяти за 30 секунд

Прежде чем углубиться в детали реализации, давайте быстро ознакомимся с основными функциями системы памяти:

```python
from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import MemoryTool

# Create Agent with memory capability
llm = HelloAgentsLLM()
agent = SimpleAgent(name="Memory Assistant", llm=llm)

# Create memory tool
memory_tool = MemoryTool(user_id="user123")
tool_registry = ToolRegistry()
tool_registry.register_tool(memory_tool)
agent.tool_registry = tool_registry

# Experience memory features
print("=== Adding Multiple Memories ===")

# Add first memory
result1 = memory_tool.run("add", content="User Zhang San is a Python developer focusing on machine learning and data analysis", memory_type="semantic", importance=0.8)
print(f"Memory 1: {result1}")

# Add second memory
result2 = memory_tool.run("add", content="Li Si is a frontend engineer skilled in React and Vue.js development", memory_type="semantic", importance=0.7)
print(f"Memory 2: {result2}")

# Add third memory
result3 = memory_tool.run("add", content="Wang Wu is a product manager responsible for user experience design and requirements analysis", memory_type="semantic", importance=0.6)
print(f"Memory 3: {result3}")

print("\n=== Searching Specific Memories ===")
# Search for frontend-related memories
print("🔍 Searching 'frontend engineer':")
result = memory_tool.run("search", query="frontend engineer", limit=3)
print(result)

print("\n=== Memory Summary ===")
result = memory_tool.run("summary")
print(result)
```

### 8.2.3 Подробное объяснение MemoryTool

Теперь давайте применим подход «сверху вниз», начиная с конкретных операций, поддерживаемых MemoryTool, и постепенно углубляясь в базовую реализацию. MemoryTool, как унифицированный интерфейс системы памяти, следует архитектурной схеме «унифицированный вход, распределенная обработка»:

````python
def execute(self, action: str, **kwargs) -> str:
    """Execute memory operation

    Supported operations:
    - add: Add memory (supports 4 types: working/episodic/semantic/perceptual)
    - search: Search memory
    - summary: Get memory summary
    - stats: Get statistics
    - update: Update memory
    - remove: Delete memory
    - forget: Forget memory (multiple strategies)
    - consolidate: Consolidate memory (short-term → long-term)
    - clear_all: Clear all memories
    """

    if action == "add":
        return self._add_memory(**kwargs)
    elif action == "search":
        return self._search_memory(**kwargs)
    elif action == "summary":
        return self._get_summary(**kwargs)
    # ... other operations
````

Это единое`execute`дизайн интерфейса упрощает метод вызова агента. Конкретная операция указывается через`action`параметр, и`**kwargs`позволяет каждой операции иметь разные требования к параметрам. Здесь мы перечислим несколько важных операций:

(1) Операция 1: добавить

-`add`Операция является основой системы памяти. Он имитирует процесс кодирования воспринимаемой информации человеческим мозгом в память. При реализации нам нужно не только хранить содержимое памяти, но и добавлять в каждую память богатую контекстную информацию. Эта информация будет играть важную роль в последующем поиске и управлении.

````python
def _add_memory(
    self,
    content: str = "",
    memory_type: str = "working",
    importance: float = 0.5,
    file_path: str = None,
    modality: str = None,
    **metadata
) -> str:
    """Add memory"""
    try:
        # Ensure session ID exists
        if self.current_session_id is None:
            self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Perceptual memory file support
        if memory_type == "perceptual" and file_path:
            inferred = modality or self._infer_modality(file_path)
            metadata.setdefault("modality", inferred)
            metadata.setdefault("raw_data", file_path)

        # Add session information to metadata
        metadata.update({
            "session_id": self.current_session_id,
            "timestamp": datetime.now().isoformat()
        })

        memory_id = self.memory_manager.add_memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata,
            auto_classify=False
        )

        return f"✅ Memory added (ID: {memory_id[:8]}...)"

    except Exception as e:
        return f"❌ Failed to add memory: {str(e)}"
````

Это в основном реализует три ключевые задачи: автоматическое управление идентификаторами сеансов (обеспечение того, чтобы каждая память имела четкую атрибуцию сеанса), интеллектуальная обработка мультимодальных данных (автоматическое определение типов файлов и сохранение связанных метаданных) и автоматическое дополнение контекстной информации (добавление временных меток и информации о сеансе в каждую память). Среди них,`importance`Параметр (по умолчанию 0,5) используется для обозначения уровня важности памяти в диапазоне значений 0,0–1,0. Этот механизм имитирует оценку человеческим мозгом важности различной информации. Такая конструкция позволяет агенту автоматически различать разговоры из разных периодов времени и предоставлять обширную контекстную информацию для последующего поиска и управления.

Для каждого типа памяти мы приводим разные примеры использования:

```python
# 1. Working Memory - Temporary information, limited capacity
memory_tool.run("add",
    content="User just asked a question about Python functions",
    memory_type="working",
    importance=0.6
)

# 2. Episodic Memory - Specific events and experiences
memory_tool.run("add",
    content="On March 15, 2024, user Zhang San completed their first Python project",
    memory_type="episodic",
    importance=0.8,
    event_type="milestone",
    location="Online learning platform"
)

# 3. Semantic Memory - Abstract knowledge and concepts
memory_tool.run("add",
    content="Python is an interpreted, object-oriented programming language",
    memory_type="semantic",
    importance=0.9,
    knowledge_type="factual"
)

# 4. Perceptual Memory - Multimodal information
memory_tool.run("add",
    content="User uploaded a Python code screenshot containing function definitions",
    memory_type="perceptual",
    importance=0.7,
    modality="image",
    file_path="./uploads/code_screenshot.png"
)
```

(2) Операция 2: поиск

-`search`Операция является основной функцией системы памяти. Ему необходимо быстро найти наиболее релевантный запросу контент среди большого количества воспоминаний. Он включает в себя несколько этапов, таких как семантическое понимание, расчет релевантности и сортировка результатов.

````python
def _search_memory(
    self,
    query: str,
    limit: int = 5,
    memory_types: List[str] = None,
    memory_type: str = None,
    min_importance: float = 0.1
) -> str:
    """Search memory"""
    try:
        # Parameter standardization
        if memory_type and not memory_types:
            memory_types = [memory_type]

        results = self.memory_manager.retrieve_memories(
            query=query,
            limit=limit,
            memory_types=memory_types,
            min_importance=min_importance
        )

        if not results:
            return f"🔍 No memories found related to '{query}'"

        # Format results
        formatted_results = []
        formatted_results.append(f"🔍 Found {len(results)} related memories:")

        for i, memory in enumerate(results, 1):
            memory_type_label = {
                "working": "Working Memory",
                "episodic": "Episodic Memory",
                "semantic": "Semantic Memory",
                "perceptual": "Perceptual Memory"
            }.get(memory.memory_type, memory.memory_type)

            content_preview = memory.content[:80] + "..." if len(memory.content) > 80 else memory.content
            formatted_results.append(
                f"{i}. [{memory_type_label}] {content_preview} (Importance: {memory.importance:.2f})"
            )

        return "\n".join(formatted_results)

    except Exception as e:
        return f"❌ Failed to search memory: {str(e)}"
````

Операция поиска предназначена для поддержки форм параметров как в единственном, так и во множественном числе (`memory_type`и`memory_types`), позволяя пользователям выражать свои потребности наиболее естественным образом. Среди них`min_importance`(по умолчанию 0.1) используется для фильтрации памяти низкого качества. Для использования функции поиска вы можете обратиться к следующему примеру:

```python
# Basic search
result = memory_tool.execute("search", query="Python programming", limit=5)

# Search by specifying memory type
result = memory_tool.execute("search",
    query="learning progress",
    memory_type="episodic",
    limit=3
)

# Multi-type search
result = memory_tool.execute("search",
    query="function definition",
    memory_types=["semantic", "episodic"],
    min_importance=0.5
)
```

(3) Операция 3: забудьте

Механизм забывания является наиболее когнитивно-научной особенностью. Он имитирует процесс выборочного забывания человеческого мозга и поддерживает три стратегии: на основе важности (удаление неважных воспоминаний), на основе времени (удаление устаревших воспоминаний) и на основе емкости (удаление наименее важных воспоминаний, когда объем памяти приближается к пределу).

````python
def _forget(self, strategy: str = "importance_based", threshold: float = 0.1, max_age_days: int = 30) -> str:
    """Forget memories (supports multiple strategies)"""
    try:
        count = self.memory_manager.forget_memories(
            strategy=strategy,
            threshold=threshold,
            max_age_days=max_age_days
        )
        return f"🧹 Forgot {count} memories (strategy: {strategy})"
    except Exception as e:
        return f"❌ Failed to forget memories: {str(e)}"
````

**Использование трёх стратегий забывания:**

```python
# 1. Importance-based forgetting - Delete memories below importance threshold
memory_tool.execute("forget",
    strategy="importance_based",
    threshold=0.2
)

# 2. Time-based forgetting - Delete memories older than specified days
memory_tool.execute("forget",
    strategy="time_based",
    max_age_days=30
)

# 3. Capacity-based forgetting - Delete least important when memory count exceeds limit
memory_tool.execute("forget",
    strategy="capacity_based",
    threshold=0.3
)
```

(4) Операция 4: консолидация

````python
def _consolidate(self, from_type: str = "working", to_type: str = "episodic", importance_threshold: float = 0.7) -> str:
    """Consolidate memories (promote important short-term memories to long-term memories)"""
    try:
        count = self.memory_manager.consolidate_memories(
            from_type=from_type,
            to_type=to_type,
            importance_threshold=importance_threshold,
        )
        return f"🔄 Consolidated {count} memories to long-term memory ({from_type} → {to_type}, threshold={importance_threshold})"
    except Exception as e:
        return f"❌ Failed to consolidate memories: {str(e)}"
````

Операция консолидации основана на концепции консолидации памяти в нейробиологии, моделирующей процесс преобразования человеческим мозгом кратковременной памяти в долговременную. По умолчанию рабочие воспоминания с важностью, превышающей 0,7, преобразуются в эпизодические воспоминания. Этот порог гарантирует, что только действительно важная информация сохранится в долгосрочной перспективе. Весь процесс автоматизирован; пользователям не нужно вручную выбирать определенные воспоминания. Система интеллектуально идентифицирует воспоминания, соответствующие критериям, и выполняет преобразование типов.

**Примеры использования консолидации памяти:**

```python
# Convert important working memories to episodic memories
memory_tool.execute("consolidate",
    from_type="working",
    to_type="episodic",
    importance_threshold=0.7
)

# Convert important episodic memories to semantic memories
memory_tool.execute("consolidate",
    from_type="episodic",
    to_type="semantic",
    importance_threshold=0.8
)
```

Благодаря сотрудничеству этих основных операций MemoryTool создает полную систему управления жизненным циклом памяти. От создания памяти, извлечения, обобщения до забывания, консолидации и управления — она образует замкнутую интеллектуальную систему управления памятью, предоставляющую агенту возможности памяти, по-настоящему человеческие.

### 8.2.4 Подробное объяснение MemoryManager

После понимания дизайна интерфейса MemoryTool давайте углубимся в основную реализацию, чтобы увидеть, как MemoryTool сотрудничает с MemoryManager. Эта многоуровневая конструкция воплощает принцип разделения проблем в разработке программного обеспечения. MemoryTool фокусируется на пользовательском интерфейсе и обработке параметров, в то время как MemoryManager отвечает за основную логику управления памятью.

MemoryTool создает экземпляр MemoryManager во время инициализации и включает различные типы модулей памяти в зависимости от конфигурации. Такая конструкция позволяет пользователям выбирать, какие типы памяти включать в зависимости от конкретных потребностей, обеспечивая функциональную полноту и избегая ненужного потребления ресурсов.

````python
class MemoryTool(Tool):
    """Memory tool - Provides memory functionality for Agent"""

    def __init__(
        self,
        user_id: str = "default_user",
        memory_config: MemoryConfig = None,
        memory_types: List[str] = None
    ):
        super().__init__(
            name="memory",
            description="Memory tool - Can store and retrieve conversation history, knowledge, and experience"
        )

        # Initialize memory manager
        self.memory_config = memory_config or MemoryConfig()
        self.memory_types = memory_types or ["working", "episodic", "semantic"]

        self.memory_manager = MemoryManager(
            config=self.memory_config,
            user_id=user_id,
            enable_working="working" in self.memory_types,
            enable_episodic="episodic" in self.memory_types,
            enable_semantic="semantic" in self.memory_types,
            enable_perceptual="perceptual" in self.memory_types
        )
````

MemoryManager, являясь основным координатором системы памяти, отвечает за управление различными типами модулей памяти и обеспечивает единый рабочий интерфейс.

````python
class MemoryManager:
    """Memory manager - Unified memory operation interface"""

    def __init__(
        self,
        config: Optional[MemoryConfig] = None,
        user_id: str = "default_user",
        enable_working: bool = True,
        enable_episodic: bool = True,
        enable_semantic: bool = True,
        enable_perceptual: bool = False
    ):
        self.config = config or MemoryConfig()
        self.user_id = user_id

        # Initialize storage and retrieval components
        self.store = MemoryStore(self.config)
        self.retriever = MemoryRetriever(self.store, self.config)

        # Initialize various types of memory
        self.memory_types = {}

        if enable_working:
            self.memory_types['working'] = WorkingMemory(self.config, self.store)

        if enable_episodic:
            self.memory_types['episodic'] = EpisodicMemory(self.config, self.store)

        if enable_semantic:
            self.memory_types['semantic'] = SemanticMemory(self.config, self.store)

        if enable_perceptual:
            self.memory_types['perceptual'] = PerceptualMemory(self.config, self.store)
````

### 8.2.5 Четыре типа памяти

Теперь давайте углубимся в конкретную реализацию четырех типов памяти. Каждый тип памяти имеет свои уникальные характеристики и сценарии применения:

(1) Рабочая память

Рабочая память — наиболее активная часть системы памяти. Он отвечает за хранение временной информации в текущем сеансе разговора. При проектировании рабочей памяти основное внимание уделяется быстрому доступу и автоматической очистке, что обеспечивает скорость отклика системы и эффективность использования ресурсов.

Рабочая память представляет собой чистое решение для хранения данных в оперативной памяти в сочетании с механизмом TTL (Time To Live) для автоматической очистки. Преимуществом этой конструкции является чрезвычайно высокая скорость доступа, но это также означает, что содержимое рабочей памяти будет потеряно после перезагрузки системы. Эта характеристика идеально соответствует позиционированию рабочей памяти: хранению временной и энергозависимой информации.

````python
class WorkingMemory:
    """Working memory implementation
    Features:
    - Limited capacity (default 50 items) + TTL automatic cleanup
    - Pure in-memory storage, extremely fast access
    - Hybrid retrieval: TF-IDF vectorization + keyword matching
    """

    def __init__(self, config: MemoryConfig):
        self.max_capacity = config.working_memory_capacity or 50
        self.max_age_minutes = config.working_memory_ttl or 60
        self.memories = []

    def add(self, memory_item: MemoryItem) -> str:
        """Add working memory"""
        self._expire_old_memories()  # Expiration cleanup

        if len(self.memories) >= self.max_capacity:
            self._remove_lowest_priority_memory()  # Capacity management

        self.memories.append(memory_item)
        return memory_item.id

    def retrieve(self, query: str, limit: int = 5, **kwargs) -> List[MemoryItem]:
        """Hybrid retrieval: TF-IDF vectorization + keyword matching"""
        self._expire_old_memories()

        # Try TF-IDF vector retrieval
        vector_scores = self._try_tfidf_search(query)

        # Calculate comprehensive score
        scored_memories = []
        for memory in self.memories:
            vector_score = vector_scores.get(memory.id, 0.0)
            keyword_score = self._calculate_keyword_score(query, memory.content)

            # Hybrid scoring
            base_relevance = vector_score * 0.7 + keyword_score * 0.3 if vector_score > 0 else keyword_score
            time_decay = self._calculate_time_decay(memory.timestamp)
            importance_weight = 0.8 + (memory.importance * 0.4)

            final_score = base_relevance * time_decay * importance_weight
            if final_score > 0:
                scored_memories.append((final_score, memory))

        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for _, memory in scored_memories[:limit]]
````

При извлечении из рабочей памяти используется гибридная стратегия извлечения. Сначала он пытается использовать векторизацию TF-IDF для семантического поиска, а если это не удается, он возвращается к сопоставлению ключевых слов. Такая конструкция обеспечивает надежные услуги поиска в различных средах. Алгоритм оценки сочетает в себе семантическое сходство, затухание во времени и вес важности. Окончательная формула оценки:`(similarity × time decay) × (0.8 + importance × 0.4)`.

(2) Эпизодическая память

Эпизодическая память отвечает за хранение конкретных событий и переживаний. Его дизайн направлен на поддержание целостности событий и отношений временной последовательности. В эпизодической памяти используется гибридное решение хранения SQLite + Qdrant. SQLite отвечает за хранение структурированных данных и сложных запросов, а Qdrant отвечает за эффективный векторный поиск.

````python
class EpisodicMemory:
    """Episodic memory implementation
    Features:
    - SQLite+Qdrant hybrid storage architecture
    - Supports time series and session-level retrieval
    - Structured filtering + semantic vector retrieval
    """

    def __init__(self, config: MemoryConfig):
        self.doc_store = SQLiteDocumentStore(config.database_path)
        self.vector_store = QdrantVectorStore(config.qdrant_url, config.qdrant_api_key)
        self.embedder = create_embedding_model_with_fallback()
        self.sessions = {}  # Session index

    def add(self, memory_item: MemoryItem) -> str:
        """Add episodic memory"""
        # Create episode object
        episode = Episode(
            episode_id=memory_item.id,
            session_id=memory_item.metadata.get("session_id", "default"),
            timestamp=memory_item.timestamp,
            content=memory_item.content,
            context=memory_item.metadata
        )

        # Update session index
        session_id = episode.session_id
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(episode.episode_id)

        # Persistent storage (SQLite + Qdrant)
        self._persist_episode(episode)
        return memory_item.id

    def retrieve(self, query: str, limit: int = 5, **kwargs) -> List[MemoryItem]:
        """Hybrid retrieval: structured filtering + semantic vector retrieval"""
        # 1. Structured pre-filtering (time range, importance, etc.)
        candidate_ids = self._structured_filter(**kwargs)

        # 2. Vector semantic retrieval
        hits = self._vector_search(query, limit * 5, kwargs.get("user_id"))

        # 3. Comprehensive scoring and sorting
        results = []
        for hit in hits:
            if self._should_include(hit, candidate_ids, kwargs):
                score = self._calculate_episode_score(hit)
                memory_item = self._create_memory_item(hit)
                results.append((score, memory_item))

        results.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in results[:limit]]

    def _calculate_episode_score(self, hit) -> float:
        """Episodic memory scoring algorithm"""
        vec_score = float(hit.get("score", 0.0))
        recency_score = self._calculate_recency(hit["metadata"]["timestamp"])
        importance = hit["metadata"].get("importance", 0.5)

        # Scoring formula: (vector similarity × 0.8 + temporal recency × 0.2) × importance weight
        base_relevance = vec_score * 0.8 + recency_score * 0.2
        importance_weight = 0.8 + (importance * 0.4)

        return base_relevance * importance_weight
````

Реализация извлечения эпизодической памяти демонстрирует сложный многофакторный механизм оценки. Он не только учитывает семантическое сходство, но также учитывает временную новизну, в конечном итоге скорректированную по весу важности. Формула подсчета очков:`(vector similarity × 0.8 + temporal recency × 0.2) × (0.8 + importance × 0.4)`, гарантируя, что результаты поиска релевантны как семантически, так и во времени.

(3) Семантическая память

Семантическая память – самая сложная часть системы памяти. Он отвечает за хранение абстрактных понятий, правил и знаний. При проектировании семантической памяти основное внимание уделяется структурированному представлению знаний и возможностям интеллектуального рассуждения. Семантическая память использует гибридную архитектуру графовой базы данных Neo4j и векторной базы данных Qdrant. Такая конструкция позволяет системе выполнять как быстрый семантический поиск, так и сложные реляционные рассуждения с использованием графов знаний.

````python
class SemanticMemory(BaseMemory):
    """Semantic memory implementation

    Features:
    - Uses HuggingFace Chinese pre-trained models for text embedding
    - Vector retrieval for fast similarity matching
    - Knowledge graph storage for entities and relationships
    - Hybrid retrieval strategy: vector + graph + semantic reasoning
    """

    def __init__(self, config: MemoryConfig, storage_backend=None):
        super().__init__(config, storage_backend)

        # Embedding model (unified provision)
        self.embedding_model = get_text_embedder()

        # Professional database storage
        self.vector_store = QdrantConnectionManager.get_instance(**qdrant_config)
        self.graph_store = Neo4jGraphStore(**neo4j_config)

        # Entity and relation cache
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []

        # NLP processor (supports Chinese and English)
        self.nlp = self._init_nlp()
````

Процесс добавления семантической памяти воплощает в себе полный рабочий процесс построения графа знаний. Система не только хранит содержимое памяти, но также автоматически извлекает сущности и связи для построения структурированных представлений знаний:

```python
def add(self, memory_item: MemoryItem) -> str:
    """Add semantic memory"""
    # 1. Generate text embedding
    embedding = self.embedding_model.encode(memory_item.content)

    # 2. Extract entities and relations
    entities = self._extract_entities(memory_item.content)
    relations = self._extract_relations(memory_item.content, entities)

    # 3. Store to Neo4j graph database
    for entity in entities:
        self._add_entity_to_graph(entity, memory_item)

    for relation in relations:
        self._add_relation_to_graph(relation, memory_item)

    # 4. Store to Qdrant vector database
    metadata = {
        "memory_id": memory_item.id,
        "entities": [e.entity_id for e in entities],
        "entity_count": len(entities),
        "relation_count": len(relations)
    }

    self.vector_store.add_vectors(
        vectors=[embedding.tolist()],
        metadata=[metadata],
        ids=[memory_item.id]
    )
```

Извлечение семантической памяти реализует гибридную стратегию поиска, сочетающую в себе возможности семантического понимания векторного поиска и возможности реляционного рассуждения поиска графов:

```python
def retrieve(self, query: str, limit: int = 5, **kwargs) -> List[MemoryItem]:
    """Retrieve semantic memory"""
    # 1. Vector retrieval
    vector_results = self._vector_search(query, limit * 2, user_id)

    # 2. Graph retrieval
    graph_results = self._graph_search(query, limit * 2, user_id)

    # 3. Hybrid ranking
    combined_results = self._combine_and_rank_results(
        vector_results, graph_results, query, limit
    )

    return combined_results[:limit]
```

Гибридный алгоритм ранжирования использует механизм многофакторной оценки:

```python
def _combine_and_rank_results(self, vector_results, graph_results, query, limit):
    """Hybrid ranking of results"""
    combined = {}

    # Merge vector and graph retrieval results
    for result in vector_results:
        combined[result["memory_id"]] = {
            **result,
            "vector_score": result.get("score", 0.0),
            "graph_score": 0.0
        }

    for result in graph_results:
        memory_id = result["memory_id"]
        if memory_id in combined:
            combined[memory_id]["graph_score"] = result.get("similarity", 0.0)
        else:
            combined[memory_id] = {
                **result,
                "vector_score": 0.0,
                "graph_score": result.get("similarity", 0.0)
            }

    # Calculate hybrid score
    for memory_id, result in combined.items():
        vector_score = result["vector_score"]
        graph_score = result["graph_score"]
        importance = result.get("importance", 0.5)

        # Base relevance score
        base_relevance = vector_score * 0.7 + graph_score * 0.3

        # Importance weight [0.8, 1.2]
        importance_weight = 0.8 + (importance * 0.4)

        # Final score: similarity * importance weight
        combined_score = base_relevance * importance_weight
        result["combined_score"] = combined_score

    # Sort and return
    sorted_results = sorted(
        combined.values(),
        key=lambda x: x["combined_score"],
        reverse=True
    )

    return sorted_results[:limit]
```

Формула оценки семантической памяти:`(vector similarity × 0.7 + graph similarity × 0.3) × (0.8 + importance × 0.4)`. Основная идея этого дизайна:

- **Вес векторного поиска (0,7)**: Семантическое сходство является основным фактором, гарантирующим семантическое отношение результатов поиска к запросу.
- **Вес получения графа (0,3)**: Реляционное рассуждение как дополнение, обнаруживающее неявные связи между понятиями.
- **Диапазон весов важности [0,8, 1,2]**: позволяет избежать чрезмерного влияния важности на ранжирование сходства, сохраняя точность поиска.

(4) Перцептивная память

Перцептивная память поддерживает хранение и извлечение данных в различных модальностях, таких как текст, изображения и аудио. Он использует стратегию хранения с разделением модальностей, создавая независимые векторные коллекции для данных разных модальностей. Такая конструкция позволяет избежать проблем несоответствия размеров, обеспечивая при этом точность поиска:

````python
class PerceptualMemory(BaseMemory):
    """Perceptual memory implementation

    Features:
    - Supports multimodal data (text, images, audio, etc.)
    - Cross-modal similarity search
    - Semantic understanding of perceptual data
    - Supports content generation and retrieval
    """

    def __init__(self, config: MemoryConfig, storage_backend=None):
        super().__init__(config, storage_backend)

        # Multimodal encoders
        self.text_embedder = get_text_embedder()
        self._clip_model = self._init_clip_model()  # Image encoding
        self._clap_model = self._init_clap_model()  # Audio encoding

        # Modality-separated vector storage
        self.vector_stores = {
            "text": QdrantConnectionManager.get_instance(
                collection_name="perceptual_text",
                vector_size=self.vector_dim
            ),
            "image": QdrantConnectionManager.get_instance(
                collection_name="perceptual_image",
                vector_size=self._image_dim
            ),
            "audio": QdrantConnectionManager.get_instance(
                collection_name="perceptual_audio",
                vector_size=self._audio_dim
            )
        }
````

Перцептивное извлечение памяти поддерживает как одномодальный, так и кросс-модальный режимы. Одномодальный поиск использует специализированные кодеры для точного сопоставления, тогда как кросс-модальный поиск требует более сложных механизмов семантического выравнивания:

```python
def retrieve(self, query: str, limit: int = 5, **kwargs) -> List[MemoryItem]:
    """Retrieve perceptual memory (can filter modality; same-modality vector retrieval + time/importance fusion)"""
    user_id = kwargs.get("user_id")
    target_modality = kwargs.get("target_modality")
    query_modality = kwargs.get("query_modality", target_modality or "text")

    # Same-modality vector retrieval
    try:
        query_vector = self._encode_data(query, query_modality)
        store = self._get_vector_store_for_modality(target_modality or query_modality)

        where = {"memory_type": "perceptual"}
        if user_id:
            where["user_id"] = user_id
        if target_modality:
            where["modality"] = target_modality

        hits = store.search_similar(
            query_vector=query_vector,
            limit=max(limit * 5, 20),
            where=where
        )
    except Exception:
        hits = []

    # Fusion ranking (vector similarity + temporal recency + importance weight)
    results = []
    for hit in hits:
        vector_score = float(hit.get("score", 0.0))
        recency_score = self._calculate_recency_score(hit["metadata"]["timestamp"])
        importance = hit["metadata"].get("importance", 0.5)

        # Scoring algorithm
        base_relevance = vector_score * 0.8 + recency_score * 0.2
        importance_weight = 0.8 + (importance * 0.4)
        combined_score = base_relevance * importance_weight

        results.append((combined_score, self._create_memory_item(hit)))

    results.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in results[:limit]]
```

Формула оценки перцептивной памяти:`(vector similarity × 0.8 + temporal recency × 0.2) × (0.8 + importance × 0.4)`. Механизм оценки перцептивной памяти также поддерживает кросс-модальный поиск, обеспечивая семантическое выравнивание данных различной модальности, таких как текст, изображения и аудио, через единое векторное пространство. При выполнении кросс-модального поиска система автоматически корректирует веса оценок, чтобы обеспечить разнообразие и точность результатов поиска. Кроме того, расчет временной новизны в перцептивной памяти использует модель экспоненциального затухания:

```python
def _calculate_recency_score(self, timestamp: str) -> float:
    """Calculate temporal recency score"""
    try:
        memory_time = datetime.fromisoformat(timestamp)
        current_time = datetime.now()
        age_hours = (current_time - memory_time).total_seconds() / 3600

        # Exponential decay: maintain high score within 24 hours, then gradually decay
        decay_factor = 0.1  # Decay coefficient
        recency_score = math.exp(-decay_factor * age_hours / 24)

        return max(0.1, recency_score)  # Maintain minimum base score of 0.1
    except Exception:
        return 0.5  # Default medium score
```

Эта модель временного затухания имитирует кривую забывания в человеческой памяти, гарантируя, что система перцептивной памяти может расставить приоритеты в извлечении более актуального во времени содержимого памяти.

## 8.3 Система RAG: улучшение поиска знаний

### 8.3.1 Основы RAG

Прежде чем погрузиться в реализацию HelloAgents в системе RAG, давайте сначала разберемся с основными концепциями, историей развития и основными принципами технологии RAG. Поскольку этот текст создан не на основе RAG, мы лишь кратко рассмотрим здесь соответствующие концепции, чтобы лучше понять технические решения и инновации в проектировании систем.

(1) Что такое РАГ?

Поисково-дополненная генерация (RAG) — это технология, сочетающая поиск информации и генерацию текста. Его основная идея такова: прежде чем генерировать ответ, сначала извлеките соответствующую информацию из внешней базы знаний, затем предоставьте полученную информацию в качестве контекста для большой языковой модели, тем самым генерируя более точные и надежные ответы.

Таким образом, фразу «Поисковая дополненная генерация» можно разбить на три слова. **Извлечение** означает запрос соответствующего контента из базы знаний; **Дополненный** означает интеграцию результатов поиска в подсказки для облегчения создания модели; **Генерация** выводит ответы, сочетающие точность и прозрачность.

(2) Основной рабочий процесс

Полный рабочий процесс приложения RAG в основном разделен на два основных этапа. На **этапе подготовки данных** система объединяет внешние знания в извлекаемую базу данных посредством **извлечения данных**, **сегментации текста** и **векторизации**. Впоследствии, на **этапе** приложения**, система отвечает на **запросы** пользователя, **извлекает** соответствующую информацию из базы данных, **вводит ее в подсказку** и, наконец, управляет большой языковой моделью для **генерации ответов**.

(3) История развития

Первый этап: Наивная РАГ (2020-2021). Это зачаточная стадия технологии RAG с прямым и простым процессом, обычно называемым режимом «Извлечение-Чтение». **Метод поиска**: в основном опирается на традиционные алгоритмы сопоставления ключевых слов, такие как`TF-IDF`или`BM25`. Эти методы рассчитывают частоту терминов и частоту документов для оценки релевантности, обеспечивая хороший эффект буквального соответствия, но затрудняя понимание семантического сходства. **Режим генерации**: содержимое полученного документа напрямую объединяется с контекстом приглашения без обработки, а затем отправляется в модель генерации.

Второй этап: Advanced RAG (2022-2023 гг.). С развитием векторных баз данных и технологий встраивания текста RAG вступила в стадию быстрого развития. Исследователи и разработчики внедрили большое количество методов оптимизации на различных этапах «извлечения» и «генерации». **Метод поиска**: переход к семантическому поиску на основе **плотного внедрения**. Преобразуя текст в многомерные векторы, модель может понимать и сопоставлять семантическое сходство, а не только ключевые слова. **Режим генерации**: добавлено множество методов оптимизации, таких как переписывание запросов, разбиение документов на фрагменты, изменение ранжирования и т. д.

Третий этап: Модульная ВЕТОШЬ (2023-настоящее время). Опираясь на передовые системы ТРЯПКИ, современные системы ТРЯПКИ продолжают развиваться в направлении модульности, автоматизации и интеллекта. Различные части системы разработаны как подключаемые, компонуемые независимые модули для адаптации к более разнообразным и сложным сценариям применения. ** Методы поиска **: такие как гибридный поиск, расширение с несколькими запросами, гипотетическое встраивание документов и т. д. ** Режимы генерации **: логическое мышление, саморефлексия и коррекция и т. д.

### 8.3.2 Принцип работы системы RAG

Прежде чем углубиться в детали реализации, мы можем использовать блок-схему, чтобы обрисовать полный рабочий процесс системы RAG HelloAgents:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-5.png" alt="RAG System Core Principle" width="85%"/>
  <p>Рисунок 8.5 Основной принцип работы системы RAG</p>
</div>

Как показано на рисунке 8.5, он демонстрирует два основных режима работы системы RAG:
1. ** Рабочий процесс обработки данных **: обработка и хранение документов знаний. Здесь мы принимаем инструмент`Markitdown`, с дизайнерской идеей равномерного преобразования всех входящих внешних источников знаний в формат Markdown для обработки.
2. ** Рабочий процесс запроса и генерации **: получение релевантной информации на основе запросов и генерация ответов.

### 8.3.3 Быстрый опыт: начните работу с функциями RAG за 30 секунд

Давайте быстро ознакомимся с основными функциями системы RAG:

```python
from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import RAGTool

# Create Agent with RAG capability
llm = HelloAgentsLLM()
agent = SimpleAgent(name="Knowledge Assistant", llm=llm)

# Create RAG tool
rag_tool = RAGTool(
    knowledge_base_path="./knowledge_base",
    collection_name="test_collection",
    rag_namespace="test"
)

tool_registry = ToolRegistry()
tool_registry.register_tool(rag_tool)
agent.tool_registry = tool_registry

# Experience RAG features
# Add first knowledge
result1 = rag_tool.execute("add_text",
    text="Python is a high-level programming language first released by Guido van Rossum in 1991. Python's design philosophy emphasizes code readability and concise syntax.",
    document_id="python_intro")
print(f"Knowledge 1: {result1}")

# Add second knowledge
result2 = rag_tool.execute("add_text",
    text="Machine learning is a branch of artificial intelligence that uses algorithms to enable computers to learn patterns from data. It mainly includes three types: supervised learning, unsupervised learning, and reinforcement learning.",
    document_id="ml_basics")
print(f"Knowledge 2: {result2}")

# Add third knowledge
result3 = rag_tool.execute("add_text",
    text="RAG (Retrieval-Augmented Generation) is an AI technology that combines information retrieval and text generation. It enhances the generation capability of large language models by retrieving relevant knowledge.",
    document_id="rag_concept")
print(f"Knowledge 3: {result3}")


print("\n=== Search Knowledge ===")
result = rag_tool.execute("search",
    query="History of Python programming language",
    limit=3,
    min_score=0.1
)
print(result)

print("\n=== Knowledge Base Statistics ===")
result = rag_tool.execute("stats")
print(result)
```

Далее мы углубимся в конкретную реализацию Rag-системы HELLOAGENTS.

### 8.3.4 Проектирование архитектуры системы RAG

В этом разделе мы используем подход, отличный от объяснения системы памяти. Потому что`Memory_tool`— это систематическая реализация, тогда как RAG в нашем проекте определяется как инструмент, который можно организовать в виде конвейера. Базовую архитектуру нашей системы RAG можно резюмировать как «пятиуровневый семиэтапный» шаблон проектирования:

```
User Layer: RAGTool unified interface
  ↓
Application Layer: Intelligent Q&A, search, management
  ↓
Processing Layer: Document parsing, chunking, vectorization
  ↓
Storage Layer: Vector database, document storage
  ↓
Foundation Layer: Embedding model, LLM, database
```

Преимущество этой многослойной конструкции заключается в том, что каждый слой может быть независимо оптимизирован и заменен при сохранении стабильности всей системы. Например, вы можете легко переключить модель встраивания с преобразователей предложений на Bailian API, не затрагивая бизнес-логику верхнего уровня. Аналогичным образом, код рабочего процесса обработки является полностью многоразовым, и вы также можете выбрать нужные вам детали и поместить их в свой собственный проект. RAGTool служит единой точкой входа в систему RAG, обеспечивая краткий интерфейс API.

````python
class RAGTool(Tool):
    """RAG tool

    Provides complete RAG capabilities:
    - Add multi-format documents (PDF, Office, images, audio, etc.)
    - Intelligent retrieval and recall
    - LLM-enhanced Q&A
    - Knowledge base management
    """

    def __init__(
        self,
        knowledge_base_path: str = "./knowledge_base",
        qdrant_url: str = None,
        qdrant_api_key: str = None,
        collection_name: str = "rag_knowledge_base",
        rag_namespace: str = "default"
    ):
        # Initialize RAG pipeline
        self._pipelines: Dict[str, Dict[str, Any]] = {}
        self.llm = HelloAgentsLLM()

        # Create default pipeline
        default_pipeline = create_rag_pipeline(
            qdrant_url=self.qdrant_url,
            qdrant_api_key=self.qdrant_api_key,
            collection_name=self.collection_name,
            rag_namespace=self.rag_namespace
        )
        self._pipelines[self.rag_namespace] = default_pipeline
````

Весь рабочий процесс обработки выглядит следующим образом:
```
Any format document → MarkItDown conversion → Markdown text → Intelligent chunking → Vectorization → Storage and retrieval
```

(1) Мультимодальная загрузка документов

Одним из основных преимуществ системы RAG является ее мощная мультимодальная возможность обработки документов. Система использует MarkItDown в качестве унифицированного механизма преобразования документов, поддерживающего почти все распространенные форматы документов. MarkItDown - это универсальный инструмент преобразования документов с открытым исходным кодом от Microsoft. Это основной компонент Rag-системы HelloAgents, отвечающий за равномерное преобразование документов любого формата в структурированный текст Markdown. Независимо от того, является ли ввод PDF, Word, Excel, изображения или аудио, он в конечном итоге будет преобразован в стандартный формат Markdown, а затем войдет в унифицированный рабочий процесс фрагментации, векторизации и хранения.

```python
def _convert_to_markdown(path: str) -> str:
    """
    Universal document reader using MarkItDown with enhanced PDF processing.
    Core function: Convert documents of any format to Markdown text

    Supported formats:
    - Documents: PDF, Word, Excel, PowerPoint
    - Images: JPG, PNG, GIF (via OCR)
    - Audio: MP3, WAV, M4A (via transcription)
    - Text: TXT, CSV, JSON, XML, HTML
    - Code: Python, JavaScript, Java, etc.
    """
    if not os.path.exists(path):
        return ""

    # Use enhanced processing for PDF files
    ext = (os.path.splitext(path)[1] or '').lower()
    if ext == '.pdf':
        return _enhanced_pdf_processing(path)

    # Use MarkItDown unified conversion for other formats
    md_instance = _get_markitdown_instance()
    if md_instance is None:
        return _fallback_text_reader(path)

    try:
        result = md_instance.convert(path)
        markdown_text = getattr(result, "text_content", None)
        if isinstance(markdown_text, str) and markdown_text.strip():
            print(f"[RAG] MarkItDown conversion successful: {path} -> {len(markdown_text)} chars Markdown")
            return markdown_text
        return ""
    except Exception as e:
        print(f"[WARNING] MarkItDown conversion failed {path}: {e}")
        return _fallback_text_reader(path)
```

(2) Интеллектуальная стратегия распределения

После конвертации MarkItDown все документы объединяются в стандартный формат Markdown. Это обеспечивает структурированную основу для последующего интеллектуального разделения на фрагменты. HelloAgents реализует интеллектуальную стратегию фрагментации специально для формата Markdown, полностью используя структурированные характеристики Markdown для точной сегментации.

Рабочий процесс разбиения на фрагменты с учетом структуры Markdown:

```
Standard Markdown text → Heading hierarchy parsing → Paragraph semantic segmentation → Token calculation chunking → Overlap strategy optimization → Vectorization preparation
       ↓                ↓              ↓            ↓           ↓            ↓
   Unified format      #/##/###      Semantic boundary  Size control  Information continuity  Embedding vector
   Clear structure     Hierarchy recognition  Integrity guarantee  Retrieval optimization  Context preservation  Similarity matching
```

Поскольку все документы преобразованы в формат Markdown, система может использовать структуру заголовков Markdown (#, ##, ### и т. д.) для точной семантической сегментации:

```python
def _split_paragraphs_with_headings(text: str) -> List[Dict]:
    """Split paragraphs based on heading hierarchy, maintaining semantic integrity"""
    lines = text.splitlines()
    heading_stack: List[str] = []
    paragraphs: List[Dict] = []
    buf: List[str] = []
    char_pos = 0

    def flush_buf(end_pos: int):
        if not buf:
            return
        content = "\n".join(buf).strip()
        if not content:
            return
        paragraphs.append({
            "content": content,
            "heading_path": " > ".join(heading_stack) if heading_stack else None,
            "start": max(0, end_pos - len(content)),
            "end": end_pos,
        })

    for ln in lines:
        raw = ln
        if raw.strip().startswith("#"):
            # Process heading line
            flush_buf(char_pos)
            level = len(raw) - len(raw.lstrip('#'))
            title = raw.lstrip('#').strip()

            if level <= 0:
                level = 1
            if level <= len(heading_stack):
                heading_stack = heading_stack[:level-1]
            heading_stack.append(title)

            char_pos += len(raw) + 1
            continue

        # Accumulate paragraph content
        if raw.strip() == "":
            flush_buf(char_pos)
            buf = []
        else:
            buf.append(raw)
        char_pos += len(raw) + 1

    flush_buf(char_pos)

    if not paragraphs:
        paragraphs = [{"content": text, "heading_path": None, "start": 0, "end": len(text)}]

    return paragraphs
```

На основе сегментации абзацев Markdown система дополнительно выполняет интеллектуальное разбиение на блоки на основе количества токенов. Поскольку входные данные уже представляют собой структурированный текст Markdown, система может более точно контролировать границы фрагментов, гарантируя, что каждый фрагмент подходит для обработки векторизации и сохраняет целостность структуры Markdown:

```python
def _chunk_paragraphs(paragraphs: List[Dict], chunk_tokens: int, overlap_tokens: int) -> List[Dict]:
    """Intelligent chunking based on token count"""
    chunks: List[Dict] = []
    cur: List[Dict] = []
    cur_tokens = 0
    i = 0

    while i < len(paragraphs):
        p = paragraphs[i]
        p_tokens = _approx_token_len(p["content"]) or 1

        if cur_tokens + p_tokens <= chunk_tokens or not cur:
            cur.append(p)
            cur_tokens += p_tokens
            i += 1
        else:
            # Generate current chunk
            content = "\n\n".join(x["content"] for x in cur)
            start = cur[0]["start"]
            end = cur[-1]["end"]
            heading_path = next((x["heading_path"] for x in reversed(cur) if x.get("heading_path")), None)

            chunks.append({
                "content": content,
                "start": start,
                "end": end,
                "heading_path": heading_path,
            })

            # Build overlap section
            if overlap_tokens > 0 and cur:
                kept: List[Dict] = []
                kept_tokens = 0
                for x in reversed(cur):
                    t = _approx_token_len(x["content"]) or 1
                    if kept_tokens + t > overlap_tokens:
                        break
                    kept.append(x)
                    kept_tokens += t
                cur = list(reversed(kept))
                cur_tokens = kept_tokens
            else:
                cur = []
                cur_tokens = 0

    # Process last chunk
    if cur:
        content = "\n\n".join(x["content"] for x in cur)
        start = cur[0]["start"]
        end = cur[-1]["end"]
        heading_path = next((x["heading_path"] for x in reversed(cur) if x.get("heading_path")), None)

        chunks.append({
            "content": content,
            "start": start,
            "end": end,
            "heading_path": heading_path,
        })

    return chunks
```

В то же время, для совместимости с разными языками, система реализует алгоритм оценки токенов для смешанного китайско-английского текста, что имеет решающее значение для точного контроля размера фрагмента:

```python
def _approx_token_len(text: str) -> int:
    """Approximate token length estimation, supports Chinese-English mixed text"""
    # CJK characters counted as 1 token each
    cjk = sum(1 for ch in text if _is_cjk(ch))
    # Other characters counted by whitespace tokenization
    non_cjk_tokens = len([t for t in text.split() if t])
    return cjk + non_cjk_tokens

def _is_cjk(ch: str) -> bool:
    """Determine if character is CJK"""
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF or  # CJK Unified Ideographs
        0x3400 <= code <= 0x4DBF or  # CJK Extension A
        0x20000 <= code <= 0x2A6DF or # CJK Extension B
        0x2A700 <= code <= 0x2B73F or # CJK Extension C
        0x2B740 <= code <= 0x2B81F or # CJK Extension D
        0x2B820 <= code <= 0x2CEAF or # CJK Extension E
        0xF900 <= code <= 0xFAFF      # CJK Compatibility Ideographs
    )
```

(3) Унифицированное встраивание и векторное хранилище

Модель встраивания является ядром системы RAG. Он отвечает за преобразование текста в многомерные векторы, позволяя компьютерам понимать и сравнивать семантическое сходство текста. Возможность извлечения системы RAG во многом зависит от качества модели встраивания и эффективности векторного хранения. HelloAgents реализует унифицированный интерфейс встраивания. В демонстрационных целях мы используем здесь API Bailian. Если вы еще не настроены, вы можете переключиться на локальный`all-MiniLM-L6-v2`модель. Если оба решения не поддерживаются, алгоритм TF-IDF также настраивается как запасной вариант. При фактическом использовании вы можете заменить его желаемой моделью или API или попытаться расширить содержимое фреймворка~

```python
def index_chunks(
    store = None,
    chunks: List[Dict] = None,
    cache_db: Optional[str] = None,
    batch_size: int = 64,
    rag_namespace: str = "default"
) -> None:
    """
    Index markdown chunks with unified embedding and Qdrant storage.
    Uses Bailian API with fallback to sentence-transformers.
    """
    if not chunks:
        print("[RAG] No chunks to index")
        return

    # Use unified embedding model
    embedder = get_text_embedder()
    dimension = get_dimension(384)

    # Create default Qdrant storage
    if store is None:
        store = _create_default_vector_store(dimension)
        print(f"[RAG] Created default Qdrant store with dimension {dimension}")

    # Preprocess Markdown text for better embedding quality
    processed_texts = []
    for c in chunks:
        raw_content = c["content"]
        processed_content = _preprocess_markdown_for_embedding(raw_content)
        processed_texts.append(processed_content)

    print(f"[RAG] Embedding start: total_texts={len(processed_texts)} batch_size={batch_size}")

    # Batch encoding
    vecs: List[List[float]] = []
    for i in range(0, len(processed_texts), batch_size):
        part = processed_texts[i:i+batch_size]
        try:
            # Use unified embedder (handles caching internally)
            part_vecs = embedder.encode(part)

            # Standardize to List[List[float]] format
            if not isinstance(part_vecs, list):
                if hasattr(part_vecs, "tolist"):
                    part_vecs = [part_vecs.tolist()]
                else:
                    part_vecs = [list(part_vecs)]

            # Process vector format and dimension
            for v in part_vecs:
                try:
                    if hasattr(v, "tolist"):
                        v = v.tolist()
                    v_norm = [float(x) for x in v]

                    # Dimension check and adjustment
                    if len(v_norm) != dimension:
                        print(f"[WARNING] Vector dimension anomaly: expected {dimension}, actual {len(v_norm)}")
                        if len(v_norm) < dimension:
                            v_norm.extend([0.0] * (dimension - len(v_norm)))
                        else:
                            v_norm = v_norm[:dimension]

                    vecs.append(v_norm)
                except Exception as e:
                    print(f"[WARNING] Vector conversion failed: {e}, using zero vector")
                    vecs.append([0.0] * dimension)

        except Exception as e:
            print(f"[WARNING] Batch {i} encoding failed: {e}")
            # Implement retry mechanism
            # ... retry logic ...

        print(f"[RAG] Embedding progress: {min(i+batch_size, len(processed_texts))}/{len(processed_texts)}")
```

### 8.3.5 Расширенные стратегии поиска

Возможности поиска информации системы RAG являются ее основной конкурентоспособностью. В практических приложениях между запросами пользователей и фактическим содержимым документов могут возникать различия в формулировках, в результате чего соответствующие документы не извлекаются. Чтобы решить эту проблему, HelloAgents реализует три взаимодополняющие расширенные стратегии поиска: расширение нескольких запросов (MQE), встраивание гипотетических документов (HyDE) и унифицированную структуру расширенного поиска.

(1) Расширение нескольких запросов (MQE)

Расширение нескольких запросов (MQE) — это метод, который улучшает извлечение данных за счет создания семантически эквивалентных разнообразных запросов. Основная идея этого метода заключается в следующем: один и тот же вопрос может иметь несколько разных выражений, и разные выражения могут соответствовать разным релевантным документам. Например, «как изучить Python» можно расширить до «Учебник по Python для начинающих», «Методы обучения Python», «Руководство по программированию на Python» и другие запросы. Выполняя эти расширенные запросы параллельно и объединяя результаты, система может охватить более широкий круг соответствующих документов, избегая пропуска важной информации из-за различий в формулировках.

Преимущество MQE заключается в том, что он может автоматически понимать множество возможных значений пользовательских запросов, что особенно эффективно для неоднозначных запросов или запросов профессиональной терминологии. Система использует LLM для генерации расширенных запросов, обеспечивая разнообразие и смысловую релевантность расширений:

```python
def _prompt_mqe(query: str, n: int) -> List[str]:
    """Use LLM to generate diverse query expansions"""
    try:
        from ...core.llm import HelloAgentsLLM
        llm = HelloAgentsLLM()
        prompt = [
            {"role": "system", "content": "You are a retrieval query expansion assistant. Generate semantically equivalent or complementary diverse queries. Use Chinese, keep it short, avoid punctuation."},
            {"role": "user", "content": f"Original query: {query}\nPlease provide {n} differently phrased queries, one per line."}
        ]
        text = llm.invoke(prompt)
        lines = [ln.strip("- \t") for ln in (text or "").splitlines()]
        outs = [ln for ln in lines if ln]
        return outs[:n] or [query]
    except Exception:
        return [query]
```

(2) Встраивание гипотетических документов (HyDE)

Встраивание гипотетических документов (HyDE) — это инновационный метод поиска. Его основная идея — «используйте ответы, чтобы найти ответы». Традиционные методы поиска используют вопросы для сопоставления документов, но часто существует разница в распределении вопросов и ответов в семантическом пространстве: вопросы обычно представляют собой вопросительные предложения, а содержание документа — повествовательные предложения. HyDE заставляет LLM сначала генерировать гипотетический параграф ответа, а затем использовать этот параграф ответа для извлечения реальных документов, тем самым сокращая семантический разрыв между запросами и документами.

Преимущество этого метода в том, что гипотетические ответы ближе к реальным ответам в семантическом пространстве, что позволяет более точно сопоставить их с соответствующими документами. Даже если содержание гипотетического ответа не совсем правильно, содержащиеся в нем ключевые термины, понятия и стили выражения могут эффективно помочь поисковой системе найти правильные документы. HyDE может генерировать гипотетические документы, содержащие терминологию предметной области, специально для профессиональных доменных запросов, что значительно повышает точность поиска:

```python
def _prompt_hyde(query: str) -> Optional[str]:
    """Generate hypothetical document to improve retrieval"""
    try:
        from ...core.llm import HelloAgentsLLM
        llm = HelloAgentsLLM()
        prompt = [
            {"role": "system", "content": "Based on the user's question, first write a possible answer paragraph for use as a query document in vector retrieval (no analysis process)."},
            {"role": "user", "content": f"Question: {query}\nPlease directly write a medium-length, objective paragraph containing key terminology."}
        ]
        return llm.invoke(prompt)
    except Exception:
        return None
```

(3) Расширенная структура поиска

HelloAgents объединяет две стратегии MQE и HyDE в единую расширенную структуру поиска. Система позволяет пользователям выбирать, какие стратегии активировать на основе конкретных сценариев через`enable_mqe`и`enable_hyde`параметры: для сценариев, требующих высокой полноты, обе стратегии могут быть включены одновременно; для сценариев, чувствительных к производительности, можно использовать только базовый поиск.

Основным механизмом расширенного поиска является трехэтапный рабочий процесс «расширение-извлечение-объединение». Во-первых, система генерирует несколько расширенных запросов на основе исходного запроса (включая разнообразные запросы, созданные MQE, и гипотетические документы, созданные HyDE); затем он параллельно выполняет поиск векторов для каждого расширенного запроса, чтобы получить пул документов-кандидатов; наконец, он объединяет все результаты посредством дедупликации и сортировки оценок, возвращая наиболее релевантные документы из списка top-k. Изобретательность этого проекта в том, что он расширяет пул кандидатов за счет`candidate_pool_multiplier`параметр (по умолчанию — 4), обеспечивающий достаточное количество документов-кандидатов для проверки, избегая при этом возврата дублированного контента посредством интеллектуальной дедупликации.

```python
def search_vectors_expanded(
    store = None,
    query: str = "",
    top_k: int = 8,
    rag_namespace: Optional[str] = None,
    only_rag_data: bool = True,
    score_threshold: Optional[float] = None,
    enable_mqe: bool = False,
    mqe_expansions: int = 2,
    enable_hyde: bool = False,
    candidate_pool_multiplier: int = 4,
) -> List[Dict]:
    """
    Search with query expansion using unified embedding and Qdrant.
    """
    if not query:
        return []

    # Create default storage
    if store is None:
        store = _create_default_vector_store()

    # Query expansion
    expansions: List[str] = [query]

    if enable_mqe and mqe_expansions > 0:
        expansions.extend(_prompt_mqe(query, mqe_expansions))
    if enable_hyde:
        hyde_text = _prompt_hyde(query)
        if hyde_text:
            expansions.append(hyde_text)

    # Deduplication and trimming
    uniq: List[str] = []
    for e in expansions:
        if e and e not in uniq:
            uniq.append(e)
    expansions = uniq[: max(1, len(uniq))]

    # Allocate candidate pool
    pool = max(top_k * candidate_pool_multiplier, 20)
    per = max(1, pool // max(1, len(expansions)))

    # Build RAG data filter
    where = {"memory_type": "rag_chunk"}
    if only_rag_data:
        where["is_rag_data"] = True
        where["data_source"] = "rag_pipeline"
    if rag_namespace:
        where["rag_namespace"] = rag_namespace

    # Collect results from all expanded queries
    agg: Dict[str, Dict] = {}
    for q in expansions:
        qv = embed_query(q)
        hits = store.search_similar(
            query_vector=qv,
            limit=per,
            score_threshold=score_threshold,
            where=where
        )
        for h in hits:
            mid = h.get("metadata", {}).get("memory_id", h.get("id"))
            s = float(h.get("score", 0.0))
            if mid not in agg or s > float(agg[mid].get("score", 0.0)):
                agg[mid] = h

    # Sort by score and return
    merged = list(agg.values())
    merged.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    return merged[:top_k]
```

В практических приложениях лучше всего работает совместное использование этих трех стратегий. MQE превосходно справляется с проблемами разнообразия формулировок, HyDE превосходно справляется с проблемами семантических разрывов, а унифицированная структура обеспечивает качество и разнообразие результатов. Для общих запросов рекомендуется включить MQE; для профессиональных доменных запросов рекомендуется одновременно включить MQE и HyDE; для сценариев, чувствительных к производительности, можно использовать только базовое извлечение или только MQE.

Конечно, есть много других интересных методов. Это просто подходящее введение в расширение для всех. В реальных сценариях использования вам также необходимо попытаться найти решения, подходящие для проблемы.

## 8.4 Создание интеллектуального помощника по вопросам и ответам на документы

В предыдущих разделах мы подробно описали проектирование и реализацию системы памяти HelloAgents и системы RAG. Теперь давайте на полном практическом примере продемонстрируем, как органично объединить эти две системы для создания интеллектуального помощника по вопросам и ответам на документы.

### 8.4.1 Предыстория дела и цели

В реальной работе нам часто приходится обрабатывать большое количество технических документов, исследовательских работ, руководств по продуктам и других файлов PDF. Традиционные методы чтения документов неэффективны, что затрудняет быстрый поиск ключевой информации, не говоря уже о установлении связей между знаниями.

В этом случае будет использоваться общедоступный PDF-документ бета-версии.`Happy-LLM-0727.pdf`из другого практического руководства Datawhale по большим моделям Happy-LLM в качестве примера создания **веб-приложения на основе Gradio**, демонстрирующего, как использовать RAGTool и MemoryTool для создания полноценного интерактивного помощника по обучению. PDF-файл можно получить по этой [ссылка](https://github.com/datawhalechina/happy-llm/releases/download/v1.0.1/Happy-LLM-0727.pdf).

Мы надеемся реализовать следующие функции:

1. **Интеллектуальная обработка документов**: используйте MarkItDown для унифицированного преобразования PDF в Markdown, интеллектуальную стратегию фрагментирования на основе структуры Markdown, эффективную векторизацию и построение индексов.

2. **Расширенные вопросы и ответы при поиске**: расширение нескольких запросов (MQE) для улучшения отзыва, встраивание гипотетических документов (HyDE) для повышения точности поиска, интеллектуальные вопросы и ответы с учетом контекста.

3. **Многоуровневое управление памятью**: рабочая память управляет текущими учебными задачами и контекстом, эпизодическая память записывает учебные события и историю запросов, семантическая память хранит концептуальные знания и понимание, перцептивная память обрабатывает особенности документов и мультимодальную информацию.

4. **Персонализированная поддержка обучения**: Персонализированные рекомендации на основе истории обучения, консолидации памяти и выборочного забывания, создания отчетов об обучении и отслеживания прогресса.

Чтобы более наглядно продемонстрировать рабочий процесс всей системы, на рисунке 8.6 показаны взаимосвязи и поток данных между пятью этапами. Пять шагов образуют полный замкнутый цикл: Шаг 1 записывает информацию из обработанных PDF-документов в систему памяти, Результаты поиска на Шаге 2 также записываются в систему памяти, Шаг 3 демонстрирует все функции системы памяти (добавление, извлечение, консолидация, забывание), Шаг 4 объединяет RAG и память для обеспечения интеллектуальной маршрутизации, а Шаг 5 собирает всю статистическую информацию для создания отчетов об обучении.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-6.png" alt="" width="85%"/>
  <p>Рисунок 8.6. Пятиэтапный рабочий процесс интеллектуального помощника по вопросам и ответам.</p>
</div>

Далее мы продемонстрируем, как реализовать это веб-приложение. Все приложение разделено на три основные части:

1. **Класс основного помощника (PDFLearningAssistant)**: инкапсулирует логику вызова RAGTool и MemoryTool.
2. **Веб-интерфейс Gradio**: обеспечивает удобный интерфейс взаимодействия с пользователем. Для обучения в этой части можно обратиться к примеру кода.
3. **Другие основные функции**: запись заметок, обзор обучения, просмотр статистики и создание отчетов.

### 8.4.2 Реализация класса Core Assistant

Сначала мы реализуем основной класс помощника`PDFLearningAssistant`, который инкапсулирует логику вызова RAGTool и MemoryTool.

(1) Инициализация класса

```python
class PDFLearningAssistant:
    """Intelligent document Q&A assistant"""

    def __init__(self, user_id: str = "default_user"):
        """Initialize learning assistant

        Args:
            user_id: User ID, used to isolate data for different users
        """
        self.user_id = user_id
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize tools
        self.memory_tool = MemoryTool(user_id=user_id)
        self.rag_tool = RAGTool(rag_namespace=f"pdf_{user_id}")

        # Learning statistics
        self.stats = {
            "session_start": datetime.now(),
            "documents_loaded": 0,
            "questions_asked": 0,
            "concepts_learned": 0
        }

        # Currently loaded document
        self.current_document = None
```

В этом процессе инициализации мы приняли несколько ключевых проектных решений:

**Инициализация MemoryTool**: реализует изоляцию памяти на уровне пользователя посредством`user_id`параметр. Воспоминания об обучении разных пользователей полностью независимы, и каждый пользователь имеет свою собственную рабочую память, эпизодическую память, семантическую память и пространство перцептивной памяти.

**Инициализация RAGTool**: реализует изоляцию пространства имен базы знаний посредством`rag_namespace`параметр. С использованием`f"pdf_{user_id}"`В качестве пространства имен каждый пользователь имеет собственную независимую базу знаний в формате PDF.

Управление сессиями`session_id`используется для отслеживания всего процесса одного учебного занятия, облегчая последующий обзор и анализ процесса обучения.

**Статистическая информация**:`stats`словарь записывает ключевые показатели обучения для создания отчетов об обучении.

(2) Загрузка PDF-документов

```python
def load_document(self, pdf_path: str) -> Dict[str, Any]:
    """Load PDF document into knowledge base

    Args:
        pdf_path: PDF file path

    Returns:
        Dict: Result containing success and message
    """
    if not os.path.exists(pdf_path):
        return {"success": False, "message": f"File does not exist: {pdf_path}"}

    start_time = time.time()

    # [RAGTool] Process PDF: MarkItDown conversion → Intelligent chunking → Vectorization
    result = self.rag_tool.execute(
        "add_document",
        file_path=pdf_path,
        chunk_size=1000,
        chunk_overlap=200
    )

    process_time = time.time() - start_time

    if result.get("success", False):
        self.current_document = os.path.basename(pdf_path)
        self.stats["documents_loaded"] += 1

        # [MemoryTool] Record to learning memory
        self.memory_tool.execute(
            "add",
            content=f"Loaded document 《{self.current_document}》",
            memory_type="episodic",
            importance=0.9,
            event_type="document_loaded",
            session_id=self.session_id
        )

        return {
            "success": True,
            "message": f"Loading successful! (Time: {process_time:.1f}s)",
            "document": self.current_document
        }
    else:
        return {
            "success": False,
            "message": f"Loading failed: {result.get('error', 'Unknown error')}"
        }
```

Мы можем завершить обработку PDF с помощью всего одной строки кода:

```python
result = self.rag_tool.execute(
    "add_document",
    file_path=pdf_path,
    chunk_size=1000,
    chunk_overlap=200
)
```

Этот вызов запускает полный рабочий процесс обработки RAGTool (преобразование MarkItDown, расширенная обработка, интеллектуальное разбиение на части, векторизация хранилища). Эти внутренние детали были подробно представлены в разделе 8.3. Нам нужно сосредоточиться только на:

- ** Тип операции **: `"add_document"` - Добавить документ в базу знаний
- **Путь к файлу**: `file_path` — путь к PDF-файлу.
- **Параметры фрагментации**: `chunk_size=1000, chunk_overlap=200` — управление фрагментированием текста.
- ** Результат возврата **: словарь, содержащий статус обработки и статистическую информацию

После успешной загрузки документа используем MemoryTool для записи его в эпизодическую память:

```python
self.memory_tool.execute(
    "add",
    content=f"Loaded document 《{self.current_document}》",
    memory_type="episodic",
    importance=0.9,
    event_type="document_loaded",
    session_id=self.session_id
)
```

**Зачем использовать эпизодическую память?** Потому что это определенное событие с временной меткой, подходящее для записи с эпизодической памятью.`session_id`Параметр связывает это событие с текущим сеансом обучения, облегчая последующий обзор процесса обучения.

Эта запись памяти закладывает основу для последующих персонализированных услуг:

- Пользователь спрашивает: «Какие документы я загружал раньше?" → Извлечь из эпизодической памяти
- Система может отслеживать учебный процесс пользователя и использование документов

### 8.4.3 Интеллектуальная функция вопросов и ответов

После загрузки документа пользователи могут задавать вопросы о документе. Мы реализуем`ask`метод обработки пользовательских вопросов:

```python
def ask(self, question: str, use_advanced_search: bool = True) -> str:
    """Ask questions about the document

    Args:
        question: User question
        use_advanced_search: Whether to use advanced retrieval (MQE + HyDE)

    Returns:
        str: Answer
    """
    if not self.current_document:
        return "⚠️ Please load a document first!"

    # [MemoryTool] Record question to working memory
    self.memory_tool.execute(
        "add",
        content=f"Question: {question}",
        memory_type="working",
        importance=0.6,
        session_id=self.session_id
    )

    # [RAGTool] Use advanced retrieval to get answer
    answer = self.rag_tool.execute(
        "ask",
        question=question,
        limit=5,
        enable_advanced_search=use_advanced_search,
        enable_mqe=use_advanced_search,
        enable_hyde=use_advanced_search
    )

    # [MemoryTool] Record to episodic memory
    self.memory_tool.execute(
        "add",
        content=f"Learning about '{question}'",
        memory_type="episodic",
        importance=0.7,
        event_type="qa_interaction",
        session_id=self.session_id
    )

    self.stats["questions_asked"] += 1

    return answer
```

Когда мы звоним`self.rag_tool.execute("ask", ...)`, RAGTool внутренне выполняет следующий расширенный рабочий процесс извлечения:

1. **Расширение нескольких запросов (MQE)**:

   ```python
   # Generate diverse queries
   expanded_queries = self._generate_multi_queries(question)
   # For example, for "What is a large language model?", it might generate:
   # - "What is the definition of a large language model?"
   # - "Please explain large language models"
   # - "What does LLM mean?"
   ```

MQE генерирует семантически эквивалентные, но по-разному выраженные запросы с помощью LLM, понимая намерения пользователя с разных точек зрения и улучшая запоминаемость на 30–50%.

2. **Гипотетические вложения документов (HyDE)**:

   - Создавайте гипотетические документы ответов, устраняя семантический разрыв между запросами и документами.
   - Используйте векторы гипотетических ответов для поиска.

Внутренняя реализация этих передовых методов поиска подробно описана в разделе 8.3.5.

### 8.4.4 Другие основные функции

Помимо загрузки документов и интеллектуальных вопросов и ответов, нам также необходимо реализовать такие функции, как запись заметок, обзор обучения, просмотр статистики и создание отчетов:

```python
def add_note(self, content: str, concept: Optional[str] = None):
    """Add learning note"""
    self.memory_tool.execute(
        "add",
        content=content,
        memory_type="semantic",
        importance=0.8,
        concept=concept or "general",
        session_id=self.session_id
    )
    self.stats["concepts_learned"] += 1

def recall(self, query: str, limit: int = 5) -> str:
    """Review learning journey"""
    result = self.memory_tool.execute(
        "search",
        query=query,
        limit=limit
    )
    return result

def get_stats(self) -> Dict[str, Any]:
    """Get learning statistics"""
    duration = (datetime.now() - self.stats["session_start"]).total_seconds()
    return {
        "Session Duration": f"{duration:.0f}s",
        "Documents Loaded": self.stats["documents_loaded"],
        "Questions Asked": self.stats["questions_asked"],
        "Learning Notes": self.stats["concepts_learned"],
        "Current Document": self.current_document or "Not loaded"
    }

def generate_report(self, save_to_file: bool = True) -> Dict[str, Any]:
    """Generate learning report"""
    memory_summary = self.memory_tool.execute("summary", limit=10)
    rag_stats = self.rag_tool.execute("stats")

    duration = (datetime.now() - self.stats["session_start"]).total_seconds()
    report = {
        "session_info": {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self.stats["session_start"].isoformat(),
            "duration_seconds": duration
        },
        "learning_metrics": {
            "documents_loaded": self.stats["documents_loaded"],
            "questions_asked": self.stats["questions_asked"],
            "concepts_learned": self.stats["concepts_learned"]
        },
        "memory_summary": memory_summary,
        "rag_status": rag_stats
    }

    if save_to_file:
        report_file = f"learning_report_{self.session_id}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        report["report_file"] = report_file

    return report
```

Эти методы соответственно реализуют:

- **add_note**: сохранение учебных заметок в семантической памяти.
- **recall**: Извлеките учебный процесс из системы памяти.
- **get_stats**: Получить статистическую информацию о текущем сеансе.
- **generate_report**: создать подробный отчет об обучении и сохранить его в формате JSON.

### 8.4.5 Демонстрация эффекта бега

Далее следует демонстрация эффекта бега. Как показано на рисунке 8.7, после входа на главную страницу необходимо сначала инициализировать помощника, который должен загрузить нашу базу данных, модель, API и другие операции загрузки. Затем передайте PDF-документ и нажмите, чтобы загрузить документ.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-7.png" alt="" width="85%"/>
  <p>Рисунок 8.7. Главная страница помощника по вопросам и ответам</p>
</div>

Первая функция — это интеллектуальные вопросы и ответы, которые можно получать на основе загруженных документов, возвращать справочные источники и рассчитывать сходство связанных материалов. Это демонстрация возможностей инструмента RAG, как показано на рисунке 8.8.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-8.png" alt="" width="85%"/>
  <p>Рисунок 8.8. Главная страница помощника по вопросам и ответам</p>
</div>

Вторая функция — изучение конспектов. Как показано на рисунке 8.9, вы можете выбирать связанные понятия и писать содержание примечаний. Эта часть использует инструмент «Память» и сохраняет ваши личные заметки в базе данных для удобной статистики и последующего возврата общих отчетов об обучении.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-9.png" alt="" width="85%"/>
  <p>Рисунок 8.9. Главная страница помощника по вопросам и ответам</p>
</div>

Наконец, есть статистика прогресса обучения и формирование отчетов. Как показано на рисунке 8.10, мы можем видеть количество загруженных документов, количество заданных вопросов и количество заметок во время использования помощника. Наконец, наши результаты и заметки вопросов и ответов организуются в документ JSON и возвращаются.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-10.png" alt="" width="85%"/>
  <p>Рисунок 8.10. Главная страница помощника по вопросам и ответам</p>
</div>

В этом примере помощника по вопросам и ответам мы продемонстрировали, как использовать RAGTool и MemoryTool для создания полноценной **интеллектуальной веб-системы вопросов и ответов для документов**. Полный код можно найти в`code/chapter8/11_Q&A_Assistant.py`. После запуска посетите`http://localhost:7860`использовать этого интеллектуального помощника по обучению.

Читателям рекомендуется лично выполнить этот кейс, испытать возможности RAG и Memory, а также расширять и настраивать их на этой основе для создания интеллектуальных приложений, отвечающих их собственным потребностям!

## 8.5 Краткое содержание главы и перспективы

В этой главе мы успешно добавили в структуру HelloAgents две основные возможности: систему памяти и систему RAG.

Для читателей, желающих глубоко изучить и применить содержание этой главы, мы даем следующие предложения:

1. От нуля до единицы: вручную спроектируйте базовый модуль памяти и постепенно добавляйте более сложные функции.

2. Попробуйте оценить различные модели внедрения и стратегии поиска в проектах, чтобы найти оптимальное решение для конкретных задач.

3. Примените изученную память и систему RAG к реальному личному проекту, проверяя и улучшая возможности на практике.

Расширенное исследование

1. Отслеживайте и изучайте новейшие репозитории памяти и RAG, изучая отличные реализации.
2. Изучите возможность применения архитектуры RAG к мультимодальным (текст + изображение) или кросс-модальным сценариям.
3. Участвуйте в проекте с открытым исходным кодом HelloAgents, делясь своими идеями и кодом.

Изучая эту главу, вы не только освоили технологию реализации систем памяти и RAG, но, что более важно, поняли, как преобразовать теорию когнитивной науки в практические инженерные решения. Этот междисциплинарный образ мышления заложит прочную основу для вашего дальнейшего развития в области искусственного интеллекта.

Наконец, давайте обобщим всю систему знаний этой главы с помощью карты связей, как показано на рис. 8.11:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/8-figures/8-11.png" alt="" width="85%"/>
  <p>Рисунок 8.11. Hello-агенты. Глава 8. Сводка знаний.</p>
</div>

В этой главе были продемонстрированы возможности системы памяти платформы HelloAgents и технологии RAG. Мы успешно создали по-настоящему «умного» помощника по обучению. Эту архитектуру можно легко расширить на другие сценарии применения, такие как обслуживание клиентов, техническая поддержка, личные помощники и другие области.

В следующей главе мы продолжим изучать способы дальнейшего улучшения качества диалога и пользовательского опыта агентов с помощью контекстной инженерии. Следите за обновлениями!

## Упражнения

> **Примечание**. Для некоторых упражнений нет стандартных ответов. Основное внимание уделяется развитию у учащихся всестороннего понимания и практических способностей систем памяти и технологии RAG.

1. В этой главе были представлены четыре типа памяти: рабочая память, эпизодическая память, семантическая память и перцептивная память. Пожалуйста, проанализируйте:

   - В разделе 8.2.5 каждый тип памяти имеет уникальную формулу оценки. Пожалуйста, сравните механизмы оценки эпизодической памяти и семантической памяти и объясните, почему эпизодическая память больше подчеркивает «временную новизну» (вес 0,2), тогда как семантическая память больше подчеркивает «извлечение графа» (вес 0,3)?
   - Если бы вам нужно было создать «личного помощника по управлению здоровьем» (который должен записывать данные о диете, физических упражнениях, сне пользователя и давать советы по здоровью), как бы вы объединили эти четыре типа памяти? Разработайте конкретные сценарии применения для каждого типа памяти.
   - Рабочая память использует механизм TTL (Time To Live) для автоматической очистки просроченных данных. Подумайте, при каких обстоятельствах важные рабочие воспоминания должны «консолидироваться» в долговременную память? Как разработать условие запуска автоматической консолидации?

2. В системе RAG, описанной в разделе 8.3, мы используем MarkItDown для единообразного преобразования документов различных форматов в Markdown. Пожалуйста, подумайте хорошенько:

> **Примечание * *: Это практический вопрос, рекомендуется фактическая работа

   - Текущая стратегия интеллектуального разбиения на части основана на иерархии заголовков Markdown (#, ##, ###) для сегментации. Если обработка документов без четкой структуры заголовков (например, новеллы, правовые положения), как оптимизировать стратегию группирования? Попробуйте реализовать алгоритм чанкинга на основе «семантических границ».
   - В разделе 8.3.5 представлены две расширенные стратегии поиска: MQE (расширение нескольких запросов) и HyDE (встраивание гипотетических документов). Выберите практический сценарий (например, вопросы и ответы по техническим документам, поиск медицинских знаний), сравните различия в эффектах базового поиска, MQE и HyDE и проанализируйте соответствующие применимые сценарии.
   - Качество извлечения системы ТРЯПКИ во многом зависит от выбора модели встраивания. Пожалуйста, сравните три решения по внедрению, упомянутые в этой главе (Bailian API, локальный трансформатор, TF-IDF), с точки зрения точности, скорости, стоимости, автономного развертывания и т. д., и предоставьте рекомендации по выбору.

3. Механизм «забывания» системы памяти — важная конструкция, имитирующая человеческое познание. На основе MemoryTool из раздела 8.2.3 выполните следующую расширенную практику:

> **Примечание * *: Это практический вопрос, рекомендуется фактическая работа

   - В настоящее время предусмотрены три стратегии забывания: основанная на важности, основанная на времени и основанная на потенциале. Пожалуйста, разработайте и внедрите стратегию «интеллектуального забывания», которая всесторонне учитывает важность, частоту доступа, распад времени и другие факторы, используя взвешенную оценку, чтобы решить, какие воспоминания следует забыть.
   - В долго работающих агентских системах база данных памяти может накапливать большой объем данных. Пожалуйста, разработайте механизм «архивирования памяти»: переносите давно неиспользуемые, но потенциально ценные воспоминания в холодное хранилище и восстанавливайте их при необходимости. Как этот механизм следует интегрировать с существующими четырьмя типами памяти?
   - Подумайте: если агенту необходимо «забыть» определенную конфиденциальную информацию (например, данные о конфиденциальности пользователя), достаточно ли просто удалить ее из базы данных? Как обеспечить полную очистку данных в случае использования векторных и графовых баз данных?

4. В случае «Интеллектуального помощника по обучению» в разделе 8.4 мы объединили MemoryTool и RAGTool. Пожалуйста, проанализируйте подробно:

   - Метод `ask_question()` в данном случае использует как извлечение RAG, так и извлечение памяти. Пожалуйста, проанализируйте: при каких обстоятельствах следует отдавать приоритет RAG? При каких обстоятельствах Память должна быть приоритетной? Как спроектировать механизм «интеллектуальной маршрутизации» для автоматического выбора наиболее подходящего метода извлечения?
   - Текущий отчет об обучении (`generate_report()`) содержит только статистическую информацию. Пожалуйста, расширьте эту функцию и разработайте более интеллектуальный генератор отчетов об обучении: способный анализировать траекторию обучения пользователя, выявлять слепые зоны знаний и рекомендовать следующий учебный контент. Какие типы памяти и стратегии извлечения необходимы для этого?
   - Предположим, вы хотите развернуть этот помощник по обучению как многопользовательский веб-сервис, где каждый пользователь имеет независимую память и базу знаний. Пожалуйста, разработайте решение для изоляции данных: как реализовать изоляцию данных на уровне пользователя в Qdrant и Neo4j? Как оптимизировать производительность поиска в многопользовательских сценариях?

5. Семантическая память использует базу данных графов Neo4j для хранения графов знаний. Пожалуйста, подумайте:

   - В реализации семантической памяти, описанной в разделе 8.2.5, система автоматически извлекает сущности и отношения для построения графов знаний. Проанализируйте, пожалуйста: насколько точно это автоматическое извлечение? При каких обстоятельствах могут быть извлечены неправильные сущности или отношения? Как разработать механизм «оценки качества графа знаний»?
   - Важным преимуществом графов знаний является поддержка сложных реляционных рассуждений. Пожалуйста, разработайте сценарий запроса, который полностью использует возможности запросов графов Neo4j (такие как многопрыжковые связи, поиск пути) для выполнения задач, которые не может выполнить чистый векторный поиск.
   - Сравните гибридную стратегию семантической памяти «поиск векторов + поиск по графам» с чистым векторным поиском: в каких типах запросов поиск по графу может привести к значительному повышению производительности? Проиллюстрируйте, пожалуйста, конкретными примерами.

## Ссылки

[1] Аткинсон Р.К. и Шиффрин Р.М. (1968). Человеческая память: предлагаемая система и процессы ее управления. В *Психологии обучения и мотивации* (Том 2, стр. 89-195). Академическая пресса.

