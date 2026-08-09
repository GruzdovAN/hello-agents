# Глава 15. Кибер-городок

В этой главе мы рассмотрим совершенно новое направление: **объединение агентских технологий с игровыми движками для создания искусственного города, полного жизненной силы**.

Помните этих реалистичных неигровых персонажей из «The Sims» или «Animal Crossing»? У них есть свои личности, воспоминания и социальные отношения. Кибергород в этой главе будет похожим проектом, но в отличие от традиционных игр наши NPC обладают настоящим «интеллектом» — они могут понимать разговоры игроков, запоминать прошлые взаимодействия и реагировать по-разному в зависимости от уровня привязанности. Кибергород в этой главе включает в себя следующие основные функции:

**(1) Интеллектуальная система диалога с NPC**: игроки могут разговаривать с NPC на естественном языке, а NPC будут отвечать в зависимости от своих ролевых настроек и воспоминаний.

**(2) Система памяти**: NPC обладают кратковременной и долговременной памятью, способной запоминать историю взаимодействия с игроками.

**(3) Система привязанности**: отношение NPC к игрокам меняется в зависимости от взаимодействия: от незнакомца к знакомому, от дружелюбного к интимному.

**(4) Геймифицированное взаимодействие**: игроки могут свободно перемещаться по офисной 2D-сцене в пиксельном стиле и взаимодействовать с различными NPC.

**(5) Система регистрации в реальном времени**: все разговоры и взаимодействия записываются для облегчения отладки и анализа.

## 15.1 Обзор проекта и архитектурный дизайн

### 15.1.1 Зачем строить город с искусственным интеллектом

Неигровые персонажи в традиционных играх обычно могут произносить только фиксированные строки или ограниченно взаимодействовать через предустановленные деревья диалогов. Даже в самых сложных RPG-играх диалоги NPC заранее пишутся сценаристами. Этот подход поддается контролю, но ему не хватает реального «разума» и «жизненной силы».

Представьте себе, если бы NPC в играх могли понимать все, что вы говорите, и больше не ограничивались бы предустановленными опциями. Вы можете общаться с NPC на естественном языке. NPC запомнят, что вы сказали в прошлый раз, ваши отношения и даже ваши предпочтения. У каждого NPC есть своя профессия, личность и стиль речи. Отношение NPC к вам меняется в зависимости от взаимодействия: от незнакомцев к друзьям и даже близким друзьям.

Это новая возможность, которую технология искусственного интеллекта привносит в игры. Объединив большие языковые модели с игровыми движками, мы можем создавать по-настоящему «живых» NPC. Это не просто техническая демонстрация, а исследование будущих игровых форм. В обучающих играх НПС могут играть исторических личностей и учёных, проводя интерактивное обучение со студентами. В виртуальных офисах NPC могут играть роль коллег и наставников, оказывая помощь и советы. NPC также могут выступать в качестве компаньонов, осуществляя эмоциональное общение с пользователями, что применяется в области психического здоровья. Конечно, самое прямое применение — это добавление AI-NPC в традиционные игры для улучшения впечатлений игроков.

### 15.1.2 Обзор технической архитектуры

Cyber ​​Town использует архитектуру разделения **игровой движок + серверные службы**, разделенную на четыре уровня, как показано на рис. 15.1.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-1.png" alt="" width="85%"/>
  <p>Рисунок 15.1 Техническая архитектура Кибергорода</p>
</div>

Интерфейсный уровень использует игровой движок Godot 4.5, отвечающий за рендеринг игры, управление игроком, отображение NPC и диалоговый интерфейс. Godot — это игровой 2D/3D-движок с открытым исходным кодом, очень подходящий для быстрой разработки игр в пиксельном стиле. Внутренний уровень использует платформу FastAPI, отвечающую за маршрутизацию API, управление состоянием NPC, обработку диалогов и ведение журналов. FastAPI — это современная веб-инфраструктура Python с отличной производительностью и простотой разработки. Уровень агента использует нашу собственную структуру HelloAgents, отвечающую за интеллект NPC, управление памятью и расчет привязанности. Каждый NPC представляет собой экземпляр SimpleAgent с независимой памятью и состоянием. Уровень внешнего сервиса обеспечивает возможности LLM, векторное хранилище и постоянство данных, включая LLM API, векторную базу данных Qdrant и реляционную базу данных SQLite.

Процесс потока данных показан на рисунке 15.2:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-2.png" alt="" width="85%"/>
  <p>Рисунок 15.2 Процесс потока данных</p>
</div>

Игроки нажимают клавишу E в Godot, чтобы взаимодействовать с NPC, а Godot отправляет запросы диалога на серверную часть FastAPI через HTTP API. Серверная часть вызывает SimpleAgent HelloAgents для обработки диалога, агент извлекает соответствующую историю из системы памяти, а затем вызывает LLM для генерации ответа. Серверная часть обновляет состояние и привязанность NPC, записывает журналы в консоль и файл и, наконец, возвращает ответ во внешний интерфейс Godot. Годо отображает ответ NPC и обновляет пользовательский интерфейс, завершая полный цикл взаимодействия.

Структура проекта следующая, что позволяет легко найти исходный код:

```
Helloagents-AI-Town/
├── helloagents-ai-town/           # Godot game project
│   ├── project.godot              # Godot project configuration
│   ├── scenes/                    # Game scenes
│   │   ├── main.tscn              # Main scene (office)
│   │   ├── player.tscn            # Player character
│   │   ├── npc.tscn               # NPC character
│   │   └── dialogue_ui.tscn       # Dialogue UI
│   ├── scripts/                   # GDScript scripts
│   │   ├── main.gd                # Main scene logic
│   │   ├── player.gd              # Player control
│   │   ├── npc.gd                 # NPC behavior
│   │   ├── dialogue_ui.gd         # Dialogue UI logic
│   │   ├── api_client.gd          # API client
│   │   └── config.gd              # Configuration management
│   └── assets/                    # Game assets
│       ├── characters/            # Character sprites
│       ├── interiors/             # Interior scenes
│       ├── ui/                    # UI materials
│       └── audio/                 # Sound effects and music
│
└── backend/                       # Python back-end
    ├── main.py                    # FastAPI main program
    ├── agents.py                  # NPC Agent system
    ├── relationship_manager.py    # Affection management
    ├── state_manager.py           # State management
    ├── logger.py                  # Logging system
    ├── config.py                  # Configuration management
    ├── models.py                  # Data models
    ├── requirements.txt           # Python dependencies
    └── .env.example               # Environment variable example
```

Подробное проектирование архитектуры и потока данных будет представлено в последующих разделах.

### 15.1.3 Быстрый опыт: запуск проекта за 5 минут

Прежде чем углубляться в детали реализации, давайте сначала запустим проект, чтобы увидеть конечный результат. Таким образом, вы получите интуитивное понимание всей системы.

**Требования к среде:**

- Годо 4.2 или выше
- Питон 3.10 или выше
- Ключ API LLM (OpenAI, DeepSeek, Zhipu и т. д.)

**Получить проект:**

Вы можете проверить`code/chapter15/Helloagents-AI-Town`или клонируйте полный репозиторий hello-agents с GitHub.

**Запуск серверной части:**

```bash
# 1. Enter backend directory
cd Helloagents-AI-Town/backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env file, fill in your API key

# 4. Start back-end service
python main.py
```

После успешного запуска вы увидите следующий вывод:

```
============================================================
🎮 Cyber Town back-end service starting...
============================================================
✅ All services started!
📡 API address: http://0.0.0.0:8000
📚 API documentation: http://0.0.0.0:8000/docs
============================================================
```

**Запуск Годо:**

Установка Godot очень проста. Windows обеспечивает прямой`.exe`файл, а Mac также предоставляет`.dmg`файл. Скачать можно прямо с официального сайта ([Windows](https://godotengine.org/download/windows/) / [Мак](https://godotengine.org/download/macos/))

Откройте движок Godot, нажмите кнопку «Импортировать», перейдите к`Helloagents-AI-Town/helloagents-ai-town/scenes/main.tscn`и нажмите «Импортировать и редактировать». После того, как Годо импортирует ресурсы, нажмите`F5`или нажмите кнопку «Запустить», чтобы начать игру.

**Испытайте основные функции:**

После запуска игры вы увидите сцену офиса Datawhale в пиксельном стиле, как показано на рисунке 15.3.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-3.png" alt="" width="85%"/>
  <p>Рисунок 15.3. Сцена игры «Кибергород»</p>
</div>

Используйте клавиши WASD для перемещения персонажа игрока. Когда вы подойдете к NPC, на экране появится подсказка «Нажмите E, чтобы взаимодействовать». После нажатия клавиши E появится диалоговое окно, и вы сможете ввести все, что хотите сказать, как показано на рисунке 15.4.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-4.png" alt="" width="85%"/>
  <p>Рисунок 15.4 Диалоговый интерфейс с NPC</p>
</div>

NPC будут отвечать в зависимости от настроек своей роли (инженер Python, менеджер по продукту, дизайнер пользовательского интерфейса) и вашей истории взаимодействия. По ходу разговора привязанность NPC к вам будет постепенно возрастать: от «незнакомого» до «знакомого», затем до «дружественного», «близкого» и даже «близкого друга».

**Система привязанностей реализована на серверной части**. В каждом разговоре значение привязанности корректируется на основе содержания сообщения игрока и анализа настроений. Хотя значение привязанности не отображается напрямую во внешнем интерфейсе игры, все изменения привязанности подробно записываются во внутренние журналы. Вы можете просмотреть изменения привязанности для каждого разговора в`backend/logs/dialogue_YYYY-MM-DD.log`файл. В файл журнала записывается подробная информация для каждого разговора, включая: текущую ценность привязанности, извлеченные соответствующие воспоминания, ответ NPC, величину изменения привязанности (+2,0, +3,0 и т. д.), причину изменения (дружеское приветствие, нормальное общение и т. д.) и результаты анализа настроений (положительные, нейтральные и т. д.). Этот дизайн позволяет разработчикам четко отслеживать развитие отношений между NPC и игроками, а также обеспечивает основу данных для последующего добавления пользовательского интерфейса взаимодействия во внешний интерфейс.

Все разговоры записываются в файлы журналов серверной части. Вы можете просмотреть их в режиме реального времени с помощью следующей команды:

```bash
# In the backend directory
python view_logs.py
```

Этот простой опыт демонстрирует основные функции AI Town. Далее мы углубимся в то, как реализовать эти функции.

## 15.2 Агентская система NPC

### 15.2.1 SimpleAgent на основе HelloAgents

В Кибер-городе каждый NPC является независимым агентом. Мы используем SimpleAgent из платформы HelloAgents для реализации интеллекта NPC. SimpleAgent — это облегченная реализация агента, которая инкапсулирует основные функции, такие как вызовы LLM, управление сообщениями и вызовы инструментов.

Вспомните SimpleAgent, о котором мы узнали в главе 7. Его суть — простой диалоговый цикл: получение сообщения пользователя, вызов LLM для генерации ответа, возврат результата. В Кибер-городе нам нужно создать экземпляр SimpleAgent для каждого NPC и настроить для них уникальные системные подсказки, назначая каждому NPC разные персональные данные и настройки ролей.

Давайте посмотрим, как создать NPC-агента. Во-первых, нам нужно определить основную информацию о NPC, включая идентификатор, имя, профессию и личность. Затем на основе этой информации строим системные подсказки, предоставляя LLM роль этого NPC. Наконец, мы создаем экземпляр SimpleAgent и настраиваем систему памяти.

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.memory import MemoryManager, WorkingMemory, EpisodicMemory

def create_npc_agent(npc_id: str, name: str, role: str, personality: str):
    """Create NPC Agent"""
    # Build system prompt
    system_prompt = f"""You are {name}, a {role}.
Your personality traits: {personality}

You work in the Datawhale office, working with colleagues to promote the development of the open source community.
Please have natural conversations with players based on your role and personality.
Remember your previous conversations to maintain dialogue coherence.
"""

    # Create LLM instance
    llm = HelloAgentsLLM()

    # Create memory manager
    memory_manager = MemoryManager(
        working_memory=WorkingMemory(capacity=10, ttl_minutes=120),
        episodic_memory=EpisodicMemory(
            db_path=f"memory_data/{npc_id}_episodic.db",
            collection_name=f"{npc_id}_memories"
        )
    )

    # Create Agent
    agent = SimpleAgent(
        name=name,
        llm=llm,
        system_prompt=system_prompt,
        memory_manager=memory_manager
    )

    return agent
```

Этот код демонстрирует, как создать агента NPC. Системная подсказка определяет личность и личность NPC, а менеджер памяти позволяет NPC запоминать историю разговоров с игроками. Рабочая память — это кратковременная память емкостью 10 сообщений и временем хранения 120 минут. EpisodicMemory — это долговременная память, использующая для хранения базу данных SQLite и векторную базу данных Qdrant и способную извлекать соответствующие исторические разговоры.

Рабочий процесс NPC Agent показан на рисунке 15.5:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-5.png" alt="" width="85%"/>
  <p>Рисунок 15.5 Рабочий процесс агента NPC</p>
</div>

### 15.2.2 Настройки ролей NPC и быстрый дизайн

Хорошему NPC нужны четкие индивидуальные и ролевые настройки. В Кибер-городе мы создали трех NPC, представляющих разные профессии и личности.

**Чжан Сан — инженер Python**

Чжан Сан — старший инженер Python, ответственный за основную разработку платформы HelloAgents. У него строгий характер, он говорит прямо и любит использовать технические термины. У него высокие требования к качеству кода, и он часто делится советами и лучшими практиками по программированию.

```python
npc_zhang = {
    "npc_id": "zhang_san",
    "name": "Zhang San",
    "role": "Python Engineer",
    "personality": "Rigorous, professional, likes to share technical knowledge. Speaks directly, focuses on code quality."
}
```

**Ли Си - менеджер по продукту**

Ли Си — опытный менеджер по продукту, отвечающий за планирование продуктов и разработку пользовательского интерфейса платформы HelloAgents. У него общительный характер, он хорош в общении и всегда может мыслить с точки зрения пользователя. Он любит обсуждать дизайн продукта и потребности пользователей и часто спрашивает «почему».

```python
npc_li = {
    "npc_id": "li_si",
    "name": "Li Si",
    "role": "Product Manager",
    "personality": "Outgoing, good at communication, focuses on user experience. Likes to think from the user's perspective."
}
```

**Ван Ву — дизайнер пользовательского интерфейса**

Ван Ву — креативный дизайнер пользовательского интерфейса, отвечающий за дизайн интерфейса и визуальное представление платформы HelloAgents. У него нежный характер, уникальная эстетика, острое восприятие цвета и планировки. Он любит обсуждать концепции дизайна и эстетику и часто делится дизайнерскими вдохновениями.

```python
npc_wang = {
    "npc_id": "wang_wu",
    "name": "Wang Wu",
    "role": "UI Designer",
    "personality": "Gentle, creative, unique aesthetics. Focuses on visual presentation and user experience."
}
```

Эти три NPC имеют разные характеристики. Игроки могут взаимодействовать с разными NPC в зависимости от своих интересов. Чжан Сан может научить вас навыкам программирования, Ли Си может обсудить с вами дизайн продукта, а Ван Ву может поделиться вдохновением для дизайна.

### 15.2.3 Интеграция системы памяти

Система памяти является ключом к интеллекту NPC. NPC, который может помнить прошлые разговоры, заставит игроков чувствовать себя более реалистично и интересно. Мы используем HelloAgents`WorkingMemory`и`EpisodicMemory`формировать кратковременную и долговременную память.

Кратковременная память хранит содержание последних разговоров с ограниченным объемом и автоматической очисткой с течением времени. Его роль — поддерживать связность диалога, позволяя NPC понимать контекст. Например, когда игрок говорит: «Какого это цвета?», NPC должен найти в кратковременной памяти, к чему относится это слово.

Долговременная память хранит всю историю разговоров, используя для семантического поиска векторные базы данных. Когда игрок упоминает тему, NPC может извлечь соответствующие исторические разговоры из долговременной памяти, вспоминая ранее обсуждавшийся контент. Например, когда игрок говорит: «Ты помнишь проект, который мы обсуждали в прошлый раз?», NPC может найти соответствующие записи разговора в долговременной памяти.

Архитектура системы памяти показана на рисунке 15.6:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-6.png" alt="" width="85%"/>
  <p>Рисунок 15.6 Архитектура системы памяти</p>
</div>

При фактическом использовании агент сначала получает недавние разговоры из кратковременной памяти, затем извлекает соответствующие исторические разговоры из долговременной памяти, отправляет эту информацию вместе в LLM и генерирует более точные и персонализированные ответы.

```python
# Agent's dialogue processing flow
def process_dialogue(agent, player_message):
    # 1. Get recent conversations from short-term memory
    recent_messages = agent.memory_manager.working_memory.get_recent_messages(5)

    # 2. Retrieve relevant history from long-term memory
    relevant_memories = agent.memory_manager.episodic_memory.search(
        query=player_message,
        top_k=3
    )

    # 3. Build context
    context = {
        "recent": recent_messages,
        "relevant": relevant_memories
    }

    # 4. Call Agent to generate reply
    reply = agent.run(player_message, context=context)

    # 5. Save to memory system
    agent.memory_manager.add_interaction(player_message, reply)

    return reply
```

Этот процесс гарантирует, что NPC смогут запомнить историю взаимодействия с игроками и отразить ее в разговорах.

### 15.2.4 Пакетная генерация диалогов: режим легкой загрузки

В реальной работе быстро обнаружилась проблема: когда несколько игроков одновременно общаются с разными NPC, серверной части необходимо одновременно обрабатывать несколько запросов LLM. Каждый запрос должен вызывать API, что не только увеличивает затраты, но также может привести к сбоям или задержкам запросов из-за ограничений параллелизма.

Чтобы решить эту проблему, мы разработали **систему пакетной генерации диалогов**. Основная идея заключается в следующем: объединить несколько диалоговых запросов NPC в один вызов LLM, позволяя LLM генерировать ответы всех NPC одновременно. Это похоже на «готовые блюда» ресторана: они готовятся партиями заранее и используются непосредственно при необходимости, что значительно снижает затраты и задержки.

Рабочий процесс создания пакета показан на рисунке 15.7:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-7.png" alt="" width="85%"/>
  <p>Рисунок 15.7. Пакетная генерация в сравнении с традиционным режимом</p>
</div>

Реализация пакетного генератора очень умна. Мы создаем специальную подсказку, требующую от LLM одновременно генерировать все диалоги NPC и возвращать их в формате JSON. Таким образом, один вызов API может получить все ответы NPC, что снижает затраты до 1/3 от исходных и значительно снижает задержку.

```python
class NPCBatchGenerator:
    """Generator for batch generating NPC dialogues"""

    def __init__(self):
        self.llm = HelloAgentsLLM()
        self.npc_configs = NPC_ROLES  # All NPC configurations

    def generate_batch_dialogues(self, context: Optional[str] = None) -> Dict[str, str]:
        """Batch generate dialogues for all NPCs

        Args:
            context: Scene context (such as "morning work time", "lunch time", etc.)

        Returns:
            Dict[str, str]: Mapping from NPC names to dialogue content
        """
        # Build batch generation prompt
        prompt = self._build_batch_prompt(context)

        # One LLM call generates all dialogues
        response = self.llm.invoke([
            {"role": "system", "content": "You are a game NPC dialogue generator, skilled at creating natural and realistic office dialogues."},
            {"role": "user", "content": prompt}
        ])

        # Parse JSON response
        dialogues = json.loads(response)
        # Return format: {"Zhang San": "...", "Li Si": "...", "Wang Wu": "..."}

        return dialogues

    def _build_batch_prompt(self, context: Optional[str] = None) -> str:
        """Build batch generation prompt"""
        # Automatically infer scene based on time
        if context is None:
            context = self._get_current_context()

        # Build NPC descriptions
        npc_descriptions = []
        for name, cfg in self.npc_configs.items():
            desc = f"- {name}({cfg['title']}): {cfg['activity']} at {cfg['location']}, personality {cfg['personality']}"
            npc_descriptions.append(desc)

        npc_desc_text = "\n".join(npc_descriptions)

        prompt = f"""Please generate current dialogues or behavior descriptions for 3 NPCs in the Datawhale office.

【Scene】{context}

【NPC Information】
{npc_desc_text}

【Generation Requirements】
1. Generate 1 sentence for each NPC (20-40 characters)
2. Content should match role settings, current activities, and scene atmosphere
3. Can be self-talk, work status description, or simple thoughts
4. Should be natural and realistic, like real office colleagues
5. **Must strictly return in JSON format**

【Output Format】(strictly follow)
{{"Zhang San": "...", "Li Si": "...", "Wang Wu": "..."}}

【Example Output】
{{"Zhang San": "This bug is really annoying, been debugging for two hours...", "Li Si": "Hmm, the priority of this feature needs to be re-evaluated.", "Wang Wu": "The latte art on this coffee is really nice, inspiration is coming!"}}

Please generate (only return JSON, no other content):
"""
        return prompt
```

Ключом к этому дизайну является построение подсказки. Мы явно требуем, чтобы LLM возвращал формат JSON и предоставлял пример вывода. LLM будет генерировать ответы строго в соответствии с этим форматом, и нам нужно только проанализировать JSON, чтобы получить все диалоги NPC.

Пакетная генерация имеет дополнительное преимущество: все диалоги NPC генерируются в одном и том же контексте, поэтому они имеют определенную степень корреляции. Например, если Чжан Сан исправляет ошибку, Ли Си может упомянуть, что помог ее проверить; если Ван Ву разрабатывает интерфейс, Чжан Сан может сказать, что проверит проект позже. Это делает атмосферу всего офиса более реалистичной и целостной.

Конечно, пакетная генерация также имеет некоторые ограничения. Он больше подходит для создания «фоновых диалогов» или «разговоров с самим собой» NPC, а не для прямого взаимодействия с игроками. Для разговоров, инициированных игроками, мы по-прежнему используем отдельных агентов для их обработки и обеспечения персонализированных и точных ответов. Пакетная генерация в основном используется в следующих сценариях:

1. **Фоновые диалоги NPC**: что делают и говорят NPC, когда игроки выходят на сцену.
2. **Обновления по времени**: регулярно обновляйте статус и диалоги NPC.
3. **Атмосфера сцены**: создание разных диалогов в зависимости от времени (утро, полдень, вечер).
4. **Снижение затрат**. Используйте пакетную генерацию, чтобы снизить частоту вызовов API в сценариях с высоким уровнем параллелизма.

**Гибридный режим: пакетная генерация + мгновенный ответ**

В реальной реализации мы использовали гибридный режим, сочетающий в себе пакетную генерацию и мгновенный ответ. Этот дизайн очень продуман, обеспечивая как эффективность, так и качество взаимодействия.

В частности, система периодически запускает пакетную генерацию в фоновом режиме, генерируя «фоновые диалоги» для всех NPC в текущей сцене. Эти диалоги кэшируются, и когда игроки приближаются к NPC, но еще не начали взаимодействие, NPC будут отображать эти фоновые диалоги, такие как «Отладка кода...», «Чтение документации продукта...» и т. д. Благодаря этому NPC кажутся «живыми», а не статическими моделями.

Однако когда игрок нажимает клавишу E для начала взаимодействия, система немедленно переключается в режим мгновенного ответа. На этом этапе серверная часть вызывает выделенного агента NPC, генерируя персонализированные ответы на основе конкретного сообщения игрока, его исторической памяти и уровня привязанности. Этот процесс происходит в режиме реального времени, что гарантирует, что ответы NPC будут максимально соответствовать вкладу игрока.

```python
# Hybrid mode implementation in main.py
@app.post("/dialogue")
async def dialogue(request: DialogueRequest):
    """Handle player-NPC dialogue (instant response mode)"""
    npc_id = request.npc_id
    player_message = request.player_message
    player_name = request.player_name

    # Get NPC Agent (each NPC has an independent Agent)
    agent = npc_agents.get(npc_id)
    if not agent:
        raise HTTPException(status_code=404, detail="NPC not found")

    # Instantly generate personalized reply
    # Here we don't use batch generation, but call Agent's run method
    reply = agent.run(player_message)

    # Update affection
    affinity_change = relationship_manager.update_affinity(
        npc_id, player_name, player_message, reply
    )

    return {
        "npc_reply": reply,
        "affinity_score": affinity_change["score"],
        "affinity_level": affinity_change["level"]
    }

# Background task: periodically batch generate background dialogues
async def background_dialogue_update():
    """Background task: update NPC background dialogues every 5 minutes"""
    while True:
        try:
            # Use batch generator to generate background dialogues for all NPCs
            batch_generator = get_batch_generator()
            dialogues = batch_generator.generate_batch_dialogues()

            # Update to state manager
            for npc_name, dialogue in dialogues.items():
                state_manager.update_npc_background_dialogue(npc_name, dialogue)

            print(f"✅ Background dialogue update complete: {len(dialogues)} NPCs")
        except Exception as e:
            print(f"❌ Background dialogue update failed: {e}")

        # Wait 5 minutes
        await asyncio.sleep(300)
```

Преимущества этого гибридного режима весьма очевидны:

1. **Снижение затрат**: для фоновых диалогов используется пакетная генерация, один вызов генерирует все диалоги NPC, низкая стоимость.
2. **Гарантия качества**: при взаимодействии с игроком используется мгновенный ответ, каждый ответ персонализирован, высокое качество.
3. **Улучшенный опыт**: у NPC всегда есть «фоновые диалоги», которые выглядят очень оживленно; взаимодействие игроков имеет точные ответы, хороший опыт
4. **Гибкая настройка**: можно динамически регулировать частоту создания пакетов в зависимости от нагрузки на сервер.

Благодаря сочетанию пакетной генерации и мгновенного реагирования мы внедрили эффективную и интеллектуальную систему NPC. В обычных обстоятельствах игроки не ощущают никакой разницы, но затраты на серверную часть и производительность значительно оптимизированы. Этот подход к проектированию также можно применить к другим сценариям, требующим большого количества вызовов ИИ.

## 15.3 Проектирование системы привязанности

### 15.3.1 Классификация уровней воздействия

В Кибер-городе отношение NPC к игрокам меняется в зависимости от взаимодействия. Мы разработали пятиуровневую систему привязанности: от незнакомца до близкого друга, причем каждый уровень имеет разные диапазоны оценок и соответствующие поведенческие характеристики.

Основная идея системы привязанности заключается в следующем: путем количественной оценки отношений между NPC и игроками сделать ответы NPC более реалистичными и многоуровневыми. Когда игроки впервые входят в игру, все NPC относятся к игрокам как-то странно, отвечая вежливо, но отстраненно. По мере развития разговора, если игроки будут вести себя дружелюбно, привязанность NPC будет постепенно возрастать, а ответы станут более сердечными и подробными.

Мы делим привязанность на пять уровней, каждый из которых соответствует диапазону оценок, как показано на рисунке 15.8:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-8.png" alt="" width="85%"/>
  <p>Рисунок 15.8 Классификация уровней воздействия</p>
</div>

- **Незнакомец (0–20 очков)**: NPC только что встретил игрока, отношение вежливое, но соблюдает дистанцию. Ответы краткие, личная информация активно не разглашается.

- **Знакомый (21-40 очков)**: NPC начинает запоминать игрока и готов к простым обменам. Ответы становятся более естественными, иногда мы делимся некоторой информацией, связанной с работой.

- **Дружелюбие (41–60 очков)**: NPC относится к игроку как к другу и готов поделиться дополнительной информацией. Ответы более подробные, будут активно спрашивать о ситуации игрока.

- **Интимный (61-80 очков)**: NPC очень доверяет игроку и готов поделиться личными темами. Ответы полны энтузиазма, предоставят помощь и совет игроку.

- **Близкий друг (81-100 очков)**: NPC относится к игроку как к лучшему другу, говорит обо всем. Ответы очень сердечные, поделятся сокровенными мыслями и чувствами.

Такой дизайн позволяет игрокам отчетливо почувствовать изменение своих отношений с неигровыми персонажами, а также обеспечивает основу для последующего игрового процесса. Например, только после достижения определенного уровня привязанности NPC будут делиться определенной специальной информацией или предоставлять особые задания.

### 15.3.2 Логика расчета привязанности

При расчете привязанности необходимо учитывать множество факторов. Мы не можем просто добавить фиксированную оценку для каждого разговора, в результате чего система будет выглядеть механической и нереалистичной. Хорошая система привязанности должна уметь определять отношение игрока и динамически корректировать оценки в зависимости от содержания разговора.

В Кибер-городе мы используем LLM для анализа содержания разговоров и определения того, является ли отношение игрока дружелюбным, нейтральным или недружелюбным. Затем мы корректируем оценку привязанности на основе результата суждения. Этот процесс происходит автоматически, игрокам не нужно сознательно выбирать варианты, что делает взаимодействие более естественным.

Процесс расчета воздействия показан на рисунке 15.9:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-9.png" alt="" width="85%"/>
  <p>Рисунок 15.9 Процесс расчета влияния</p>
</div>

```python
class RelationshipManager:
    """Affection manager"""

    def __init__(self):
        self.affinity_data = {}  # Store affection data
        self.llm = HelloAgentsLLM()  # For analyzing conversations

    def analyze_sentiment(self, player_message: str, npc_reply: str) -> int:
        """Analyze conversation sentiment, return affection change value"""
        prompt = f"""Analyze the player's attitude in the following conversation:
Player: {player_message}
NPC: {npc_reply}

Please judge if the player's attitude is:
1. Friendly (+5 points): Polite, enthusiastic, expressing thanks or agreement
2. Neutral (+2 points): Normal inquiry or statement
3. Unfriendly (-3 points): Rude, indifferent, critical or negative

Only return the number, no other content."""

        response = self.llm.think([{"role": "user", "content": prompt}])
        try:
            score_change = int(response.strip())
            return max(-3, min(5, score_change))  # Limit between -3 and 5
        except:
            return 2  # Default neutral

    def update_affinity(self, npc_id: str, player_name: str,
                       player_message: str, npc_reply: str) -> dict:
        """Update affection"""
        key = f"{npc_id}_{player_name}"

        # Get current affection
        if key not in self.affinity_data:
            self.affinity_data[key] = {
                "score": 0,
                "level": "Stranger",
                "interaction_count": 0
            }

        # Analyze conversation sentiment
        score_change = self.analyze_sentiment(player_message, npc_reply)

        # Update score
        current_score = self.affinity_data[key]["score"]
        new_score = max(0, min(100, current_score + score_change))

        # Update level
        level = self.get_affinity_level(new_score)

        # Update data
        self.affinity_data[key].update({
            "score": new_score,
            "level": level,
            "interaction_count": self.affinity_data[key]["interaction_count"] + 1
        })

        return self.affinity_data[key]

    def get_affinity_level(self, score: int) -> str:
        """Get affection level based on score"""
        if score <= 20:
            return "Stranger"
        elif score <= 40:
            return "Familiar"
        elif score <= 60:
            return "Friendly"
        elif score <= 80:
            return "Intimate"
        else:
            return "Close Friend"
```

Эта реализация использует LLM для анализа содержания разговора, автоматически оценивая отношение игрока и корректируя привязанность. Такой дизайн делает систему привязанности более интеллектуальной и естественной, игрокам не нужно намеренно угождать NPC, они просто нормально общаются.

### 15.3.3 Привязанность влияет на диалог

Привязанность — это не просто число, она действительно должна влиять на поведение NPC. В Кибергороде мы модифицируем системные подсказки NPC, чтобы они могли настраивать стили ответов в зависимости от текущего уровня привязанности.

Когда привязанность низкая, NPC сохраняют вежливое, но отстраненное отношение. Когда привязанность возрастает, NPC становятся более восторженными и разговорчивыми. Это изменение достигается за счет динамической настройки системных подсказок.

```python
def create_npc_agent_with_affinity(npc_id: str, name: str, role: str,
                                   personality: str, affinity_level: str):
    """Create NPC Agent with affection"""

    # Adjust prompts based on affection level
    affinity_prompts = {
        "Stranger": "You just met this player, be polite but not overly enthusiastic. Keep replies brief and professional.",
        "Familiar": "You already know this player, can have normal exchanges. Replies should be natural and friendly.",
        "Friendly": "You treat this player as a friend, willing to share more information. Replies should be detailed and enthusiastic.",
        "Intimate": "You trust this player very much, can share private topics. Replies should be full of care.",
        "Close Friend": "You treat this player as your best friend, talk about everything. Replies should be cordial and sincere."
    }

    system_prompt = f"""You are {name}, a {role}.
Your personality traits: {personality}

Current relationship with player: {affinity_level}
{affinity_prompts.get(affinity_level, affinity_prompts["Stranger"])}

You work in the Datawhale office, working with colleagues to promote the development of the open source community.
Please reply naturally based on your role, personality, and relationship with the player.
"""

    # Create Agent
    llm = HelloAgentsLLM()
    agent = SimpleAgent(
        name=name,
        llm=llm,
        system_prompt=system_prompt
    )

    return agent
```

Благодаря такому дизайну поведение NPC динамически меняется в зависимости от привязанности. Игроки могут ясно почувствовать, что по мере увеличения количества взаимодействий отношение к ним NPC постепенно меняется, что значительно повышает погружение в игру и делает ее интереснее.

## 15.4 Реализация серверной службы

### 15.4.1 Структура приложения FastAPI

Серверная часть Cyber ​​Town построена с использованием инфраструктуры FastAPI и отвечает за обработку запросов от внешнего интерфейса Godot, вызов агентов NPC HelloAgents, управление состоянием и привязанностью NPC, а также запись журналов. Четкая структура приложения упрощает поддержку и расширение кода.

Наше приложение FastAPI имеет модульную конструкцию, разделяя различные функции на разные файлы, как показано на рисунке 15.10:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-10.png" alt="" width="85%"/>
  <p>Рисунок 15.10 Структура внутреннего приложения</p>
</div>

Начнем с`main.py`, входной файл для приложения FastAPI:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn

from agents import NPCAgentManager
from relationship_manager import RelationshipManager
from state_manager import StateManager
from logger import DialogueLogger
from config import settings

# Create FastAPI application
app = FastAPI(
    title="Cyber Town Back-End Service",
    description="AI NPC dialogue system based on HelloAgents",
    version="1.0.0"
)

# Configure CORS, allow Godot front-end access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production environment should limit specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize各个managers
agent_manager = NPCAgentManager()
relationship_manager = RelationshipManager()
state_manager = StateManager()
dialogue_logger = DialogueLogger()

@app.on_event("startup")
async def startup_event():
    """Initialization on application startup"""
    print("=" * 60)
    print("🎮 Cyber Town back-end service starting...")
    print("=" * 60)

    # Initialize NPC Agents
    agent_manager.initialize_npcs()
    print("✅ NPC Agents initialized")

    # Initialize state manager
    state_manager.initialize_npcs()
    print("✅ State manager initialized")

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running",
        "message": "Cyber Town back-end service is running",
        "version": "1.0.0",
        "npcs": state_manager.get_npc_count()
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )
```

Этот основной программный файл определяет базовую структуру приложения FastAPI, настраивает промежуточное программное обеспечение CORS для разрешения запросов между источниками и инициализирует диспетчеры приложений при запуске. Далее мы реализуем определенные маршруты API.

### 15.4.2 Проектирование маршрутов API

Серверная часть Cyber ​​Town должна предоставить несколько основных конечных точек API для обработки запросов от внешнего интерфейса Godot. Мы добавляем эти маршруты в`main.py`.

**Получить статус NPC**

Этот API возвращает текущий статус всех NPC, включая местоположение, занятость и т. д.:

```python
from models import NPCStatusResponse

@app.get("/npcs/status", response_model=NPCStatusResponse)
async def get_npc_status():
    """Get status of all NPCs"""
    npcs = state_manager.get_all_npc_states()
    return {"npcs": npcs}

@app.get("/npcs/{npc_id}/status")
async def get_single_npc_status(npc_id: str):
    """Get status of a single NPC"""
    npc = state_manager.get_npc_state(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} does not exist")
    return npc
```

**Диалоговый интерфейс**

Это самый основной API, обрабатывающий разговоры между игроком и NPC:

```python
from models import DialogueRequest, DialogueResponse

@app.post("/dialogue", response_model=DialogueResponse)
async def dialogue(request: DialogueRequest):
    """Handle player-NPC dialogue"""
    # 1. Verify NPC exists
    if not agent_manager.has_npc(request.npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {request.npc_id} does not exist")

    # 2. Check if NPC is busy
    if state_manager.is_npc_busy(request.npc_id):
        raise HTTPException(status_code=409, detail=f"NPC {request.npc_id} is talking with another player")

    # 3. Mark NPC as busy
    state_manager.set_npc_busy(request.npc_id, True)

    try:
        # 4. Get current affection
        affinity_info = relationship_manager.get_affinity(
            request.npc_id,
            request.player_name
        )

        # 5. Call Agent to generate reply
        agent = agent_manager.get_agent(request.npc_id, affinity_info["level"])
        reply = agent.run(request.player_message)

        # 6. Update affection
        new_affinity = relationship_manager.update_affinity(
            request.npc_id,
            request.player_name,
            request.player_message,
            reply
        )

        # 7. Record log
        dialogue_logger.log_dialogue(
            npc_id=request.npc_id,
            player_name=request.player_name,
            player_message=request.player_message,
            npc_reply=reply,
            affinity_info=new_affinity
        )

        # 8. Return reply
        return DialogueResponse(
            npc_reply=reply,
            affinity_level=new_affinity["level"],
            affinity_score=new_affinity["score"]
        )

    except Exception as e:
        dialogue_logger.log_error(f"Dialogue processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dialogue processing failed: {str(e)}")

    finally:
        # 9. Release NPC status
        state_manager.set_npc_busy(request.npc_id, False)
```

**Запрос о привязанности**

Этот API позволяет запрашивать привязанность игрока к NPC:

```python
from models import AffinityInfo

@app.get("/affinity/{npc_id}/{player_name}", response_model=AffinityInfo)
async def get_affinity(npc_id: str, player_name: str):
    """Get player-NPC affection"""
    if not agent_manager.has_npc(npc_id):
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} does not exist")

    affinity = relationship_manager.get_affinity(npc_id, player_name)
    return affinity
```

Поток вызова маршрута API показан на рисунке 15.11:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-11.png" alt="" width="85%"/>
  <p>Рисунок 15.11. Процесс вызова API</p>
</div>

### 15.4.3 Система управления состоянием и регистрации

**Государственный менеджер**

Менеджер состояния отвечает за отслеживание текущего состояния каждого NPC, включая местоположение, занятость, текущие действия и т. д. Это важно для предотвращения проблем с параллелизмом, например, чтобы NPC не разговаривал с несколькими игроками одновременно.

```python
# state_manager.py
from typing import Dict, List, Optional
from datetime import datetime

class StateManager:
    """NPC state manager"""

    def __init__(self):
        self.npc_states: Dict[str, dict] = {}

    def initialize_npcs(self):
        """Initialize NPC states"""
        npcs = [
            {
                "npc_id": "zhang_san",
                "name": "Zhang San",
                "role": "Python Engineer",
                "position": {"x": 300, "y": 200}
            },
            {
                "npc_id": "li_si",
                "name": "Li Si",
                "role": "Product Manager",
                "position": {"x": 500, "y": 200}
            },
            {
                "npc_id": "wang_wu",
                "name": "Wang Wu",
                "role": "UI Designer",
                "position": {"x": 700, "y": 200}
            }
        ]

        for npc in npcs:
            self.npc_states[npc["npc_id"]] = {
                **npc,
                "is_busy": False,
                "current_action": "idle",
                "last_interaction": None
            }

    def get_npc_state(self, npc_id: str) -> Optional[dict]:
        """Get NPC state"""
        return self.npc_states.get(npc_id)

    def get_all_npc_states(self) -> List[dict]:
        """Get all NPC states"""
        return list(self.npc_states.values())

    def is_npc_busy(self, npc_id: str) -> bool:
        """Check if NPC is busy"""
        npc = self.npc_states.get(npc_id)
        return npc["is_busy"] if npc else False

    def set_npc_busy(self, npc_id: str, busy: bool):
        """Set NPC busy status"""
        if npc_id in self.npc_states:
            self.npc_states[npc_id]["is_busy"] = busy
            if busy:
                self.npc_states[npc_id]["last_interaction"] = datetime.now().isoformat()

    def get_npc_count(self) -> int:
        """Get NPC count"""
        return len(self.npc_states)
```

**Система регистрации**

Система журналирования реализует двойной вывод: консольный и файловый. Это позволяет удобно просматривать в режиме реального времени и сохранять исторические записи.

```python
# logger.py
import logging
from datetime import datetime
from pathlib import Path

class DialogueLogger:
    """Dialogue logger"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create log file name (by date)
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"dialogue_{today}.log"

        # Configure logging
        self.logger = logging.getLogger("DialogueLogger")
        self.logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def log_dialogue(self, npc_id: str, player_name: str,
                    player_message: str, npc_reply: str,
                    affinity_info: dict):
        """Log dialogue"""
        log_message = f"""
{'='*60}
NPC: {npc_id}
Player: {player_name}
Player message: {player_message}
NPC reply: {npc_reply}
Affection: {affinity_info['level']} ({affinity_info['score']}/100)
Interaction count: {affinity_info['interaction_count']}
{'='*60}
"""
        self.logger.info(log_message)

    def log_error(self, error_message: str):
        """Log error"""
        self.logger.error(error_message)
```

Эта система журналирования отображает содержимое диалога в режиме реального времени на консоли, сохраняя его в файлы. Журналы каждого дня сохраняются в отдельных файлах для удобства последующего анализа.

### 15.4.4 Понимание системы сцен Годо

Прежде чем приступить к созданию игровых сцен, нам необходимо сначала понять основные концепции Godot — Scene и Node. Это самое большое отличие Godot от других игровых движков, а также одна из его самых мощных функций.

**Что такое узел?**

Узлы — это самые основные строительные блоки в Godot. Вы можете думать об узлах как о кубиках Lego, каждый узел имеет определенную функцию. Например, узлы Sprite2D используются для отображения изображений, узлы AudioStreamPlayer используются для воспроизведения звука, а узлы CharacterBody2D используются для управления физическим движением персонажей. Godot предоставляет сотни различных типов узлов, каждый из которых ориентирован на хорошее выполнение одной задачи.

Узлы могут формировать отношения родитель-потомок, образуя древовидную структуру. Родительские узлы могут влиять на дочерние узлы, например, перемещение родительского узла приведет к одновременному перемещению всех дочерних узлов, скрытие родительского узла одновременно скроет все дочерние узлы. Эти иерархические отношения позволяют нам легко организовывать сложные игровые объекты и управлять ими.

**Что такое сцена?**

Сцена — это набор узлов, сохраненный в файле .tscn. Вы можете думать о сцене как о «префабе». Например, мы можем создать сцену «игрока», содержащую все связанные узлы, такие как спрайты персонажей, тела столкновений, звуковые эффекты и т. д. Затем использовать эту сцену в игре несколько раз, при каждом использовании будет создаваться независимый экземпляр.

Сила сцен заключается в их возможности повторного использования и модульности. Мы можем создать экземпляр одной сцены внутри другой сцены, образуя вложенные структуры. Например, основная сцена может содержать сцены игроков, несколько сцен NPC и сцены пользовательского интерфейса. Изменение сцены NPC автоматически повлияет на все экземпляры NPC, что значительно упростит разработку и обслуживание.

**Простой пример**

Давайте воспользуемся простым примером, чтобы понять сцены и узлы. Предположим, мы хотим создать сцену «игрока»:

```
Player (CharacterBody2D)  ← Root node, responsible for physics movement
├─ AnimatedSprite2D       ← Child node, displays character animation
├─ CollisionShape2D       ← Child node, defines collision shape
└─ Camera2D               ← Child node, camera follows player
```

Эта сцена содержит 4 узла, образующих древовидную структуру. CharacterBody2D — корневой узел, остальные три — его дочерние узлы. Мы можем добавить скрипты к каждому узлу, чтобы контролировать его поведение, или добавить скрипт к корневому узлу, чтобы координировать все дочерние узлы.

Когда мы создаем экземпляр этой сцены Player в главной сцене, Годо создает копию всего этого дерева узлов. Мы можем создать несколько экземпляров игрока, каждый из которых независим со своей позицией, состоянием и поведением.

**Преимущества создания экземпляра сцены**

В Кибер-городе есть три NPC: Чжан Сан, Ли Си и Ван Ву. Без использования системы сцен нам пришлось бы создавать узлы, устанавливать свойства и писать сценарии для каждого NPC отдельно, что приводило бы к большому количеству повторяющейся работы. Используя систему сцен, нам нужно всего лишь создать общую сцену NPC, а затем создать ее экземпляр три раза, задав разные имена и информацию о роли через параметры сценария.

Преимущество этого дизайна: если мы хотим добавить новую функцию ко всем NPC (например, отображение пузырей диалогов над их головами), нам нужно только изменить сцену NPC, и все экземпляры автоматически получат эту функцию.

## 15.5. Создание игровой сцены «Годо»

**Why Choose Godot as the Game Engine?**

Среди множества игровых движков мы выбрали Godot 4.5 в качестве внешнего движка, главным образом, исходя из следующих соображений:

(1) **Годо обладает естественными преимуществами в разработке 2D-игр**. Cyber ​​Town — это 2D-игра в пиксельном стиле с видом сверху. 2D-движок Godot очень развит и предоставляет типы узлов, специально разработанные для 2D-игр, такие как TileMap, AnimatedSprite2D, CharacterBody2D и т. д. Эффективность разработки намного выше, чем у таких движков, как Unity. Система сцен Godot позволяет нам инкапсулировать такие элементы, как игроки, неигровые персонажи и пользовательский интерфейс, в независимые сцены, а затем создавать их экземпляры в основной сцене. Этот компонентный дизайн очень подходит для наших нужд.

(2) **Godot имеет полностью открытый исходный код и бесплатен**. Godot использует лицензию MIT без лицензионных отчислений или распределения доходов, что очень удобно для учебных проектов и проектов с открытым исходным кодом. Вы можете свободно изменять исходный код движка и коммерциализировать игры, не беспокоясь о проблемах с лицензированием. Напротив, несмотря на то, что Unity является мощной платформой, в 2024 году она ввела политику взимания платы за выполнение, что вызвало широкую полемику в сообществе разработчиков.

(3) **У Годо чрезвычайно низкая стоимость обучения**. Godot использует GDScript в качестве основного языка сценариев, динамически типизированного языка, похожего на Python, с кратким и простым для понимания синтаксисом и очень легкой кривой обучения. For readers already familiar with Python, learning GDScript has almost no barrier - variable declarations, function definitions, control flow, and other syntax are highly similar to Python. You can even start writing game scripts within a few hours. Древовидная структура узлов Godot также очень интуитивно понятна, вы можете визуально увидеть иерархические отношения сцены в редакторе, что очень удобно для новичков.

(4) **Godot очень просто интегрируется с серверной частью Python**. Godot имеет встроенный узел HTTPRequest, который может легко взаимодействовать с серверными модулями FastAPI через HTTP. Нам нужно всего лишь создать клиентский скрипт API, инкапсулирующий все вызовы API для вызова серверных возможностей ИИ в игре. Такая архитектура разделения внешнего и внутреннего компонентов позволяет нам независимо разрабатывать и тестировать игровую логику и логику искусственного интеллекта, что значительно повышает эффективность разработки.

Конечно, у Годо есть и некоторые ограничения. Например, 3D-возможности Godot по-прежнему отстают от Unreal Engine и Unity. Если вы хотите разрабатывать крупномасштабные 3D-игры, возможно, вам придется рассмотреть другие движки. Но для 2D-игр, инди-игр и обучающих проектов Godot — отличный выбор.

### 15.5.1 Дизайн сцены и организация ресурсов

Разобравшись с системой сцен Годо, давайте посмотрим на дизайн сцен Кибер-города. Вся игра состоит из четырех основных сцен: Main (основная сцена), Player (игрок), NPC (неигровой персонаж) и DialogueUI (диалоговый интерфейс). Каждая сцена представляет собой независимый модуль, который можно редактировать и тестировать отдельно, а затем объединять в полноценную игру.

Организация сцены Кибер-города имеет модульную конструкцию. Сначала мы создаем три базовые сцены: Player (игрок), NPC (неигровой персонаж) и DialogueUI (диалоговый интерфейс). Затем в Main (основная сцена) мы создаем экземпляры и объединяем эти сцены. Особо стоит отметить, что все три NPC (Чжан Сан, Ли Си, Ван Ву) являются экземплярами одной и той же сцены NPC, просто с разной ролевой информацией, заданной через параметры сценария.

Давайте сначала посмотрим на структуру четырех основных сцен, как показано на рисунке 15.12:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-12.png" alt="" width="85%"/>
  <p>Рисунок 15.12. Четыре основных сцены кибергорода</p>
</div>

На этой диаграмме показаны четыре независимые сцены и их внутренняя структура. **Сцена 1 (основная)** — это основная сцена, содержащая фоновое изображение (Sprite2D), экземпляр игрока, узел организации NPC (с тремя экземплярами NPC ниже), экземпляр диалогового интерфейса, узел организации стен и фоновую музыку. Обратите внимание, что Player, NPC_Zhang, NPC_Li, NPC_Wang и DialogueUI здесь являются экземплярами сцены, а не обычными узлами. **Сцена 2 (Игрок)** определяет структуру персонажа игрока, включая анимацию, столкновение, камеру и два узла звуковых эффектов. **Сцена 3 (NPC)** — это общий шаблон. Чжан Сан, Ли Си и Ван Ву являются экземплярами этой сцены, содержащей столкновение, анимацию, область взаимодействия и две метки. **Сцена 4 (DialogueUI)** — это узел CanvasLayer, содержащий Panel и различные элементы пользовательского интерфейса.

Процесс создания сцены можно понять следующим образом: мы создали файл сцены NPC.tscn в редакторе Godot, определяя структуру узла NPC. Затем в главной сцене мы трижды «создали экземпляр» этой сцены NPC, создав три независимые копии с именами NPC_Zhang, NPC_Li и NPC_Wang соответственно. Каждая копия имеет свою собственную позицию и состояние, но они имеют одну и ту же структуру узла. Если мы изменим NPC.tscn, например добавив к NPC новый узел звукового эффекта, все три экземпляра автоматически получат этот звуковой эффект.

Шаги по созданию этих сцен в Godot следующие:

1. **Создание сцены игрока**: создайте новую сцену, выберите CharacterBody2D в качестве корневого узла, добавьте дочерние узлы AnimatedSprite2D, CollisionShape2D, Camera2D, InteractSound и RunningSound, сохраните как Player.tscn.

2. **Создание сцены NPC**: создайте новую сцену, выберите CharacterBody2D в качестве корневого узла, добавьте дочерние узлы CollisionShape2D, AnimatedSprite2D, InteractionArea (Area2D с CollisionShape2D ниже), NameLabel и DialogueLabel, сохраните как NPC.tscn.

3. **Создание сцены DialogueUI**: создайте новую сцену, выберите CanvasLayer в качестве корневого узла, добавьте дочерний узел Panel, в разделе Panel добавьте NPCName, NPTitle, DialogueText (RichTextLabel), PlayerInput (LineEdit), SendButton и CloseButton, сохраните как DialogueUI.tscn.

4. **Создать главную сцену**: создайте новую сцену, выберите Node2D в качестве корневого узла, добавьте фон (Sprite2D) в качестве фонового изображения, в разделе «Фон» добавьте украшение кита, затем создайте экземпляр сцены Player, создайте узел NPC и трижды создайте экземпляр сцены NPC под ним, создайте экземпляр сцены DialogueUI, создайте узел Walls для организации столкновений со стенами, наконец, добавьте AudioStreamPlayer для воспроизведения фоновой музыки.

Преимущества такого метода организации сцен: каждая сцена независима и может тестироваться отдельно; NPC используют экземпляры одной и той же сцены, одно изменение влияет на всех NPC; Сцены обмениваются данными посредством сигналов с низкой связью, просты в обслуживании и расширении.

### 15.5.2 Реализация управления игроком

Персонаж игрока — один из самых важных элементов в игре. Нам необходимо реализовать управление движением WASD, переключение анимации, обнаружение столкновений, взаимодействие с NPC и систему звуковых эффектов.

Структура сцены игрока включает в себя: CharacterBody2D в качестве корневого узла, отвечающего за физическое движение и столкновение; AnimatedSprite2D, отображающий анимацию персонажей; CollisionShape2D, определяющий форму столкновения; Camera2D, следующий за игроком; два AudioStreamPlayer воспроизводят звуковые эффекты взаимодействия и звуковые эффекты ходьбы соответственно.

Скрипт управления плеером`player.gd`реализует логику движения, взаимодействия и звуковых эффектов:

```python
extends CharacterBody2D

# Movement speed
@export var speed: float = 200.0

# Currently interactable NPC
var nearby_npc: Node = null

# Interaction state (disable movement during interaction)
var is_interacting: bool = false

# Node references
@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var camera: Camera2D = $Camera2D

# Sound effect references
@onready var interact_sound: AudioStreamPlayer = null
@onready var running_sound: AudioStreamPlayer = null

# Walking sound effect state
var is_playing_running_sound: bool = false

func _ready():
    # Add to player group (important! NPCs need this group to identify player)
    add_to_group("player")

    # Get sound effect nodes (optional, won't error if doesn't exist)
    interact_sound = get_node_or_null("InteractSound")
    running_sound = get_node_or_null("RunningSound")

    # Enable camera
    camera.enabled = true

    # Play default animation
    if animated_sprite.sprite_frames != null and animated_sprite.sprite_frames.has_animation("idle"):
        animated_sprite.play("idle")

func _physics_process(_delta: float):
    # If interacting, disable movement
    if is_interacting:
        velocity = Vector2.ZERO
        move_and_slide()
        # Play idle animation
        if animated_sprite.sprite_frames != null and animated_sprite.sprite_frames.has_animation("idle"):
            animated_sprite.play("idle")
        # Stop walking sound effect
        stop_running_sound()
        return

    # Get input direction
    var input_direction = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")

    # Set velocity
    velocity = input_direction * speed

    # Move
    move_and_slide()

    # Update animation and direction
    update_animation(input_direction)

    # Update walking sound effect
    update_running_sound(input_direction)

func update_animation(direction: Vector2):
    """Update character animation (supports 4 directions)"""
    if animated_sprite.sprite_frames == null:
        return

    # Play animation based on movement direction
    if direction.length() > 0:
        # Moving - determine main direction
        if abs(direction.x) > abs(direction.y):
            # Left-right movement
            if direction.x > 0:
                # Right
                if animated_sprite.sprite_frames.has_animation("walk_right"):
                    animated_sprite.play("walk_right")
                    animated_sprite.flip_h = false
                elif animated_sprite.sprite_frames.has_animation("walk"):
                    animated_sprite.play("walk")
                    animated_sprite.flip_h = false
            else:
                # Left
                if animated_sprite.sprite_frames.has_animation("walk_left"):
                    animated_sprite.play("walk_left")
                    animated_sprite.flip_h = false
                elif animated_sprite.sprite_frames.has_animation("walk"):
                    animated_sprite.play("walk")
                    animated_sprite.flip_h = true
        else:
            # Up-down movement
            if direction.y > 0:
                # Down
                if animated_sprite.sprite_frames.has_animation("walk_down"):
                    animated_sprite.play("walk_down")
                elif animated_sprite.sprite_frames.has_animation("walk"):
                    animated_sprite.play("walk")
            else:
                # Up
                if animated_sprite.sprite_frames.has_animation("walk_up"):
                    animated_sprite.play("walk_up")
                elif animated_sprite.sprite_frames.has_animation("walk"):
                    animated_sprite.play("walk")
    else:
        # Idle
        if animated_sprite.sprite_frames.has_animation("idle"):
            animated_sprite.play("idle")

func _input(event: InputEvent):
    # Press E key to interact with NPC
    if event is InputEventKey:
        if event.pressed and not event.echo:
            if event.keycode == KEY_E or event.keycode == KEY_ENTER:
                if nearby_npc != null:
                    interact_with_npc()

func interact_with_npc():
    """Interact with nearby NPC"""
    if nearby_npc != null:
        # Play interaction sound effect
        if interact_sound:
            interact_sound.play()

        # Send signal to dialogue system
        get_tree().call_group("dialogue_system", "start_dialogue", nearby_npc.npc_name)

func set_nearby_npc(npc: Node):
    """Set nearby NPC"""
    nearby_npc = npc

func set_interacting(interacting: bool):
    """Set interaction state"""
    is_interacting = interacting
    if interacting:
        # Stop walking sound effect
        stop_running_sound()

func update_running_sound(direction: Vector2):
    """Update walking sound effect"""
    if running_sound == null:
        return

    # If moving
    if direction.length() > 0:
        # If sound effect not playing yet, start playing
        if not is_playing_running_sound:
            running_sound.play()
            is_playing_running_sound = true
    else:
        # If stopped moving, stop sound effect
        stop_running_sound()

func stop_running_sound():
    """Stop walking sound effect"""
    if running_sound and is_playing_running_sound:
        running_sound.stop()
        is_playing_running_sound = false
```

Этот скрипт реализует полный контроль над игроком. Игроки используют клавиши WASD (или клавиши со стрелками) для перемещения, а персонаж воспроизводит соответствующую анимацию в четырех направлениях (ходьба вверх/вниз/влево/вправо) в зависимости от направления движения. Когда игрок приближается к NPC, NPC вызывает`set_nearby_npc()`чтобы установить себя как интерактивный объект, и игрок может нажать клавишу E, чтобы вызвать взаимодействие. Во время взаимодействия воспроизводятся звуковые эффекты и`call_group()`уведомляет диалоговую систему о начале разговора. Во время диалога,`set_interacting(true)`отключает движение игрока, которое восстанавливается после завершения диалога. Звуковые эффекты ходьбы автоматически воспроизводятся, когда игрок движется, и автоматически прекращаются, когда он останавливается.

### 15.5.3 Поведение и взаимодействие NPC

Неигровым персонажам необходимо реализовать три основные функции: случайное патрулирование и блуждание по сцене, реагирование на взаимодействия игроков и отображение пузырей диалогов. Мы используем Area2D, чтобы определить, находится ли игрок рядом с NPC. Когда игрок входит в зону взаимодействия, игрок получает уведомление, и нажатие клавиши E начинает разговор.

Структура сцены NPC включает в себя: CharacterBody2D в качестве корневого узла; CollisionShape2D определяет форму столкновения NPC; AnimatedSprite2D отображает анимацию NPC; InteractionArea (Area2D) обнаруживает, что игрок входит в диапазон взаимодействия, а CollisionShape2D ниже определяет диапазон взаимодействия; NameLabel отображает имя NPC; DialogueLabel отображает диалоговое окно.

Скрипт NPC`npc.gd`реализует логику патрулирования, взаимодействия и диалогового пузыря:

```python
extends CharacterBody2D

# NPC information
@export var npc_name: String = "Zhang San"
@export var npc_title: String = "Python Engineer"

# NPC appearance configuration
@export var sprite_frames: SpriteFrames = null  # Custom sprite frame resource

# NPC movement configuration
@export var move_speed: float = 50.0  # Movement speed
@export var wander_enabled: bool = true  # Whether to enable patrol
@export var wander_range: float = 200.0  # Patrol range
@export var wander_interval_min: float = 3.0  # Minimum patrol interval (seconds)
@export var wander_interval_max: float = 8.0  # Maximum patrol interval (seconds)

# Current dialogue content (obtained from back-end)
var current_dialogue: String = ""

# Node references
@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var interaction_area: Area2D = $InteractionArea
@onready var name_label: Label = $NameLabel
@onready var dialogue_label: Label = $DialogueLabel

# Player reference
var player: Node = null

# Patrol-related variables
var wander_target: Vector2 = Vector2.ZERO  # Patrol target position
var wander_timer: float = 0.0  # Patrol timer
var is_wandering: bool = false  # Whether currently patrolling
var is_interacting: bool = false  # Whether currently interacting with player
var spawn_position: Vector2 = Vector2.ZERO  # Spawn position

func _ready():
    # Add to npcs group
    add_to_group("npcs")

    # Set NPC name
    name_label.text = npc_name

    # Connect interaction area signals
    interaction_area.body_entered.connect(_on_body_entered)
    interaction_area.body_exited.connect(_on_body_exited)

    # Initialize dialogue label
    dialogue_label.text = ""
    dialogue_label.visible = false

    # Set custom sprite frames (if any)
    if sprite_frames != null:
        animated_sprite.sprite_frames = sprite_frames

    # Play default animation
    if animated_sprite.sprite_frames != null and animated_sprite.sprite_frames.has_animation("idle"):
        animated_sprite.play("idle")

    # Record spawn position
    spawn_position = global_position

    # Initialize patrol timer
    if wander_enabled:
        wander_timer = randf_range(wander_interval_min, wander_interval_max)
        choose_new_wander_target()

func _on_body_entered(body: Node2D):
    """Player enters interaction range"""
    if body.is_in_group("player"):
        player = body

        if player.has_method("set_nearby_npc"):
            player.set_nearby_npc(self)

func _on_body_exited(body: Node2D):
    """Player leaves interaction range"""
    if body.is_in_group("player"):
        if player != null and player.has_method("set_nearby_npc"):
            player.set_nearby_npc(null)
        player = null

func update_dialogue(dialogue: String):
    """Update NPC dialogue content"""
    current_dialogue = dialogue
    dialogue_label.text = dialogue
    dialogue_label.visible = true

    # Hide dialogue after 10 seconds
    await get_tree().create_timer(10.0).timeout
    dialogue_label.visible = false

func _physics_process(delta: float):
    """Physics update - handle movement"""
    # If interacting with player, stop movement
    if is_interacting:
        velocity = Vector2.ZERO
        move_and_slide()
        # Play idle animation
        if animated_sprite.sprite_frames != null and animated_sprite.sprite_frames.has_animation("idle"):
            animated_sprite.play("idle")
        return

    # If patrol not enabled, don't move
    if not wander_enabled:
        return

    # Update patrol timer
    wander_timer -= delta

    # If timer ends, choose new target and start moving
    if wander_timer <= 0:
        choose_new_wander_target()
        wander_timer = randf_range(wander_interval_min, wander_interval_max)

    # If patrolling, move to target
    if is_wandering:
        # Check if reached target
        if global_position.distance_to(wander_target) < 10:
            # Reached target, stop movement
            is_wandering = false
            velocity = Vector2.ZERO
            move_and_slide()
            # Play idle animation
            if animated_sprite.sprite_frames != null and animated_sprite.sprite_frames.has_animation("idle"):
                animated_sprite.play("idle")
        else:
            # Continue moving to target
            var direction = (wander_target - global_position).normalized()
            velocity = direction * move_speed
            move_and_slide()
            # Update animation
            update_animation(direction)
    else:
        # Stop movement
        velocity = Vector2.ZERO
        move_and_slide()
        # Play idle animation
        if animated_sprite.sprite_frames != null and animated_sprite.sprite_frames.has_animation("idle"):
            animated_sprite.play("idle")

func choose_new_wander_target():
    """Choose new patrol target"""
    # Randomly choose a point near spawn position
    var offset = Vector2(
        randf_range(-wander_range, wander_range),
        randf_range(-wander_range, wander_range)
    )
    wander_target = spawn_position + offset
    is_wandering = true

func update_animation(direction: Vector2):
    """Update animation"""
    if animated_sprite.sprite_frames == null:
        return

    if direction.length() > 0:
        # Movement animation
        if abs(direction.x) > abs(direction.y):
            # Left-right movement
            if direction.x > 0:
                if animated_sprite.sprite_frames.has_animation("walk_right"):
                    animated_sprite.play("walk_right")
                elif animated_sprite.sprite_frames.has_animation("walk"):
                    animated_sprite.play("walk")
                    animated_sprite.flip_h = false
            else:
                if animated_sprite.sprite_frames.has_animation("walk_left"):
                    animated_sprite.play("walk_left")
                elif animated_sprite.sprite_frames.has_animation("walk"):
                    animated_sprite.play("walk")
                    animated_sprite.flip_h = true
        else:
            # Up-down movement
            if direction.y > 0:
                if animated_sprite.sprite_frames.has_animation("walk_down"):
                    animated_sprite.play("walk_down")
                elif animated_sprite.sprite_frames.has_animation("walk"):
                    animated_sprite.play("walk")
            else:
                if animated_sprite.sprite_frames.has_animation("walk_up"):
                    animated_sprite.play("walk_up")
                elif animated_sprite.sprite_frames.has_animation("walk"):
                    animated_sprite.play("walk")
    else:
        # Idle animation
        if animated_sprite.sprite_frames.has_animation("idle"):
            animated_sprite.play("idle")

func set_interacting(interacting: bool):
    """Set interaction state"""
    is_interacting = interacting
```

Этот скрипт реализует полное поведение NPC. NPC случайным образом патрулируют территорию.`wander_range`вокруг места своего появления, выбирая новую целевую точку и перемещаясь туда каждый раз.`wander_interval_min`к`wander_interval_max`секунды. Во время движения воспроизводится анимация в 4 направлениях (ходьба_вверх/вниз/влево/вправо), а при достижении цели они останавливаются и воспроизводят анимацию простоя. Когда игрок входит в область взаимодействия, NPC вызывает игрока`set_nearby_npc(self)`метод, устанавливающий себя как интерактивный объект. После того, как игрок нажмет клавишу E, диалоговая система вызывает NPC.`set_interacting(true)`метод, и NPC перестает двигаться. После завершения диалога`set_interacting(false)`вызывается, и NPC возобновляет патрулирование. Основная сцена периодически вызывает`update_dialogue()`метод обновления диалогового окна NPC, отображающий содержимое автономного диалога между NPC.

## 15.6 Реализация внешней и внутренней связи

### 15.6.1 Инкапсуляция клиента API

Интерфейс Godot должен взаимодействовать с серверной частью FastAPI через HTTP. Создаем API-клиентский скрипт`api_client.gd`, инкапсулируя все вызовы API, и установить его как синглтон AutoLoad (автозагрузки), чтобы другие сценарии могли его удобно использовать.

Клиент API использует узел HTTPRequest Godot для отправки HTTP-запросов. HTTPRequest — асинхронный узел, который не блокирует игру после отправки запросов, а уведомляет о завершении запроса посредством сигналов. Это обеспечивает плавность игры — даже при высокой задержке в сети нет подтормаживаний. Мы используем механизм сигналов для уведомления других сценариев об ответах API, а не с помощью await, что позволяет нескольким сценариям одновременно прослушивать один и тот же ответ API.

```python
# api_client.gd
extends Node

# Signal definitions
signal chat_response_received(npc_name: String, message: String)
signal chat_error(error_message: String)
signal npc_status_received(dialogues: Dictionary)
signal npc_list_received(npcs: Array)

# HTTP request nodes
var http_chat: HTTPRequest
var http_status: HTTPRequest
var http_npcs: HTTPRequest

func _ready():
    # Create HTTP request nodes
    http_chat = HTTPRequest.new()
    http_status = HTTPRequest.new()
    http_npcs = HTTPRequest.new()

    add_child(http_chat)
    add_child(http_status)
    add_child(http_npcs)

    # Connect signals
    http_chat.request_completed.connect(_on_chat_request_completed)
    http_status.request_completed.connect(_on_status_request_completed)
    http_npcs.request_completed.connect(_on_npcs_request_completed)

# ==================== Chat API ====================
func send_chat(npc_name: String, message: String) -> void:
    """Send chat request"""
    var data = {
        "npc_name": npc_name,
        "message": message
    }

    var json_string = JSON.stringify(data)
    var headers = ["Content-Type: application/json"]

    var error = http_chat.request(
        Config.API_CHAT,
        headers,
        HTTPClient.METHOD_POST,
        json_string
    )

    if error != OK:
        print("[ERROR] Failed to send chat request: ", error)
        chat_error.emit("Network request failed")

func _on_chat_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    """Handle chat response"""
    if response_code != 200:
        print("[ERROR] Chat request failed: HTTP ", response_code)
        chat_error.emit("Server error: " + str(response_code))
        return

    var json = JSON.new()
    var parse_result = json.parse(body.get_string_from_utf8())

    if parse_result != OK:
        print("[ERROR] Failed to parse response")
        chat_error.emit("Response parsing failed")
        return

    var response = json.data

    if response.has("success") and response["success"]:
        var npc_name = response["npc_name"]
        var msg = response["message"]
        print("[INFO] Received NPC reply: ", npc_name, " -> ", msg)
        chat_response_received.emit(npc_name, msg)
    else:
        chat_error.emit("Chat failed")

# ==================== NPC Status API ====================
func get_npc_status() -> void:
    """Get NPC status"""
    # Check if request is being processed
    if http_status.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
        print("[WARN] NPC status request is being processed, skipping this request")
        return

    var error = http_status.request(Config.API_NPC_STATUS)

    if error != OK:
        print("[ERROR] Failed to get NPC status: ", error)

func _on_status_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    """Handle NPC status response"""
    if response_code != 200:
        print("[ERROR] NPC status request failed: HTTP ", response_code)
        return

    var json = JSON.new()
    var parse_result = json.parse(body.get_string_from_utf8())

    if parse_result != OK:
        print("[ERROR] Failed to parse NPC status")
        return

    var response = json.data

    if response.has("dialogues"):
        var dialogues = response["dialogues"]
        print("[INFO] Received NPC status update: ", dialogues.size(), " NPCs")
        npc_status_received.emit(dialogues)

# ==================== NPC List API ====================
func get_npc_list() -> void:
    """Get NPC list"""
    var error = http_npcs.request(Config.API_NPCS)

    if error != OK:
        print("[ERROR] Failed to get NPC list: ", error)

func _on_npcs_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    """Handle NPC list response"""
    if response_code != 200:
        print("[ERROR] NPC list request failed: HTTP ", response_code)
        return

    var json = JSON.new()
    var parse_result = json.parse(body.get_string_from_utf8())

    if parse_result != OK:
        print("[ERROR] Failed to parse NPC list")
        return

    var response = json.data

    if response.has("npcs"):
        var npcs = response["npcs"]
        print("[INFO] Received NPC list: ", npcs.size(), " NPCs")
        npc_list_received.emit(npcs)
```

Этот API-клиент инкапсулирует три основные функции: отправить запрос в чат (`send_chat`), получить статус NPC (`get_npc_status`) и получить список NPC (`get_npc_list`). Все HTTP-запросы являются асинхронными и уведомляют о результатах ответа посредством сигналов. Мы создали независимые узлы HTTPRequest для каждого API, что позволяет отправлять несколько запросов одновременно, не мешая друг другу. URL-адреса API получаются из синглтона Config для удобного унифицированного управления. Диалоговая система слушает`chat_response_received`сигнал для получения ответов NPC, и основная сцена слушает`npc_status_received`сигнал для обновления диалоговых пузырей NPC.

### 15.6.2 Реализация диалогового пользовательского интерфейса

Интерфейс диалога — это интерфейс взаимодействия игрока и NPC. Нам нужно создать простое и красивое диалоговое окно, содержащее имя NPC, заголовок, отображение содержимого диалога, поле ввода и кнопки.

Структура пользовательского интерфейса диалога показана на рисунке 15.13:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-13.png" alt="" width="85%"/>
  <p>Рисунок 15.13 Структура пользовательского интерфейса диалогового окна</p>
</div>

Дизайн диалогового пользовательского интерфейса очень прост. DialogueUI — это узел CanvasLayer, то есть он всегда будет отображаться поверх игрового экрана и не будет закрыт другими игровыми объектами. Панель — это фон диалогового окна, закрепленный в нижней части экрана. В панели Panel размещены непосредственно 6 элементов пользовательского интерфейса: NPCName отображает имя NPC, NPTitle отображает заголовок, DialogueText использует RichTextLabel для отображения содержимого диалога (поддерживает расширенный текстовый формат), PlayerInput — это LineEdit для ввода данных игроком, а SendButton и CloseButton используются для отправки сообщений и закрытия диалогового окна соответственно.

Скрипт диалогового пользовательского интерфейса`dialogue_ui.gd`реализует логику диалогового интерфейса:

```python
# dialogue_ui.gd
extends CanvasLayer

# UI node references
@onready var panel = $Panel
@onready var npc_name_label = $Panel/NPCName
@onready var npc_title_label = $Panel/NPCTitle
@onready var dialogue_text = $Panel/DialogueText
@onready var input_field = $Panel/PlayerInput
@onready var send_button = $Panel/SendButton
@onready var close_button = $Panel/CloseButton

# API client
var api_client: Node = null

# Current NPC in dialogue
var current_npc_name: String = ""

func _ready():
    # Hide dialogue box on initialization
    visible = false

    # Connect button signals
    send_button.pressed.connect(_on_send_button_pressed)
    close_button.pressed.connect(_on_close_button_pressed)
    input_field.text_submitted.connect(_on_text_submitted)

    # Get API client
    api_client = get_node_or_null("/root/APIClient")

func start_dialogue(npc_name: String):
    """Start dialogue with NPC"""
    current_npc_name = npc_name

    # Set NPC information
    npc_name_label.text = npc_name
    npc_title_label.text = get_npc_title(npc_name)

    # Clear dialogue content
    dialogue_text.clear()
    dialogue_text.append_text("[color=gray]Conversation with " + npc_name + " started...[/color]\n")

    # Clear input field
    input_field.text = ""

    # Show dialogue box
    show_dialogue()

    # Focus input field
    input_field.grab_focus()

func show_dialogue():
    """Show dialogue box"""
    visible = true

    # Notify player to enter interaction state (disable movement)
    var player = get_tree().get_first_node_in_group("player")
    if player and player.has_method("set_interacting"):
        player.set_interacting(true)

func hide_dialogue():
    """Hide dialogue box"""
    visible = false
    current_npc_name = ""

    # Notify player to exit interaction state (enable movement)
    var player = get_tree().get_first_node_in_group("player")
    if player and player.has_method("set_interacting"):
        player.set_interacting(false)

func _on_send_button_pressed():
    """Send button clicked"""
    send_message()

func _on_close_button_pressed():
    """Close button clicked"""
    hide_dialogue()

func _on_text_submitted(_text: String):
    """Input field enter pressed"""
    send_message()

func send_message():
    """Send message"""
    var message = input_field.text.strip_edges()

    if message.is_empty():
        return

    if current_npc_name.is_empty():
        return

    # Display player message
    dialogue_text.append_text("\n[color=cyan]Player:[/color] " + message + "\n")

    # Clear input field
    input_field.text = ""

    # Disable input
    input_field.editable = false
    send_button.disabled = true

    # Send API request
    if api_client:
        api_client.send_chat_request(current_npc_name, message)

func on_chat_response_received(npc_name: String, response: String):
    """Received NPC reply"""
    if npc_name == current_npc_name:
        # Display NPC reply
        dialogue_text.append_text("[color=yellow]" + npc_name + ":[/color] " + response + "\n")

        # Enable input
        input_field.editable = true
        send_button.disabled = false
        input_field.grab_focus()

func get_npc_title(npc_name: String) -> String:
    """Get NPC title"""
    var titles = {
        "Zhang San": "Python Engineer",
        "Li Si": "Product Manager",
        "Wang Wu": "UI Designer"
    }
    return titles.get(npc_name, "")
```

This dialogue UI implements complete dialogue functionality. Players can input and send messages, and the UI uses RichTextLabel's append_text method to display dialogue content, supporting rich text format (colors, bold, etc.). All API calls are asynchronous, disabling the input box while waiting for responses to prevent duplicate sends. Когда отображается диалоговое окно, оно уведомляет игрока о необходимости войти в состояние взаимодействия, отключая движение, и восстанавливает движение при закрытии.

### 15.6.3 Интеграция основной сцены

Наконец, нам нужно интегрировать все функции в основную сцену: управление игроком, взаимодействие с NPC, диалоговый интерфейс и обновление статуса NPC. Сценарий основной сцены`main.gd`координирует эти компоненты и периодически получает статус NPC из серверной части для обновления диалоговых пузырей NPC.

```python
# main.gd
extends Node2D

# NPC node references
@onready var npc_zhang: Node2D = $NPCs/NPC_Zhang
@onready var npc_li: Node2D = $NPCs/NPC_Li
@onready var npc_wang: Node2D = $NPCs/NPC_Wang

# API client
var api_client: Node = null

# NPC status update timer
var status_update_timer: float = 0.0

func _ready():
    print("[INFO] Main scene initialization")

    # Get API client
    api_client = get_node_or_null("/root/APIClient")
    if api_client:
        api_client.npc_status_received.connect(_on_npc_status_received)

        # Immediately get NPC status once
        api_client.get_npc_status()
    else:
        print("[ERROR] API client not found")

func _process(delta: float):
    # Periodically update NPC status
    status_update_timer += delta
    if status_update_timer >= Config.NPC_STATUS_UPDATE_INTERVAL:
        status_update_timer = 0.0
        if api_client:
            api_client.get_npc_status()

func _on_npc_status_received(dialogues: Dictionary):
    """Received NPC status update"""
    print("[INFO] Update NPC status: ", dialogues)

    # Update each NPC's dialogue
    for npc_name in dialogues:
        var dialogue = dialogues[npc_name]
        update_npc_dialogue(npc_name, dialogue)

func update_npc_dialogue(npc_name: String, dialogue: String):
    """Update specified NPC's dialogue"""
    var npc_node = get_npc_node(npc_name)
    if npc_node and npc_node.has_method("update_dialogue"):
        npc_node.update_dialogue(dialogue)

func get_npc_node(npc_name: String) -> Node2D:
    """Get NPC node by name"""
    match npc_name:
        "Zhang San":
            return npc_zhang
        "Li Si":
            return npc_li
        "Wang Wu":
            return npc_wang
        _:
            return null
```

Основная функция сценария основной сцены — периодическое получение статуса NPC из серверной части. В`_ready()`, мы получаем ссылку на синглтон APIClient и подключаем`npc_status_received`сигнал. Тогда мы сразу звоним`get_npc_status()`чтобы получить статус NPC один раз. В`_process()`, мы используем таймер для вызова`get_npc_status()`каждый`Config.NPC_STATUS_UPDATE_INTERVAL`секунд (по умолчанию 30 секунд). При получении обновлений статуса NPC`_on_npc_status_received()`функция обратного вызова обходит всех NPC и вызывает их`update_dialogue()`метод обновления диалоговых пузырей. Таким образом, даже если игрок не взаимодействует с NPC, он все равно сможет видеть автономный диалог между NPC.

Полный процесс взаимодействия между интерфейсом и сервером показан на рисунке 15.14:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-14.png" alt="" width="85%"/>
  <p>Рисунок 15.14. Полный процесс взаимодействия между внешним и внутренним сервером</p>
</div>

На данный момент все функции внешнего и внутреннего взаимодействия реализованы. Игроки могут свободно перемещаться по игре, взаимодействовать с неигровыми персонажами и разговаривать на естественном языке. Между тем, основная сцена периодически получает статус NPC из серверной части, обновляет пузыри диалогов NPC и отображает автономный диалог между NPC. Вся система использует сигнальный механизм для связи со слабой связью между компонентами, что упрощает ее обслуживание и расширение.

## 15.7 Резюме и перспективы

### 15.7.1 Обзор главы

В этой главе мы завершили полноценный проект города с искусственным интеллектом — Кибергород. Этот проект объединяет платформу HelloAgents с игровым движком Godot для создания яркого виртуального мира. Давайте рассмотрим основной материал, который мы узнали.

**Технический архитектурный проект**

Мы внедрили отдельную архитектуру игрового движка + серверную службу, разделив интерфейсный рендеринг, внутреннюю логику и искусственный интеллект на разные уровни. Godot отвечает за игровую графику и взаимодействие с игроками, FastAPI — за сервисы API и управление состоянием, а HelloAgents — за системы интеллекта и памяти NPC. Такая многоуровневая конструкция позволяет разрабатывать и тестировать каждую часть независимо, а также обеспечивает хорошую основу для будущего расширения.

**NPC Agent System**

Мы использовали SimpleAgent от HelloAgents, чтобы создать независимых агентов для каждого NPC. У каждого NPC есть своя ролевая установка, черты личности и система памяти. Благодаря тщательно разработанным системным подсказкам мы сделали Чжан Саня строгим инженером Python, Ли Си хорошим коммуникативным менеджером по продукту, а Ван Ву креативным дизайнером пользовательского интерфейса. Эти NPC могут не только понимать диалоги игроков, но и реагировать в соответствии со своими ролевыми характеристиками.

**Система памяти и привязанности**

Мы реализовали двухслойную систему памяти: кратковременная память поддерживает связность диалогов, а долговременная память хранит всю историю взаимодействия. Благодаря семантическому поиску в векторных базах данных NPC могут вспомнить ранее обсуждавшиеся темы. Система привязанности позволяет неигровым персонажам меняться в зависимости от взаимодействия с игроками: от незнакомца до близкого друга, с разными проявлениями поведения на каждом уровне. Такой дизайн делает неигровых персонажей более реалистичными и интересными.

**Построение игровой сцены**

Мы использовали Godot для создания офисной сцены в пиксельном стиле, реализовав управление игроком, блуждание NPC, обнаружение взаимодействия и диалоговый интерфейс. Благодаря модульной конструкции системы сцен мы можем легко добавлять новых NPC, новые сцены и новые функции. Краткий синтаксис GDScript делает реализацию игровой логики интуитивно понятной и эффективной.

**Внешняя и внутренняя связь**

Мы использовали HTTP REST API для реализации связи между интерфейсом Godot и сервером FastAPI. С помощью асинхронных запросов и систем сигналов мы обеспечили плавность игры — даже при высокой задержке в сети на впечатления игроков это не влияет. Инкапсуляция клиента API позволяет другим сценариям удобно вызывать серверные службы, а реализация диалогового пользовательского интерфейса позволяет игрокам естественным образом общаться с NPC.

Технологический стек проекта показан на рисунке 15.15:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/15-figures/15-15.png" alt="" width="85%"/>
  <p>Рисунок 15.15. Технологический стек Кибергорода</p>
</div>

### 15.7.2 Указания по расширению

Кибер-город — это только отправная точка, существует множество направлений для развития. Эти расширения могут не только повысить удовольствие от игры, но и раскрыть больше возможностей использования технологий искусственного интеллекта в играх.

**(1) Поддержка многопользовательской онлайн-игры**

В настоящее время Cyber ​​Town — это однопользовательская игра, но мы можем расширить ее до многопользовательской онлайн-игры. Несколько игроков могут одновременно войти в один и тот же офис и взаимодействовать с NPC и другими игроками. Это требует внедрения WebSocket для связи в реальном времени и баз данных для сохранения данных игроков и состояний NPC. NPC могут запоминать взаимодействие с разными игроками и поддерживать независимый уровень привязанности к каждому игроку.

**(2) Система квестов**

Мы можем разработать систему квестов для NPC. Когда привязанность игрока к NPC достигает определенного уровня, NPC предоставляет специальные квесты. Например, Чжан Сан может попросить игрока помочь в отладке кода, Ли Си может попросить игрока собрать отзывы пользователей, а Ван Ву может попросить игрока оценить предложения по дизайну. Выполнение квестов может принести награды и еще больше усилить привязанность.

**(3) Взаимодействие между NPC**

В настоящее время NPC взаимодействуют только с игроками, но мы можем позволить NPC взаимодействовать друг с другом. Чжан Сан может обсудить требования к продукту с Ли Си, Ли Си может обсудить дизайн интерфейса с Ван Ву, а Ван Ву может обсудить техническую реализацию с Чжан Санем. Эти взаимодействия могут происходить автоматически в фоновом режиме, и игроки могут наблюдать за диалогами между NPC, что делает весь мир более оживленным.

**(4) Система эмоций**

Помимо привязанности, мы можем добавить более сложную систему эмоций для NPC. NPC могут находиться в разных эмоциональных состояниях, например, счастливых, грустных, злых и взволнованных, что влияет на стиль ответов и поведение NPC. Например, когда NPC в хорошем настроении, они охотнее делятся информацией; в плохом настроении они могут быть довольно холодными.

**(5) Динамическая система событий**

Мы можем создавать динамические события, чтобы сделать игровой мир богаче. Например, регулярно проводите командные собрания, на которых собираются все NPC и игроки, чтобы обсудить ход проекта; или устраивать вечеринки по случаю дня рождения NPC; или чрезвычайные задачи, требующие сотрудничества каждого. Эти мероприятия могут сделать игру более разнообразной и увлекательной.

**(6) Большой мир**

В настоящее время в Кибер-городе есть только одна офисная сцена, но мы можем расшириться до более крупного мира. Мы можем добавлять разные сцены, такие как кафе, библиотеки и парки, каждая со своими NPC и методами взаимодействия. Игроки могут перемещаться между разными сценами и исследовать более широкий виртуальный мир.

**(7) Персонализированное обучение**

NPC могут узнать предпочтения и привычки каждого игрока. Например, если игрок часто обсуждает Python с Чжан Санем, NPC запомнит, что игрок интересуется программированием, и будет активно делиться соответствующим контентом в будущем. Если игроку нравится играть в игры по ночам, NPC запомнит эту привычку и будет более активен ночью.

### 15.7.3 Размышления и перспективы

Кибер-город демонстрирует огромный потенциал технологий искусственного интеллекта в играх. NPC в традиционных играх ограничены предустановленными деревьями диалогов и сценариями, в то время как NPC с искусственным интеллектом могут понимать и генерировать естественный язык, ведя реальные разговоры с игроками. Это не только усиливает погружение в игру, но и открывает новые возможности для игрового дизайна.

Однако ИИ-НПЦ также сталкиваются с некоторыми проблемами. Во-первых, это проблема стоимости: каждый разговор требует вызова LLM API, за который взимается определенная плата. Для больших многопользовательских онлайн-игр эта стоимость может быть очень высокой. Во-вторых, это проблема с задержкой: вывод LLM требует времени, и если задержка в сети высока, игрокам может потребоваться подождать несколько секунд, чтобы увидеть ответы NPC. Наконец, существует проблема контроля контента: контент, созданный LLM, может быть не полностью управляемым, поэтому требуются хорошо продуманные подсказки и механизмы фильтрации контента.

Несмотря на эти проблемы, будущее AI-NPC остается многообещающим. По мере развития технологии LLM скорость вывода будет увеличиваться, а затраты уменьшаться. Локализованные небольшие LLM также быстро развиваются — в будущем они, возможно, смогут запускаться непосредственно на устройствах игроков, вообще не требуя сетевых запросов. Сочетание технологий искусственного интеллекта и игр принесет игрокам беспрецедентные впечатления.

В главе дипломного проекта пятой части мы узнаем, как создавать агенты общего назначения, используя одиночные агенты и мультиагенты. Это будет ваше творческое время, так что следите за обновлениями!
