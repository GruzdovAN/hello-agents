# Глава 9. Инженерия контекста

В предыдущих главах мы представили системы памяти и RAG для агентов. Однако, чтобы агенты могли стабильно «думать» и «действовать» в реальных сложных сценариях, одних только памяти и извлечения недостаточно — нам нужна инженерная методология, позволяющая непрерывно и систематически создавать соответствующий «контекст» для модели. Это тема этой главы: Контекстная инженерия. Основное внимание уделяется тому, «как собирать и оптимизировать входной контекст многоразовым, измеримым и развиваемым способом перед каждым вызовом модели», тем самым повышая правильность, надежность и эффективность<sup>[1][2]</sup>.

Чтобы читатели могли быстро освоить всю функциональность этой главы, мы предоставляем устанавливаемый непосредственно пакет Python. Вы можете установить версию, соответствующую этой главе, с помощью следующей команды:

```bash
pip install "hello-agents[all]==0.2.8"
```

В этой главе в основном представлены основные концепции и методы разработки контекста, а также добавлен построитель контекста и два вспомогательных инструмента в среду HelloAgents:

- **ContextBuilder** (`hello_agents/context/builder.py`): построитель контекста, реализующий конвейер GSSC (Gather-Select-Structure-Compress), предоставляющий унифицированный интерфейс управления контекстом.
- **NoteTool** (`hello_agents/tools/builtin/note_tool.py`): инструмент структурированных заметок, поддерживающий управление постоянной памятью для агентов.
- **TerminalTool** (`hello_agents/tools/builtin/terminal_tool.py`): инструмент терминала, который поддерживает операции с файловой системой и своевременное получение контекста для агентов.

Вместе эти компоненты составляют комплексное решение для контекстной инженерии, которое является ключом к реализации долгосрочного управления задачами и агентного поиска и будет подробно представлено в последующих разделах.

Помимо установки фреймворка, вам также необходимо настроить LLM API в`.env`. В примерах в этой главе в основном используются большие языковые модели для управления контекстом и интеллектуального принятия решений.

После завершения настройки вы можете начать изучение этой главы!

## 9.1 Что такое контекстная инженерия

После многих лет, когда оперативное проектирование стало в центре внимания прикладного ИИ, на первый план вышел новый термин: **Контекстная инженерия**. Сегодня построение систем с использованием языковых моделей — это уже не просто поиск правильных формулировок в подсказках, а ответ на более макроэкономический вопрос: **Какая конфигурация контекста с наибольшей вероятностью заставит модель вести себя так, как мы ожидаем?**

Так называемый «контекст» относится к набору токенов, включенных при выборке большой языковой модели (LLM). Техническая проблема заключается в том, чтобы «оптимизировать полезность этих токенов** в соответствии с ограничениями, присущими LLM, чтобы стабильно получать ожидаемые результаты». Чтобы эффективно использовать LLM, часто необходимо «думать в контексте», то есть: при каждом вызове проверять общее состояние, видимое LLM, и прогнозировать поведение, которое это состояние может вызвать.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/9-figures/9-1.webp" alt="" width="85%"/>
  <p>Рисунок 9.1. Быстрое проектирование и контекстное проектирование</p>
</div>

В этом разделе будут рассмотрены новые возможности контекстной инженерии и представлена ​​усовершенствованная ментальная модель для создания **управляемых и эффективных** агентов.

**Контекстное проектирование против оперативного проектирования**

Как показано на рисунке 9.1, с точки зрения ведущих поставщиков моделей, контекстная инженерия является естественным развитием оперативного проектирования. Оперативное проектирование фокусируется на том, как писать и организовывать инструкции LLM для получения лучших результатов (например, написание системных подсказок и структурированные стратегии); в то время как контекстная инженерия — это **как планировать и поддерживать «оптимальный набор информации (токены)» на этапе вывода**, который включает в себя не только само приглашение, но и всю другую информацию, которая попадет в окно контекста.

На ранних этапах разработки LLM подсказки часто были основной работой, поскольку большинство случаев использования (кроме ежедневного чата) требовали тонкой оптимизации подсказок для одноходовой классификации или генерации текста. Как следует из названия, суть разработки подсказок заключается в том, «как писать эффективные подсказки», особенно системные подсказки. Однако по мере того, как мы начинаем создавать более сильные агенты, которые работают в течение более длительных периодов времени и в нескольких раундах вывода, нам нужны стратегии, которые могут управлять **всем состоянием контекста**, включая системные инструкции, инструменты, MCP (протокол контекста модели), внешние данные, историю сообщений и т. д.

Агент, работающий в цикле, будет постоянно генерировать данные, которые могут иметь отношение к следующему раунду вывода. Эта информация должна **периодически уточняться**. Таким образом, «искусство и техника» контекстной инженерии заключается в «определении того, какой контент должен войти в ограниченное контекстное окно» из постоянно расширяющейся «вселенной информации-кандидата».

## 9.2 Почему важна контекстная инженерия

Хотя модели становятся быстрее и могут обрабатывать большие объемы данных, мы наблюдаем, что: как и люди, LLM в определенный момент «блуждают» или «запутываются». Тесты «иголки в стоге сена» выявили феномен: **гниение контекста** — по мере увеличения количества токенов в контекстном окне способность модели точно извлекать информацию из контекста фактически снижается.

Разные модели могут иметь более плавные кривые деградации, но эта характеристика проявляется практически во всех моделях. Следовательно, **контекст следует рассматривать как ограниченный ресурс с уменьшающейся предельной отдачей**. Точно так же, как люди имеют ограниченный объем рабочей памяти, у LLM также есть «бюджет внимания». Каждый новый токен потребляет часть этого бюджета, поэтому нам нужно более внимательно относиться к тому, какие токены следует предоставлять LLM.

Этот дефицит не случаен, а обусловлен архитектурными ограничениями программ LLM. Трансформеры позволяют каждому токену устанавливать ассоциации со **всеми** токенами в контексте, теоретически образуя \(n^2\) парные отношения внимания. По мере увеличения длины контекста способность модели моделировать эти парные отношения «растягивается», что естественным образом создает напряжение между «масштабом контекста» и «концентрацией внимания». Кроме того, шаблоны внимания модели обусловлены распределением обучающих данных — короткие последовательности обычно встречаются чаще, чем длинные, поэтому у модели меньше опыта работы с «полноконтекстными зависимостями» и меньше специализированных параметров.

Такие методы, как интерполяция кодирования положения, могут позволить моделям «адаптироваться» к последовательностям, более длительным, чем во время обучения во время вывода, но за счет некоторой точности в понимании положений токенов. В целом, эти факторы вместе образуют **градиент производительности**, а не «обрывной» коллапс: модели по-прежнему эффективны в длительных контекстах, но по сравнению с короткими контекстами их точность в поиске информации и долгосрочном рассуждении снизится.

Учитывая вышеизложенное, **сознательная контекстная инженерия** становится необходимостью для создания надежных агентов.

### 9.2.1 «Анатомия» эффективного контекста

В условиях «ограниченного бюджета внимания» цель отличной контекстной инженерии состоит в следующем: **максимизировать вероятность получения ожидаемых результатов с как можно меньшим количеством токенов, но с высокой плотностью сигнала**. На практике мы рекомендуем проектировать с учетом следующих компонентов:

- **Системная подсказка**: ясный и понятный язык с иерархией информации на «правильной» высоте. Распространенные ошибки в двух крайностях:
  - Чрезмерное кодирование: написание сложной, хрупкой логики if-else в подсказках с высокими долгосрочными затратами на обслуживание и хрупкостью.
  - Слишком расплывчато: предоставляются только макроцели и общие рекомендации, отсутствуют **конкретные сигналы** для ожидаемых результатов или предполагается неправильный «общий контекст».
  Рекомендуется организовывать подсказки в разделы (например, <background_information>, <instructions>, руководство по инструменту, описание вывода и т. д.), разделенные XML/Markdown. Независимо от формата, поиск представляет собой **"минимально необходимый набор информации", который может полностью описать ожидаемое поведение** ("минимум" не равен "самый короткий"). Сначала запустите лучшую модель с минимальным запросом, затем добавьте четкие инструкции и примеры, основанные на режимах сбоя.

- **Инструменты**: инструменты определяют контракт между агентом и информационным пространством/пространством действий и должны способствовать эффективности: они должны возвращать **удобную для токенов** информацию, одновременно поощряя эффективное поведение агента. Инструменты должны:
  - Иметь единые обязанности с низким дублированием, четкой семантикой интерфейса;
  - быть устойчивым к ошибкам;
  - Иметь четкие и недвусмысленные описания параметров, полностью используя сильные стороны модели в выражениях и рассуждениях.
  Распространенным типом сбоя является «раздутый набор инструментов»: нечеткие функциональные границы, что делает решение «какой инструмент использовать» само по себе неоднозначным. **Если инженеры-люди не могут определить, какой инструмент использовать, не ждите, что агенты справятся с задачей лучше**. Тщательное определение «Минимально жизнеспособного набора инструментов (MVTS)» часто может значительно улучшить стабильность и удобство обслуживания при долгосрочном взаимодействии.

- **Несколько примеров**. Всегда рекомендуется приводить примеры, но не рекомендуется вставлять в подсказки «все граничные условия». Пожалуйста, внимательно выберите набор **разнообразных и типичных** примеров, которые непосредственно описывают «ожидаемое поведение». Для студентов магистратуры **хорошие примеры стоят тысячи слов**.

Общий руководящий принцип: **достаточная, но компактная информация**. Как показано на рисунке 9.2, это динамическое извлечение, входящее во время выполнения.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/9-figures/9-2.webp" alt="" width="85%"/>
  <p>Рисунок 9.2 Калибровка системного приглашения</p>
</div>

### 9.2.2 Получение контекста и агентный поиск

Краткое определение: **Агент = LLM, автономно вызывающий инструменты в цикле**. По мере увеличения возможностей базовых моделей уровень автономии агентов может быть повышен: они смогут более независимо исследовать сложные проблемные области и восстанавливаться после ошибок.

Инженерная практика постепенно переходит от «одноразового извлечения перед выводом (встраивание извлечения)» к «**контексту JIT»**. Последний больше не предварительно загружает все необходимые данные, но поддерживает **облегченные ссылки** (пути к файлам, запросы к хранилищу, URL-адреса и т. д.), динамически загружая необходимые данные с помощью инструментов во время выполнения. Это позволяет модели писать целевые запросы, кэшировать необходимые результаты и анализировать большие объемы данных с помощью таких команд, как <code>head</code>/<code>tail</code>, не помещая в контекст сразу целые блоки данных. Его когнитивная модель ближе к человеку: мы не запоминаем всю информацию, а используем внешние индексы, такие как файловые системы, почтовые ящики, закладки, для извлечения по требованию.

Помимо эффективности хранения, **метаданные ссылок** сами по себе могут помочь улучшить поведение: иерархия каталогов, соглашения об именах, временные метки и т. д. — все это неявно передает «цель и своевременность». Например, <code>tests/test_utils.py</code> и <code>src/core/test_utils.py</code> имеют разное семантическое значение.

Разрешение агентам самостоятельно перемещаться и извлекать информацию также обеспечивает **прогрессивное раскрытие**: каждый шаг взаимодействия генерирует новый контекст, который, в свою очередь, определяет следующее решение: размер файла указывает на сложность, наименование указывает на цель, временные метки указывают на релевантность. Агенты могут строить понимание слой за слоем, сохраняя в рабочей памяти только «необходимое на данный момент подмножество» и используя «ведение заметок» для дополнительной устойчивости, тем самым сохраняя концентрацию, а не «увлекаясь полнотой».

Компромисс таков: исследование во время выполнения часто происходит медленнее, чем предварительно вычисленное извлечение, и требует «самоуверенного» инженерного проектирования, чтобы гарантировать, что модель имеет правильные инструменты и эвристики. Без руководства агенты могут неправильно использовать инструменты, заходить в тупик или пропускать ключевую информацию, что приводит к потере контекста.

Во многих сценариях **гибридная стратегия** более эффективна: предварительно загружайте небольшое количество «важного» контекста для обеспечения скорости, а затем позволяйте агентам продолжать автономное исследование по требованию. Выбор границ зависит от динамики задачи и требований к своевременности. В разработке вы можете предварительно загружать файлы, такие как «описания соглашений проекта (например, README/руководства)», предоставляя при этом примитивы, такие как <code>glob</code>, <code>grep</code>, что позволяет агентам получать определенные файлы точно в срок, тем самым обходя невозвратные затраты на устаревшие индексы и сложные синтаксические деревья.

### 9.2.3 Контекстная инженерия для долгосрочных задач

Задачи с длительным горизонтом требуют от агентов поддержания согласованности, согласованности контекста и ориентации на цели в последовательностях действий, выходящих за рамки контекстного окна. Например, большие миграции кодовой базы, систематические исследования, занимающие несколько часов. Ожидание бесконечного увеличения контекстного окна не может решить проблемы «загрязнения контекста» и деградации релевантности, поэтому необходимы инженерные методы, непосредственно устраняющие эти ограничения: **Сжатие**, **Структурированное ведение заметок** и **Субагентные архитектуры**.

- **Уплотнение**
  - Определение: когда разговор приближается к пределу контекста, выполните высокоточное суммирование и перезапустите новое окно контекста со сводкой, чтобы сохранить согласованность на большом расстоянии.
  - Практика: сжимайте модель и сохраняйте архитектурные решения, неустраненные дефекты, детали реализации, отбрасывая повторяющиеся выходные данные инструмента и шум; новое окно содержит сжатую сводку + несколько недавних весьма важных артефактов (например, «недавно использованные файлы»).
  - Рекомендации по настройке: сначала оптимизируйте **запоминание** (убедитесь, что не пропущена ключевая информация), затем оптимизируйте **точность** (удаление избыточного контента); безопасное сжатие «легким касанием» предназначено для очистки «вызовов инструментов и результатов в глубокой истории».

- **Структурированное ведение заметок**
  - Определение: Также называется «памятью агента». Агенты записывают ключевую информацию в **постоянное хранилище вне контекста** с фиксированной частотой, извлекая ее обратно по требованию на последующих этапах.
  - Ценность: поддержание постоянного состояния и зависимостей с чрезвычайно низкими затратами на контекст. Например, ведение списков TODO, проекта NOTES.md, индексов ключевых выводов/зависимостей/блокировщиков, поддержание прогресса и согласованности между десятками вызовов инструментов и множественными сбросами контекста.
  - Примечание. Одинаково эффективно в сценариях, не связанных с кодированием (таких как долгосрочные стратегические задачи, управление целями и статистический подсчет в играх/симуляциях). В сочетании с <code>MemoryTool</code> из главы 8 можно легко реализовать внешнюю память на основе файлов или векторов и извлекать ее во время выполнения.

- **Архитектура субагента**
  - Идея: главный агент отвечает за высокоуровневое планирование и синтез, в то время как каждый из нескольких специализированных субагентов копает глубже, вызывает инструменты и исследует «окна чистого контекста», в конечном итоге возвращая только **сокращенные сводки** (обычно 1000–2000 токенов).
  - Преимущества: Достичь разделения задач. Сложные контексты поиска остаются внутренними для субагентов, в то время как основной агент фокусируется на интеграции и рассуждениях; подходит для сложных задач исследования/анализа, требующих параллельного исследования.
  - Опыт: общедоступные многоагентные исследовательские системы показывают, что этот шаблон имеет значительные преимущества по сравнению с базовыми моделями с одним агентом в сложных исследовательских задачах.

Компромиссы методов могут следовать следующим практическим правилам:

- **Сжатие**: подходит для задач, требующих длительной непрерывности разговора, с акцентом на «ретрансляцию контекста».
- **Структурированное ведение заметок**: подходит для итеративной разработки и исследований с указанием этапов/поэтапных результатов.
- **Архитектура субагентов**: подходит для комплексных исследований и анализа, для которых может быть полезно параллельное исследование.

Несмотря на то, что возможности моделей продолжают улучшаться, «поддержание согласованности и сосредоточенности в длительных взаимодействиях» остается основной проблемой в создании надежных агентов. Тщательная и систематическая контекстная инженерия сохранит свою ключевую ценность в долгосрочной перспективе.

## 9.3 Практика в Hello-Agents: ContextBuilder

В этом разделе подробно описывается практика контекстной инженерии в среде HelloAgents. Мы постепенно продемонстрируем, как построить систему управления контекстом промышленного уровня, начиная с мотивации проектирования, основных структур данных, деталей реализации и заканчивая завершением кейсов. Философия проектирования ContextBuilder «проста и эффективна», устраняет ненужную сложность, обеспечивает единый выбор на основе оценок «релевантность + новизна», что соответствует инженерной ориентации модульности и удобства обслуживания агента.

### 9.3.1 Мотивация и цели дизайна

Прежде чем создавать ContextBuilder, нам сначала необходимо уточнить цели его разработки и основную ценность. Отличная система управления контекстом должна решать следующие ключевые проблемы:

1. **Унифицированный ввод**: абстракция «Сбор-Выбор-Структура-Сжатие» в виде многоразового конвейера, позволяющая сократить повторяющийся код шаблона в реализациях агента. Этот унифицированный дизайн интерфейса позволяет разработчикам избежать повторного написания логики управления контекстом в каждом агенте.

2. **Стабильная форма**. Вывод шаблона контекста с фиксированным скелетом, облегчающий отладку, A/B-тестирование и оценку. Мы приняли секционированную структуру шаблона:
   - `[Роль и политика]`: уточните позиционирование роли агента и рекомендации по поведению.
   - `[Task]`: конкретная задача, которую необходимо выполнить в данный момент.
   - `[State]`: текущее состояние агента и контекстная информация.
   - `[Доказательства]`: доказательная информация, полученная из внешних баз знаний.
   - `[Контекст]`: Исторический диалог и связанные с ним воспоминания
   - `[Вывод]`: ожидаемый формат вывода и требования.

3. **Budget Guardian**: максимально сохраняйте ценную информацию в рамках бюджета токена, обеспечивая резервные стратегии сжатия для контекстов превышения лимита. Это гарантирует, что даже в сценариях с огромными объемами информации система сможет работать стабильно.

4. **Минимальные правила**: не вводите такие параметры классификации, как источник/приоритет, чтобы избежать роста сложности. Практика показывает, что простой механизм оценки, основанный на релевантности и новизне, достаточно эффективен в большинстве сценариев.

### 9.3.2 Базовые структуры данных

Реализация ContextBuilder опирается на две основные структуры данных, которые определяют конфигурацию системы и информационные блоки.

(1) ContextPacket: пакет информации о кандидате

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class ContextPacket:
    """Candidate information package

    Attributes:
        content: Information content
        timestamp: Timestamp
        token_count: Token count
        relevance_score: Relevance score (0.0-1.0)
        metadata: Optional metadata
    """
    content: str
    timestamp: datetime
    token_count: int
    relevance_score: float = 0.5
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.metadata is None:
            self.metadata = {}
        # Ensure relevance score is within valid range
        self.relevance_score = max(0.0, min(1.0, self.relevance_score))
```

`ContextPacket`является основной единицей информации в системе. Информация о каждом кандидате инкапсулируется как ContextPacket, содержащий основные атрибуты, такие как контент, временная метка, количество токенов и оценка релевантности. Эта унифицированная структура данных упрощает последующую логику выбора и сортировки.

(2) ContextConfig: Управление конфигурацией

```python
@dataclass
class ContextConfig:
    """Context building configuration

    Attributes:
        max_tokens: Maximum token count
        reserve_ratio: Ratio reserved for system instructions (0.0-1.0)
        min_relevance: Minimum relevance threshold
        enable_compression: Whether to enable compression
        recency_weight: Recency weight (0.0-1.0)
        relevance_weight: Relevance weight (0.0-1.0)
    """
    max_tokens: int = 3000
    reserve_ratio: float = 0.2
    min_relevance: float = 0.1
    enable_compression: bool = True
    recency_weight: float = 0.3
    relevance_weight: float = 0.7

    def __post_init__(self):
        """Validate configuration parameters"""
        assert 0.0 <= self.reserve_ratio <= 1.0, "reserve_ratio must be in [0, 1] range"
        assert 0.0 <= self.min_relevance <= 1.0, "min_relevance must be in [0, 1] range"
        assert abs(self.recency_weight + self.relevance_weight - 1.0) < 1e-6, \
            "recency_weight + relevance_weight must equal 1.0"
```

`ContextConfig`инкапсулирует все настраиваемые параметры, делая поведение системы гибко настраиваемым. Особого внимания заслуживает`reserve_ratio`параметр, который гарантирует, что ключевая информация, такая как системные инструкции, всегда будет иметь достаточно места и не будет вытеснена другой информацией.

### 9.3.3 Подробное объяснение конвейера GSSC

Ядром ContextBuilder является конвейер GSSC (Gather-Select-Structure-Compress), который разбивает процесс построения контекста на четыре четких этапа. Давайте углубимся в детали реализации каждого этапа.

(1) Сбор: сбор информации из нескольких источников.

Первый этап – сбор информации о кандидате из нескольких источников. Ключом к этому этапу является отказоустойчивость и гибкость.

```python
def _gather(
    self,
    user_query: str,
    conversation_history: Optional[List[Message]] = None,
    system_instructions: Optional[str] = None,
    custom_packets: Optional[List[ContextPacket]] = None
) -> List[ContextPacket]:
    """Collect all candidate information

    Args:
        user_query: User query
        conversation_history: Conversation history
        system_instructions: System instructions
        custom_packets: Custom information packages

    Returns:
        List[ContextPacket]: Candidate information list
    """
    packets = []

    # 1. Add system instructions (highest priority, not scored)
    if system_instructions:
        packets.append(ContextPacket(
            content=system_instructions,
            timestamp=datetime.now(),
            token_count=self._count_tokens(system_instructions),
            relevance_score=1.0,  # System instructions always retained
            metadata={"type": "system_instruction", "priority": "high"}
        ))

    # 2. Retrieve relevant memories from memory system
    if self.memory_tool:
        try:
            memory_results = self.memory_tool.run({
                "action": "search",
                "query": user_query,
                "limit": 10,
                "min_importance": 0.3
            })
            # Parse memory results and convert to ContextPacket
            memory_packets = self._parse_memory_results(memory_results, user_query)
            packets.extend(memory_packets)
        except Exception as e:
            print(f"[WARNING] Memory retrieval failed: {e}")

    # 3. Retrieve relevant knowledge from RAG system
    if self.rag_tool:
        try:
            rag_results = self.rag_tool.run({
                "action": "search",
                "query": user_query,
                "limit": 5,
                "min_score": 0.3
            })
            # Parse RAG results and convert to ContextPacket
            rag_packets = self._parse_rag_results(rag_results, user_query)
            packets.extend(rag_packets)
        except Exception as e:
            print(f"[WARNING] RAG retrieval failed: {e}")

    # 4. Add conversation history (only keep recent N entries)
    if conversation_history:
        recent_history = conversation_history[-5:]  # Default keep recent 5 entries
        for msg in recent_history:
            packets.append(ContextPacket(
                content=f"{msg.role}: {msg.content}",
                timestamp=msg.timestamp if hasattr(msg, 'timestamp') else datetime.now(),
                token_count=self._count_tokens(msg.content),
                relevance_score=0.6,  # Base relevance of historical messages
                metadata={"type": "conversation_history", "role": msg.role}
            ))

    # 5. Add custom information packages
    if custom_packets:
        packets.extend(custom_packets)

    print(f"[ContextBuilder] Collected {len(packets)} candidate information packages")
    return packets
```

Эта реализация демонстрирует несколько важных конструктивных соображений:

- **Механизм отказоустойчивости**: каждый вызов внешнего источника данных обертывается в try-Exception, гарантируя, что сбой одного источника не повлияет на весь процесс.
- **Приоритетная обработка**: системные инструкции помечаются как высокоприоритетные, что гарантирует их постоянное сохранение.
- **Ограничение истории**: в истории разговоров сохраняются только самые последние записи, поэтому контекстное окно не занято исторической информацией.

(2) Выберите: интеллектуальный выбор информации.

Второй этап заключается в оценке и выборе информации о кандидате на основе релевантности и актуальности. Это ядро ​​всего пайплайна и напрямую определяет качество конечного контекста.

```python
def _select(
    self,
    packets: List[ContextPacket],
    user_query: str,
    available_tokens: int
) -> List[ContextPacket]:
    """Select the most relevant information packages

    Args:
        packets: Candidate information package list
        user_query: User query (for calculating relevance)
        available_tokens: Available token count

    Returns:
        List[ContextPacket]: Selected information package list
    """
    # 1. Separate system instructions and other information
    system_packets = [p for p in packets if p.metadata.get("type") == "system_instruction"]
    other_packets = [p for p in packets if p.metadata.get("type") != "system_instruction"]

    # 2. Calculate tokens occupied by system instructions
    system_tokens = sum(p.token_count for p in system_packets)
    remaining_tokens = available_tokens - system_tokens

    if remaining_tokens <= 0:
        print("[WARNING] System instructions have occupied all token budget")
        return system_packets

    # 3. Calculate comprehensive scores for other information
    scored_packets = []
    for packet in other_packets:
        # Calculate relevance score (if not yet calculated)
        if packet.relevance_score == 0.5:  # Default value, needs recalculation
            relevance = self._calculate_relevance(packet.content, user_query)
            packet.relevance_score = relevance

        # Calculate recency score
        recency = self._calculate_recency(packet.timestamp)

        # Combined score = relevance weight × relevance + recency weight × recency
        combined_score = (
            self.config.relevance_weight * packet.relevance_score +
            self.config.recency_weight * recency
        )

        # Filter information below minimum relevance threshold
        if packet.relevance_score >= self.config.min_relevance:
            scored_packets.append((combined_score, packet))

    # 4. Sort by score in descending order
    scored_packets.sort(key=lambda x: x[0], reverse=True)

    # 5. Greedy selection: fill from high to low score until token limit is reached
    selected = system_packets.copy()
    current_tokens = system_tokens

    for score, packet in scored_packets:
        if current_tokens + packet.token_count <= available_tokens:
            selected.append(packet)
            current_tokens += packet.token_count
        else:
            # Token budget is full, stop selection
            break

    print(f"[ContextBuilder] Selected {len(selected)} information packages, total {current_tokens} tokens")
    return selected

def _calculate_relevance(self, content: str, query: str) -> float:
    """Calculate relevance between content and query

    Uses simple keyword overlap algorithm. In production, can be replaced with vector similarity calculation.

    Args:
        content: Content text
        query: Query text

    Returns:
        float: Relevance score (0.0-1.0)
    """
    # Tokenization (simple implementation, can use more complex tokenizers)
    content_words = set(content.lower().split())
    query_words = set(query.lower().split())

    if not query_words:
        return 0.0

    # Jaccard similarity
    intersection = content_words & query_words
    union = content_words | query_words

    return len(intersection) / len(union) if union else 0.0

def _calculate_recency(self, timestamp: datetime) -> float:
    """Calculate temporal recency score

    Uses exponential decay model, maintains high score within 24 hours, then gradually decays.

    Args:
        timestamp: Information timestamp

    Returns:
        float: Recency score (0.0-1.0)
    """
    import math

    age_hours = (datetime.now() - timestamp).total_seconds() / 3600

    # Exponential decay: maintain high score within 24 hours, then gradually decay
    decay_factor = 0.1  # Decay coefficient
    recency_score = math.exp(-decay_factor * age_hours / 24)

    return max(0.1, min(1.0, recency_score))  # Limit to [0.1, 1.0] range
```

Основной алгоритм этапа выбора учитывает несколько важных инженерных соображений:

- **Механизм оценки**: использует взвешенную комбинацию релевантности и новизны с настраиваемыми весами.
- **Жадный алгоритм**: заполняет баллы от высокого к низкому, обеспечивая отбор наиболее ценной информации в рамках ограниченного бюджета.
- **Механизм фильтрации**: фильтрует некачественную информацию с помощью параметра min_relevance.

(3) Структура: структурированный вывод

Третий этап — организовать выбранную информацию в структурированный шаблон контекста.

```python
def _structure(self, selected_packets: List[ContextPacket], user_query: str) -> str:
    """Organize selected information packages into structured context template

    Args:
        selected_packets: Selected information package list
        user_query: User query

    Returns:
        str: Structured context string
    """
    # Group by type
    system_instructions = []
    evidence = []
    context = []

    for packet in selected_packets:
        packet_type = packet.metadata.get("type", "general")

        if packet_type == "system_instruction":
            system_instructions.append(packet.content)
        elif packet_type in ["rag_result", "knowledge"]:
            evidence.append(packet.content)
        else:
            context.append(packet.content)

    # Build structured template
    sections = []

    # [Role & Policies]
    if system_instructions:
        sections.append("[Role & Policies]\n" + "\n".join(system_instructions))

    # [Task]
    sections.append(f"[Task]\n{user_query}")

    # [Evidence]
    if evidence:
        sections.append("[Evidence]\n" + "\n---\n".join(evidence))

    # [Context]
    if context:
        sections.append("[Context]\n" + "\n".join(context))

    # [Output]
    sections.append("[Output]\nPlease provide accurate, evidence-based answers based on the above information.")

    return "\n\n".join(sections)
```

На этапе структурирования разрозненные информационные пакеты объединяются в четкие разделы. Такая конструкция имеет ряд преимуществ:

- **Удобочитаемость**: четкие разделы облегчают понимание структуры контекста как людьми, так и моделями.
- **Возможность отладки**: проще локализовать проблему, можно быстро определить, в какой области содержится проблемная информация.
- **Расширяемость**: для добавления новых источников информации требуется только создание новых разделов.

(4) Сжатие: резервное сжатие

Четвертый этап — сжатие контекстов, превышающих лимит.

```python
def _compress(self, context: str, max_tokens: int) -> str:
    """Compress over-limit context

    Args:
        context: Original context
        max_tokens: Maximum token limit

    Returns:
        str: Compressed context
    """
    current_tokens = self._count_tokens(context)

    if current_tokens <= max_tokens:
        return context  # No compression needed

    print(f"[ContextBuilder] Context over limit ({current_tokens} > {max_tokens}), executing compression")

    # Section compression: maintain structural integrity
    sections = context.split("\n\n")
    compressed_sections = []
    current_total = 0

    for section in sections:
        section_tokens = self._count_tokens(section)

        if current_total + section_tokens <= max_tokens:
            # Fully retain
            compressed_sections.append(section)
            current_total += section_tokens
        else:
            # Partially retain
            remaining_tokens = max_tokens - current_total
            if remaining_tokens > 50:  # Retain at least 50 tokens
                # Simple truncation (can use LLM summarization in production)
                truncated = self._truncate_text(section, remaining_tokens)
                compressed_sections.append(truncated + "\n[... Content compressed ...]")
            break

    compressed_context = "\n\n".join(compressed_sections)
    final_tokens = self._count_tokens(compressed_context)
    print(f"[ContextBuilder] Compression complete: {current_tokens} -> {final_tokens} tokens")

    return compressed_context

def _truncate_text(self, text: str, max_tokens: int) -> str:
    """Truncate text to specified token count

    Args:
        text: Original text
        max_tokens: Maximum token count

    Returns:
        str: Truncated text
    """
    # Simple implementation: estimate by character ratio
    # Should use precise tokenizer in production
    char_per_token = len(text) / self._count_tokens(text) if self._count_tokens(text) > 0 else 4
    max_chars = int(max_tokens * char_per_token)

    return text[:max_chars]

def _count_tokens(self, text: str) -> int:
    """Estimate token count of text

    Args:
        text: Text content

    Returns:
        int: Token count
    """
    # Simple estimation: Chinese 1 char ≈ 1 token, English 1 word ≈ 1.3 tokens
    # Should use actual tokenizer in production
    chinese_chars = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    english_words = len([w for w in text.split() if w])

    return int(chinese_chars + english_words * 1.3)
```

В конструкции ступени сжатия реализован принцип «сохранения структурной целостности». Даже когда бюджет токена ограничен, он пытается сохранить ключевую информацию из каждого раздела.

### 9.3.4 Полный пример использования

Теперь давайте на полном примере продемонстрируем, как использовать ContextBuilder в реальных проектах.

(1) Основное использование

```python
from hello_agents.context import ContextBuilder, ContextConfig
from hello_agents.tools import MemoryTool, RAGTool
from hello_agents.core.message import Message
from datetime import datetime

# 1. Initialize tools
memory_tool = MemoryTool(user_id="user123")
rag_tool = RAGTool(knowledge_base_path="./knowledge_base")

# 2. Create ContextBuilder
config = ContextConfig(
    max_tokens=3000,
    reserve_ratio=0.2,
    min_relevance=0.2,
    enable_compression=True
)

builder = ContextBuilder(
    memory_tool=memory_tool,
    rag_tool=rag_tool,
    config=config
)

# 3. Prepare conversation history
conversation_history = [
    Message(content="I'm developing a data analysis tool", role="user", timestamp=datetime.now()),
    Message(content="Great! Data analysis tools usually need to handle large amounts of data. What tech stack do you plan to use?", role="assistant", timestamp=datetime.now()),
    Message(content="I plan to use Python and Pandas, and have completed the CSV reading module", role="user", timestamp=datetime.now()),
    Message(content="Good choice! Pandas is very powerful for data processing. Next you may need to consider data cleaning and transformation.", role="assistant", timestamp=datetime.now()),
]

# 4. Add some memories
memory_tool.run({
    "action": "add",
    "content": "User is developing a data analysis tool using Python and Pandas",
    "memory_type": "semantic",
    "importance": 0.8
})

memory_tool.run({
    "action": "add",
    "content": "Completed development of CSV reading module",
    "memory_type": "episodic",
    "importance": 0.7
})

# 5. Build context
context = builder.build(
    user_query="How to optimize Pandas memory usage?",
    conversation_history=conversation_history,
    system_instructions="You are a senior Python data engineering consultant. Your answers need to: 1) Provide specific actionable advice 2) Explain technical principles 3) Provide code examples"
)

print("=" * 80)
print("Built context:")
print("=" * 80)
print(context)
print("=" * 80)
```

(2) Демонстрация эффекта работы

После запуска приведенного выше кода вы увидите следующий структурированный контекстный вывод:

```
================================================================================
Built context:
================================================================================
[Role & Policies]
You are a senior Python data engineering consultant. Your answers need to: 1) Provide specific actionable advice 2) Explain technical principles 3) Provide code examples

[Task]
How to optimize Pandas memory usage?

[Evidence]
Core strategies for Pandas memory optimization include:
1. Use appropriate data types (such as category instead of object)
2. Read large files in chunks
3. Use chunksize parameter
---
Data type optimization can significantly reduce memory usage. For example, downgrading int64 to int32 can save 50% memory.

[Context]
user: I'm developing a data analysis tool
assistant: Great! Data analysis tools usually need to handle large amounts of data. What tech stack do you plan to use?
user: I plan to use Python and Pandas, and have completed the CSV reading module
assistant: Good choice! Pandas is very powerful for data processing. Next you may need to consider data cleaning and transformation.
Memory: User is developing a data analysis tool using Python and Pandas
Memory: Completed development of CSV reading module

[Output]
Please provide accurate, evidence-based answers based on the above information.
================================================================================
```

Этот структурированный контекст содержит всю необходимую информацию:

- **[Роль и политика]**: поясняет роль ИИ и требования к ответам.
- **[Задание]**: четко выражает вопрос пользователя.
- **[Доказательства]**: Соответствующие знания, полученные из системы RAG
- **[Контекст]**: история разговоров и связанные с ними воспоминания, предоставляющие достаточную справочную информацию.
- **[Вывод]**: помогает LLM организовать ответ.

(3) Интеграция с агентом

Наконец, давайте продемонстрируем, как интегрировать ContextBuilder в агент:

```python
from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.context import ContextBuilder, ContextConfig
from hello_agents.tools import MemoryTool, RAGTool

class ContextAwareAgent(SimpleAgent):
    """Agent with context awareness capability"""

    def __init__(self, name: str, llm: HelloAgentsLLM, **kwargs):
        super().__init__(name=name, llm=llm, system_prompt=kwargs.get("system_prompt", ""))

        # Initialize context builder
        self.memory_tool = MemoryTool(user_id=kwargs.get("user_id", "default"))
        self.rag_tool = RAGTool(knowledge_base_path=kwargs.get("knowledge_base_path", "./kb"))

        self.context_builder = ContextBuilder(
            memory_tool=self.memory_tool,
            rag_tool=self.rag_tool,
            config=ContextConfig(max_tokens=4000)
        )

        self.conversation_history = []

    def run(self, user_input: str) -> str:
        """Run Agent, automatically build optimized context"""

        # 1. Use ContextBuilder to build optimized context
        optimized_context = self.context_builder.build(
            user_query=user_input,
            conversation_history=self.conversation_history,
            system_instructions=self.system_prompt
        )

        # 2. Call LLM with optimized context
        messages = [
            {"role": "system", "content": optimized_context},
            {"role": "user", "content": user_input}
        ]
        response = self.llm.invoke(messages)

        # 3. Update conversation history
        from hello_agents.core.message import Message
        from datetime import datetime

        self.conversation_history.append(
            Message(content=user_input, role="user", timestamp=datetime.now())
        )
        self.conversation_history.append(
            Message(content=response, role="assistant", timestamp=datetime.now())
        )

        # 4. Record important interactions to memory system
        self.memory_tool.run({
            "action": "add",
            "content": f"Q: {user_input}\nA: {response[:200]}...",  # Summary
            "memory_type": "episodic",
            "importance": 0.6
        })

        return response

# Usage example
agent = ContextAwareAgent(
    name="Data Analysis Consultant",
    llm=HelloAgentsLLM(),
    system_prompt="You are a senior Python data engineering consultant.",
    user_id="user123",
    knowledge_base_path="./data_science_kb"
)

response = agent.run("How to optimize Pandas memory usage?")
print(response)
```

Благодаря такому подходу ContextBuilder становится «мозгом управления контекстом» агента, автоматически осуществляющим сбор, фильтрацию и организацию информации, что позволяет агенту всегда рассуждать и генерировать данные в оптимальном контексте.

### 9.3.5 Лучшие практики и рекомендации по оптимизации

При фактическом применении ContextBuilder стоит отметить следующие рекомендации:

1. **Динамическая настройка бюджета токенов**: динамически настраивайте `max_tokens` в зависимости от сложности задачи, используйте меньшие бюджеты для простых задач, увеличивайте бюджеты для сложных задач.

2. **Оптимизация расчета релевантности**. В производственных средах замените простое перекрытие ключевых слов расчетом векторного сходства, чтобы улучшить качество поиска.

3. **Механизм кэширования**. Чтобы сохранить неизменяемые системные инструкции и содержимое базы знаний, внедрите механизмы кэширования, чтобы избежать повторных вычислений.

4. **Мониторинг и журналирование**: записывайте статистическую информацию для каждой сборки контекста (количество выбранной информации, скорость использования токена и т. д.) для последующей оптимизации.

5. **A/B-тестирование**. Для ключевых параметров (таких как вес релевантности и вес недавности) найдите оптимальную конфигурацию с помощью A/B-тестирования.

## 9.4 NoteTool: структурированные заметки

NoteTool — это структурированный компонент внешней памяти, предназначенный для «долгосрочных задач». В качестве носителей он использует файлы Markdown, с заголовком YAML для записи ключевой информации и телом для записи статуса, выводов, блокировщиков и элементов действий. Этот дизайн сочетает в себе удобочитаемость, удобство управления версиями и простоту повторного внедрения в контекст, что делает его важным инструментом для создания долгосрочных агентов.

### 9.4.1 Философия проектирования и сценарии применения

Прежде чем углубляться в детали реализации, давайте сначала разберемся с философией проектирования и типичными сценариями применения NoteTool.

(1) Зачем нам нужен NoteTool?

В главе 8 мы представили MemoryTool, который предоставляет мощные возможности управления памятью. Однако MemoryTool в основном фокусируется на **разговорной памяти** — кратковременной рабочей памяти, эпизодической памяти и семантической памяти. Для **проектных задач**, требующих долгосрочного отслеживания и структурированного управления, нам нужен более простой и удобный для человека метод записи.

NoteTool заполняет этот пробел, предоставляя:

- **Структурированная запись**: используется формат Markdown + YAML, подходящий как для машинного анализа, так и для чтения и редактирования человеком.
- **Поддержка версий**: обычный текстовый формат, естественно поддерживает системы контроля версий, такие как Git.
- **Низкие накладные расходы**: нет необходимости в сложных операциях с базой данных, подходит для легкого отслеживания состояния
- **Гибкая категоризация**: гибко упорядочивайте заметки по типам и тегам, поддерживая многомерный поиск.

(2) Типичные сценарии применения

NoteTool особенно подходит для следующих сценариев:

**Сценарий 1: Долгосрочное отслеживание проектов**

Представьте себе, что агент помогает выполнить большую задачу по рефакторингу кодовой базы, которая может занять дни или даже недели. NoteTool может записывать:

- `task_state`: статус и прогресс задачи текущего этапа.
- «заключение»: ключевые выводы после завершения каждого этапа.
- `blocker`: обнаруженные проблемы и точки блокировки.
- `действие`: Следующий план действий

```python
# Record task status
notes.run({
    "action": "create",
    "title": "Refactoring Project - Phase 1",
    "content": "Completed refactoring of data model layer, test coverage reached 85%. Next will refactor business logic layer.",
    "note_type": "task_state",
    "tags": ["refactoring", "phase1"]
})

# Record blocker
notes.run({
    "action": "create",
    "title": "Dependency Conflict Issue",
    "content": "Found some third-party library versions incompatible, need to resolve. Impact scope: 3 modules in business logic layer.",
    "note_type": "blocker",
    "tags": ["dependency", "urgent"]
})
```

**Сценарий 2: Управление исследовательскими задачами**

Интеллектуальный научный сотрудник, проводящий обзор литературы, может использовать NoteTool для записи:

- Основные точки зрения каждой статьи («заключение»)
- Темы, требующие углубленного изучения («действия»)
- Важные ссылки («ссылка»)

**Сценарий 3: Сотрудничество с ContextBuilder**

Перед каждым раундом диалога агент может получить соответствующие заметки через`search`или`list`операции и внедрить их в контекст:

```python
# In Agent's run method
def run(self, user_input: str) -> str:
    # 1. Retrieve relevant notes
    relevant_notes = self.note_tool.run({
        "action": "search",
        "query": user_input,
        "limit": 3
    })

    # 2. Convert note content to ContextPacket
    note_packets = []
    for note in relevant_notes:
        note_packets.append(ContextPacket(
            content=note['content'],
            timestamp=note['updated_at'],
            token_count=self._count_tokens(note['content']),
            relevance_score=0.7,
            metadata={"type": "note", "note_type": note['type']}
        ))

    # 3. Pass notes when building context
    context = self.context_builder.build(
        user_query=user_input,
        custom_packets=note_packets,
        ...
    )
```

### 9.4.2 Подробное объяснение формата хранения

NoteTool использует гибридный формат Markdown + YAML, который обеспечивает баланс структуры и читабельности.

(1) Формат файла примечания

Каждая нота является независимой`.md`файл следующего формата:

```markdown
---
id: note_20250119_153000_0
title: Project Progress - Phase 1
type: task_state
tags: [refactoring, phase1, backend]
created_at: 2025-01-19T15:30:00
updated_at: 2025-01-19T15:30:00
---

# Project Progress - Phase 1

## Completion Status

Completed refactoring of data model layer, main changes include:

1. Unified entity class naming conventions
2. Introduced type hints to improve code maintainability
3. Optimized database query performance

## Test Coverage

- Unit test coverage: 85%
- Integration test coverage: 70%

## Next Steps

1. Refactor business logic layer
2. Resolve dependency conflict issues
3. Increase integration test coverage to 85%
```

Преимущества этого формата:

- **Метаданные YAML**: машинный анализ, поддержка точного извлечения и извлечения полей.
- **Тело Markdown**: удобочитаемое, поддерживает расширенное форматирование (заголовки, списки, блоки кода и т. д.).
- **Имя файла как идентификатор**: упрощает управление: имя файла каждой заметки является ее уникальным идентификатором.

(2) Индексный файл

NoteTool поддерживает`notes_index.json`файл для быстрого поиска и управления заметками:

```json
{
  "note_20250119_153000_0": {
    "id": "note_20250119_153000_0",
    "title": "Project Progress - Phase 1",
    "type": "task_state",
    "tags": ["refactoring", "phase1", "backend"],
    "created_at": "2025-01-19T15:30:00",
    "updated_at": "2025-01-19T15:30:00",
    "file_path": "./notes/note_20250119_153000_0.md"
  }
}
```

Роль этого индексного файла:

- **Быстрый поиск**: не нужно открывать каждый файл, поиск прямо по индексу.
- **Управление метаданными**: централизованное управление метаданными для всех заметок.
- **Проверка целостности**: позволяет обнаружить отсутствующие или поврежденные файлы.

### 9.4.3 Подробное объяснение основных операций

NoteTool предоставляет семь основных операций, охватывающих полное управление жизненным циклом заметок.

(1) создать: Создать заметку

```python
def _create_note(
    self,
    title: str,
    content: str,
    note_type: str = "general",
    tags: Optional[List[str]] = None
) -> str:
    """Create note

    Args:
        title: Note title
        content: Note content (Markdown format)
        note_type: Note type (task_state/conclusion/blocker/action/reference/general)
        tags: Tag list

    Returns:
        str: Note ID
    """
    from datetime import datetime

    # 1. Generate unique ID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    note_id = f"note_{timestamp}_{len(self.index)}"

    # 2. Build metadata
    metadata = {
        "id": note_id,
        "title": title,
        "type": note_type,
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    # 3. Build complete Markdown file content
    md_content = self._build_markdown(metadata, content)

    # 4. Save to file
    file_path = os.path.join(self.workspace, f"{note_id}.md")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 5. Update index
    metadata["file_path"] = file_path
    self.index[note_id] = metadata
    self._save_index()

    return note_id

def _build_markdown(self, metadata: Dict, content: str) -> str:
    """Build Markdown file content (YAML + body)"""
    import yaml

    # YAML front matter
    yaml_header = yaml.dump(metadata, allow_unicode=True, sort_keys=False)

    # Combined format
    return f"---\n{yaml_header}---\n\n{content}"
```

Пример использования:

```python
from hello_agents.tools import NoteTool

notes = NoteTool(workspace="./project_notes")

note_id = notes.run({
    "action": "create",
    "title": "Refactoring Project - Phase 1",
    "content": """## Completion Status
Completed refactoring of data model layer, test coverage reached 85%.

## Next Steps
Refactor business logic layer""",
    "note_type": "task_state",
    "tags": ["refactoring", "phase1"]
})

print(f"✅ Note created successfully, ID: {note_id}")
```

(2) читать: Прочитать примечание

```python
def _read_note(self, note_id: str) -> Dict:
    """Read note content

    Args:
        note_id: Note ID

    Returns:
        Dict: Dictionary containing metadata and content
    """
    if note_id not in self.index:
        raise ValueError(f"Note does not exist: {note_id}")

    file_path = self.index[note_id]["file_path"]

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # Parse YAML metadata and Markdown body
    metadata, content = self._parse_markdown(raw_content)

    return {
        "metadata": metadata,
        "content": content
    }

def _parse_markdown(self, raw_content: str) -> Tuple[Dict, str]:
    """Parse Markdown file (separate YAML and body)"""
    import yaml

    # Find YAML delimiters
    parts = raw_content.split('---\n', 2)

    if len(parts) >= 3:
        # Has YAML front matter
        yaml_str = parts[1]
        content = parts[2].strip()
        metadata = yaml.safe_load(yaml_str)
    else:
        # No metadata, all as body
        metadata = {}
        content = raw_content.strip()

    return metadata, content
```

(3) обновление: обновление примечания

```python
def _update_note(
    self,
    note_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    note_type: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> str:
    """Update note

    Args:
        note_id: Note ID
        title: New title (optional)
        content: New content (optional)
        note_type: New type (optional)
        tags: New tags (optional)

    Returns:
        str: Operation result message
    """
    if note_id not in self.index:
        raise ValueError(f"Note does not exist: {note_id}")

    # 1. Read existing note
    note = self._read_note(note_id)
    metadata = note["metadata"]
    old_content = note["content"]

    # 2. Update fields
    if title:
        metadata["title"] = title
    if note_type:
        metadata["type"] = note_type
    if tags is not None:
        metadata["tags"] = tags
    if content is not None:
        old_content = content

    # Update timestamp
    from datetime import datetime
    metadata["updated_at"] = datetime.now().isoformat()

    # 3. Rebuild and save
    md_content = self._build_markdown(metadata, old_content)
    file_path = metadata["file_path"]

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 4. Update index
    self.index[note_id] = metadata
    self._save_index()

    return f"✅ Note updated: {metadata['title']}"
```

(4) поиск: Поиск по заметкам

```python
def _search_notes(
    self,
    query: str,
    limit: int = 10,
    note_type: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[Dict]:
    """Search notes

    Args:
        query: Search keyword
        limit: Return quantity limit
        note_type: Filter by type (optional)
        tags: Filter by tags (optional)

    Returns:
        List[Dict]: List of matching notes
    """
    results = []
    query_lower = query.lower()

    for note_id, metadata in self.index.items():
        # Type filter
        if note_type and metadata.get("type") != note_type:
            continue

        # Tag filter
        if tags:
            note_tags = set(metadata.get("tags", []))
            if not note_tags.intersection(tags):
                continue

        # Read note content
        try:
            note = self._read_note(note_id)
            content = note["content"]
            title = metadata.get("title", "")

            # Search in title and content
            if query_lower in title.lower() or query_lower in content.lower():
                results.append({
                    "note_id": note_id,
                    "title": title,
                    "type": metadata.get("type"),
                    "tags": metadata.get("tags", []),
                    "content": content,
                    "updated_at": metadata.get("updated_at")
                })
        except Exception as e:
            print(f"[WARNING] Failed to read note {note_id}: {e}")
            continue

    # Sort by update time
    results.sort(key=lambda x: x["updated_at"], reverse=True)

    return results[:limit]
```

(5) список: Список примечаний

```python
def _list_notes(
    self,
    note_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 20
) -> List[Dict]:
    """List notes (in reverse chronological order by update time)

    Args:
        note_type: Filter by type (optional)
        tags: Filter by tags (optional)
        limit: Return quantity limit

    Returns:
        List[Dict]: List of note metadata
    """
    results = []

    for note_id, metadata in self.index.items():
        # Type filter
        if note_type and metadata.get("type") != note_type:
            continue

        # Tag filter
        if tags:
            note_tags = set(metadata.get("tags", []))
            if not note_tags.intersection(tags):
                continue

        results.append(metadata)

    # Sort by update time
    results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

    return results[:limit]
```

(6) резюме: Краткое описание примечаний

```python
def _summary(self) -> Dict[str, Any]:
    """Generate note summary statistics

    Returns:
        Dict: Statistical information
    """
    total_count = len(self.index)

    # Count by type
    type_counts = {}
    for metadata in self.index.values():
        note_type = metadata.get("type", "general")
        type_counts[note_type] = type_counts.get(note_type, 0) + 1

    # Recently updated notes
    recent_notes = sorted(
        self.index.values(),
        key=lambda x: x.get("updated_at", ""),
        reverse=True
    )[:5]

    return {
        "total_notes": total_count,
        "type_distribution": type_counts,
        "recent_notes": [
            {
                "id": note["id"],
                "title": note.get("title", ""),
                "type": note.get("type"),
                "updated_at": note.get("updated_at")
            }
            for note in recent_notes
        ]
    }
```

(7) удалить: Удалить заметку

```python
def _delete_note(self, note_id: str) -> str:
    """Delete note

    Args:
        note_id: Note ID

    Returns:
        str: Operation result message
    """
    if note_id not in self.index:
        raise ValueError(f"Note does not exist: {note_id}")

    # 1. Delete file
    file_path = self.index[note_id]["file_path"]
    if os.path.exists(file_path):
        os.remove(file_path)

    # 2. Remove from index
    title = self.index[note_id].get("title", note_id)
    del self.index[note_id]
    self._save_index()

    return f"✅ Note deleted: {title}"
```

### 9.4.4 Глубокая интеграция с ContextBuilder

Истинная сила NoteTool заключается в его совместном использовании с ContextBuilder. Давайте продемонстрируем эту интеграцию на примере полного тематического исследования.

(1) Настройка сценария

Предположим, мы создаем помощника по долгосрочному проекту, которому необходимо:

1. Запись поэтапного хода проекта
2. Отслеживайте нерешенные проблемы
3. Автоматически просматривайте соответствующие заметки во время каждого разговора.
4. Предоставлять последовательные рекомендации, основанные на исторических заметках.

(2) Пример реализации

```python
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.context import ContextBuilder, ContextConfig, ContextPacket
from hello_agents.tools import MemoryTool, RAGTool, NoteTool
from datetime import datetime

class ProjectAssistant(SimpleAgent):
    """Long-term project assistant, integrating NoteTool and ContextBuilder"""

    def __init__(self, name: str, project_name: str, **kwargs):
        super().__init__(name=name, llm=HelloAgentsLLM(), **kwargs)

        self.project_name = project_name

        # Initialize tools
        self.memory_tool = MemoryTool(user_id=project_name)
        self.rag_tool = RAGTool(knowledge_base_path=f"./{project_name}_kb")
        self.note_tool = NoteTool(workspace=f"./{project_name}_notes")

        # Initialize context builder
        self.context_builder = ContextBuilder(
            memory_tool=self.memory_tool,
            rag_tool=self.rag_tool,
            config=ContextConfig(max_tokens=4000)
        )

        self.conversation_history = []

    def run(self, user_input: str, note_as_action: bool = False) -> str:
        """Run assistant, automatically integrate notes"""

        # 1. Retrieve relevant notes from NoteTool
        relevant_notes = self._retrieve_relevant_notes(user_input)

        # 2. Convert notes to ContextPacket
        note_packets = self._notes_to_packets(relevant_notes)

        # 3. Build optimized context
        context = self.context_builder.build(
            user_query=user_input,
            conversation_history=self.conversation_history,
            system_instructions=self._build_system_instructions(),
            custom_packets=note_packets
        )

        # 4. Call LLM
        response = self.llm.invoke(context)

        # 5. If needed, record interaction as note
        if note_as_action:
            self._save_as_note(user_input, response)

        # 6. Update conversation history
        self._update_history(user_input, response)

        return response

    def _retrieve_relevant_notes(self, query: str, limit: int = 3) -> List[Dict]:
        """Retrieve relevant notes"""
        try:
            # Prioritize retrieving blocker and action type notes
            blockers = self.note_tool.run({
                "action": "list",
                "note_type": "blocker",
                "limit": 2
            })

            # General search
            search_results = self.note_tool.run({
                "action": "search",
                "query": query,
                "limit": limit
            })

            # Merge and deduplicate
            all_notes = {note['note_id']: note for note in blockers + search_results}
            return list(all_notes.values())[:limit]

        except Exception as e:
            print(f"[WARNING] Note retrieval failed: {e}")
            return []

    def _notes_to_packets(self, notes: List[Dict]) -> List[ContextPacket]:
        """Convert notes to context packets"""
        packets = []

        for note in notes:
            content = f"[Note: {note['title']}]\n{note['content']}"

            packets.append(ContextPacket(
                content=content,
                timestamp=datetime.fromisoformat(note['updated_at']),
                token_count=len(content) // 4,  # Simple estimation
                relevance_score=0.75,  # Notes have high relevance
                metadata={
                    "type": "note",
                    "note_type": note['type'],
                    "note_id": note['note_id']
                }
            ))

        return packets

    def _save_as_note(self, user_input: str, response: str):
        """Save interaction as note"""
        try:
            # Determine what type of note to save
            if "problem" in user_input.lower() or "blocker" in user_input.lower():
                note_type = "blocker"
            elif "plan" in user_input.lower() or "next" in user_input.lower():
                note_type = "action"
            else:
                note_type = "conclusion"

            self.note_tool.run({
                "action": "create",
                "title": f"{user_input[:30]}...",
                "content": f"## Question\n{user_input}\n\n## Analysis\n{response}",
                "note_type": note_type,
                "tags": [self.project_name, "auto_generated"]
            })

        except Exception as e:
            print(f"[WARNING] Failed to save note: {e}")

    def _build_system_instructions(self) -> str:
        """Build system instructions"""
        return f"""You are a long-term assistant for the {self.project_name} project.

Your responsibilities:
1. Provide coherent recommendations based on historical notes
2. Track project progress and pending issues
3. Reference relevant historical notes when answering
4. Provide specific, actionable next-step recommendations

Notes:
- Prioritize issues marked as blockers
- Indicate source of basis in recommendations (notes, memory, or knowledge base)
- Maintain awareness of overall project progress"""

    def _update_history(self, user_input: str, response: str):
        """Update conversation history"""
        from hello_agents.core.message import Message

        self.conversation_history.append(
            Message(content=user_input, role="user", timestamp=datetime.now())
        )
        self.conversation_history.append(
            Message(content=response, role="assistant", timestamp=datetime.now())
        )

        # Limit history length
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

# Usage example
assistant = ProjectAssistant(
    name="Project Assistant",
    project_name="data_pipeline_refactoring"
)

# First interaction: Record project status
response = assistant.run(
    "We have completed refactoring of the data model layer, test coverage reached 85%. Next plan is to refactor the business logic layer.",
    note_as_action=True
)

# Second interaction: Raise issue
response = assistant.run(
    "When refactoring the business logic layer, I encountered dependency version conflict issues. How should I resolve this?"
)

# View note summary
summary = assistant.note_tool.run({"action": "summary"})
print(summary)
```

(3) Демонстрация эффекта бега

```bash
[ContextBuilder] Collected 8 candidate information packages
[ContextBuilder] Selected 7 information packages, total 3500 tokens

✅ Assistant answer:

I noticed this issue was mentioned in your previously recorded notes. According to the note [Refactoring Project - Phase 1], your current test coverage has reached 85%, which is a good foundation.

Regarding the dependency version conflict issue, I recommend:

1. **Use virtual environment isolation**: Create an independent virtual environment for the business logic layer to avoid dependency conflicts with other modules
2. **Lock versions**: Explicitly specify exact versions of all dependencies in requirements.txt
3. **Use pipdeptree**: Analyze the dependency tree to find the root cause of conflicts

I will mark this issue as a blocker and recommend prioritizing its resolution.

[Source: Note note_20250119_153000_0, Project knowledge base]

---

📋 Note summary:
{
  "total_notes": 2,
  "type_distribution": {
    "action": 1,
    "blocker": 1
  },
  "recent_notes": [
    {
      "id": "note_20250119_154500_1",
      "title": "When refactoring the business logic layer, I encountered dependency version conflict issues...",
      "type": "blocker",
      "updated_at": "2025-01-19T15:45:00"
    },
    {
      "id": "note_20250119_153000_0",
      "title": "We have completed refactoring of the data model layer...",
      "type": "action",
      "updated_at": "2025-01-19T15:30:00"
    }
  ]
}
```

### 9.4.5 Лучшие практики

При фактическом использовании NoteTool следующие рекомендации помогут вам создать более мощные долгосрочные агенты:

1. **Разумная классификация заметок**:
   - `task_state`: запись поэтапного прогресса и статуса.
   - `заключение`: запишите важные выводы и заключения.
   - `blocker`: проблемы с блокировкой записи, наивысший приоритет.
   - `action`: Запишите следующие планы действий.
   - `ссылка`: записывайте важные справочные материалы.

2. **Регулярная очистка и архивирование**:
   - Для устраненных блокировщиков обновите до завершения
   - Если действия устарели, немедленно удалите или обновите их.
   - Используйте теги для управления версиями, например `["v1.0", "completed"]`

3. **Сотрудничество с ContextBuilder**:
   - Получайте соответствующие заметки перед каждым раундом диалога.
   - Установите разные оценки релевантности в зависимости от типа заметки (блокировщик > действие > заключение).
   - Ограничьте количество заметок, чтобы избежать перегрузки контекста.

4. **Взаимодействие человека и машины**:
   - Заметки представлены в удобочитаемом формате Markdown, поддерживающем ручное редактирование.
   - Используйте Git для контроля версий, чтобы отслеживать развитие заметок.
   - На ключевых этапах вручную просматривайте заметки, созданные агентом

5. **Автоматизированный рабочий процесс**:
   - Регулярно создавать сводные отчеты о заметках
   - Автоматически создавать документы о ходе проекта на основе заметок
   - Синхронизировать содержимое заметок с другими системами (такими как Notion, Confluence)

## 9.5 TerminalTool: мгновенный доступ к файловой системе

В предыдущих главах мы представили MemoryTool и RAGTool, которые обеспечивают возможности разговорной памяти и извлечения знаний соответственно. Однако во многих практических сценариях агентам требуется **мгновенный доступ и исследование файловой системы** — просмотр файлов журналов, анализ структуры кодовой базы, получение файлов конфигурации и т. д. Именно здесь на помощь приходит TerminalTool.

TerminalTool предоставляет агентам **возможность безопасного выполнения из командной строки**, поддерживает общие команды файловой системы и обработки текста, обеспечивая при этом безопасность системы с помощью многоуровневых механизмов безопасности. Эта конструкция реализует концепцию «контекста точно в срок (JIT)», упомянутую в разделе 9.2.2 — агентам не нужно предварительно загружать все файлы, но они должны исследовать и извлекать их по требованию.

### 9.5.1 Философия проектирования и механизмы безопасности

(1) Зачем нам нужен TerminalTool?

При создании долгосрочных агентов мы часто сталкиваемся со следующими сценариями:

**Сценарий 1: Исследование кодовой базы**

Помощник по разработке должен помочь пользователям понять структуру большой базы кода:

```python
# Traditional approach: Pre-index all files (high cost, may be outdated)
rag_tool.add_document("./project/**/*.py")  # Time-consuming, occupies large storage

# TerminalTool approach: Instant exploration
terminal.run({"command": "find . -name '*.py' -type f"})  # Fast, real-time
terminal.run({"command": "grep -r 'class UserService' ."})  # Precise location
terminal.run({"command": "head -n 50 src/services/user.py"})  # View on demand
```

**Сценарий 2: Анализ файла журнала**

Помощнику по эксплуатации необходимо проанализировать журналы приложений:

```python
# Check log file size
terminal.run({"command": "ls -lh /var/log/app.log"})

# View latest error logs
terminal.run({"command": "tail -n 100 /var/log/app.log | grep ERROR"})

# Count error type distribution
terminal.run({"command": "grep ERROR /var/log/app.log | cut -d':' -f3 | sort | uniq -c"})
```

**Сценарий 3: Предварительный просмотр файла данных**

Помощнику по анализу данных необходимо быстро понять структуру файлов данных:

```python
# View first few lines of CSV file
terminal.run({"command": "head -n 5 data/sales.csv"})

# Count lines
terminal.run({"command": "wc -l data/*.csv"})

# View column names
terminal.run({"command": "head -n 1 data/sales.csv | tr ',' '\n'"})
```

Общая характеристика этих сценариев: **требуется облегченный доступ к файловой системе в реальном времени, а не предварительная индексация и векторизация**. TerminalTool предназначен именно для такого «исследовательского» рабочего процесса.

(2) Подробное объяснение механизма безопасности

Разрешение агентам выполнять команды — мощная, но опасная возможность. TerminalTool обеспечивает безопасность системы с помощью многоуровневых механизмов безопасности:

**Первый уровень: Белый список команд**

Разрешить только безопасные команды только для чтения и полностью запретить любые операции, которые могут изменить систему:

```python
ALLOWED_COMMANDS = {
    # File listing and information
    'ls', 'dir', 'tree',
    # File content viewing
    'cat', 'head', 'tail', 'less', 'more',
    # File search
    'find', 'grep', 'egrep', 'fgrep',
    # Text processing
    'wc', 'sort', 'uniq', 'cut', 'awk', 'sed',
    # Directory operations
    'pwd', 'cd',
    # File information
    'file', 'stat', 'du', 'df',
    # Others
    'echo', 'which', 'whereis',
}
```

Если агент попытается выполнить команду вне белого списка, она будет немедленно отклонена:

```python
terminal.run({"command": "rm -rf /"})
# ❌ Command not allowed: rm
# Allowed commands: cat, cd, cut, dir, du, ...
```

**Второй уровень: ограничение рабочих каталогов (песочница)**

TerminalTool может получить доступ только к указанному рабочему каталогу и его подкаталогам, но не может получить доступ к другим частям системы:

```python
# Specify working directory during initialization
terminal = TerminalTool(workspace="./project")

# Allowed: Access files within working directory
terminal.run({"command": "cat ./src/main.py"})  # ✅

# Prohibited: Access files outside working directory
terminal.run({"command": "cat /etc/passwd"})  # ❌ Not allowed to access paths outside working directory

# Prohibited: Escape through ..
terminal.run({"command": "cd ../../../etc"})  # ❌ Not allowed to access paths outside working directory
```

Этот механизм песочницы гарантирует, что даже если поведение агента является ненормальным, оно не сможет повлиять на другие части системы.

**Третий уровень: контроль тайм-аута**

Каждая команда имеет ограничение по времени выполнения, чтобы предотвратить бесконечные циклы или истощение ресурсов:

```python
terminal = TerminalTool(
    workspace="./project",
    timeout=30  # 30 second timeout
)

# If command execution exceeds 30 seconds
terminal.run({"command": "find / -name '*.log'"})
# ❌ Command execution timeout (exceeded 30 seconds)
```

**Четвертый уровень: ограничение размера вывода**

Ограничьте размер вывода команды, чтобы предотвратить переполнение памяти:

```python
terminal = TerminalTool(
    workspace="./project",
    max_output_size=10 * 1024 * 1024  # 10MB
)

# If output exceeds 10MB
terminal.run({"command": "cat huge_file.log"})
# ... (first 10MB of content) ...
# ⚠️ Output truncated (exceeded 10485760 bytes)
```

Благодаря этим четырем уровням механизмов безопасности TerminalTool предоставляет мощные возможности, одновременно обеспечивая максимальную безопасность системы.

### 9.5.2 Подробное объяснение основных функций

Реализация TerminalTool фокусируется на двух основных функциях: выполнении команд и навигации по каталогам.

(1) Выполнение команды

Ядро`_execute_command`метод отвечает за фактическое выполнение команд:

```python
def _execute_command(self, command: str) -> str:
    """Execute command"""
    try:
        # Execute command in current directory
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(self.current_dir),  # Execute in current working directory
            capture_output=True,
            text=True,
            timeout=self.timeout,
            env=os.environ.copy()
        )

        # Merge standard output and standard error
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"

        # Check output size
        if len(output) > self.max_output_size:
            output = output[:self.max_output_size]
            output += f"\n\n⚠️ Output truncated (exceeded {self.max_output_size} bytes)"

        # Add return code information
        if result.returncode != 0:
            output = f"⚠️ Command return code: {result.returncode}\n\n{output}"

        return output if output else "✅ Command executed successfully (no output)"

    except subprocess.TimeoutExpired:
        return f"❌ Command execution timeout (exceeded {self.timeout} seconds)"
    except Exception as e:
        return f"❌ Command execution failed: {e}"
```

Ключевые моменты этой реализации:

- **Информация о текущем каталоге**: используйте параметр cwd для выполнения команд в правильном каталоге.
- **Обработка ошибок**: фиксируйте и объединяйте стандартные ошибки, предоставляйте полную диагностическую информацию.
- **Проверка кода возврата**: ненулевые коды возврата помечаются как предупреждения.
- **Отказоустойчивая конструкция**: тайм-ауты и исключения обрабатываются правильно, не приводят к сбою агента.

(2) Навигация по каталогам

Специальное обращение с`cd`команда поддерживает навигацию агента по файловой системе:

```python
def _handle_cd(self, parts: List[str]) -> str:
    """Handle cd command"""
    if not self.allow_cd:
        return "❌ cd command is disabled"

    if len(parts) < 2:
        # cd without parameters, return current directory
        return f"Current directory: {self.current_dir}"

    target_dir = parts[1]

    # Handle relative path
    if target_dir == "..":
        new_dir = self.current_dir.parent
    elif target_dir == ".":
        new_dir = self.current_dir
    elif target_dir == "~":
        new_dir = self.workspace
    else:
        new_dir = (self.current_dir / target_dir).resolve()

    # Check if within working directory
    try:
        new_dir.relative_to(self.workspace)
    except ValueError:
        return f"❌ Not allowed to access paths outside working directory: {new_dir}"

    # Check if directory exists
    if not new_dir.exists():
        return f"❌ Directory does not exist: {new_dir}"

    if not new_dir.is_dir():
        return f"❌ Not a directory: {new_dir}"

    # Update current directory
    self.current_dir = new_dir
    return f"✅ Switched to directory: {self.current_dir}"
```

Эта конструкция поддерживает агентов в многоэтапном исследовании файловой системы:

```python
# Step 1: View project structure
terminal.run({"command": "ls -la"})

# Step 2: Enter source code directory
terminal.run({"command": "cd src"})

# Step 3: Find specific files
terminal.run({"command": "find . -name '*service*.py'"})

# Step 4: View file content
terminal.run({"command": "cat user_service.py"})
```

### 9.5.3 Типичные шаблоны использования

TerminalTool поддерживает различные общие шаблоны работы файловой системы.

(1) Исследовательская навигация

Агенты могут шаг за шагом исследовать кодовые базы, как разработчики-люди:

```python
from hello_agents.tools import TerminalTool

terminal = TerminalTool(workspace="./my_project")

# Step 1: View project root directory
print(terminal.run({"command": "ls -la"}))
"""
total 24
drwxr-xr-x  6 user  staff   192 Jan 19 16:00 .
drwxr-xr-x  5 user  staff   160 Jan 19 15:30 ..
-rw-r--r--  1 user  staff  1234 Jan 19 15:30 README.md
drwxr-xr-x  4 user  staff   128 Jan 19 15:30 src
drwxr-xr-x  3 user  staff    96 Jan 19 15:30 tests
-rw-r--r--  1 user  staff   456 Jan 19 15:30 requirements.txt
"""

# Step 2: View source code directory structure
terminal.run({"command": "cd src"})
print(terminal.run({"command": "tree"}))

# Step 3: Search for specific patterns
print(terminal.run({"command": "grep -r 'def process' ."}))
```

(2) Анализ файла данных

Быстро разобраться в структуре и содержимом файлов данных:

```python
terminal = TerminalTool(workspace="./data")

# View first few lines of CSV file
print(terminal.run({"command": "head -n 5 sales_2024.csv"}))
"""
date,product,quantity,revenue
2024-01-01,Widget A,150,4500.00
2024-01-01,Widget B,200,8000.00
2024-01-02,Widget A,180,5400.00
2024-01-02,Widget C,120,3600.00
"""

# Count total lines
print(terminal.run({"command": "wc -l *.csv"}))
"""
  10234 sales_2024.csv
   8567 sales_2023.csv
  18801 total
"""

# Extract and count product categories
print(terminal.run({"command": "tail -n +2 sales_2024.csv | cut -d',' -f2 | sort | uniq -c"}))
"""
  3456 Widget A
  4123 Widget B
  2655 Widget C
"""
```

(3) Анализ файла журнала

Анализ журналов приложений в режиме реального времени позволяет быстро обнаруживать проблемы:

```python
terminal = TerminalTool(workspace="/var/log")

# View latest error logs
print(terminal.run({"command": "tail -n 50 app.log | grep ERROR"}))

# Count error type distribution
print(terminal.run({"command": "grep ERROR app.log | awk '{print $4}' | sort | uniq -c | sort -rn"}))
"""
  245 DatabaseConnectionError
  123 TimeoutException
   67 ValidationError
   34 AuthenticationError
"""

# Find logs for specific time period
print(terminal.run({"command": "grep '2024-01-19 15:' app.log | tail -n 20"}))
```

(4) Анализ кодовой базы

Помогите просмотреть и понять код:

```python
terminal = TerminalTool(workspace="./codebase")

# Count lines of code
print(terminal.run({"command": "find . -name '*.py' -exec wc -l {} + | tail -n 1"}))

# Find all TODO comments
print(terminal.run({"command": "grep -rn 'TODO' --include='*.py'"}))

# Find definition of specific function
print(terminal.run({"command": "grep -rn 'def process_data' --include='*.py'"}))

# View function implementation
print(terminal.run({"command": "sed -n '/def process_data/,/^def /p' src/processor.py | head -n -1"}))
```

### 9.5.4 Сотрудничество с другими инструментами

Истинная сила TerminalTool заключается в его совместном использовании с MemoryTool, NoteTool и ContextBuilder.

(1) Сотрудничество с MemoryTool

Информация, обнаруженная TerminalTool, может храниться в системе памяти:

```python
# Use TerminalTool to discover project structure
structure = terminal.run({"command": "tree -L 2 src"})

# Store in semantic memory
memory_tool.run({
    "action": "add",
    "content": f"Project structure:\n{structure}",
    "memory_type": "semantic",
    "importance": 0.8,
    "metadata": {"type": "project_structure"}
})
```

(2) Сотрудничество с NoteTool

Важные открытия можно записывать в виде структурированных заметок:

```python
# Discover a performance bottleneck
log_analysis = terminal.run({"command": "grep 'slow query' app.log | tail -n 10"})

# Record as blocker note
note_tool.run({
    "action": "create",
    "title": "Database Slow Query Issue",
    "content": f"## Problem Description\nFound multiple slow queries affecting system performance\n\n## Log Analysis\n```\n{log_anaанализ}\n```\n\n## Next Steps\n1. Analyze slow query SQL\n2. Add indexes\n3. Optimize query logic",
    "note_type": "blocker",
    "tags": ["performance", "database"]
})
```

(3) Сотрудничество с ContextBuilder

Вывод TerminalTool может быть частью контекста:

```python
# Explore codebase
code_structure = terminal.run({"command": "ls -R src"})
recent_changes = terminal.run({"command": "git log --oneline -10"})

# Convert to ContextPacket
from hello_agents.context import ContextPacket
from datetime import datetime

packets = [
    ContextPacket(
        content=f"Codebase structure:\n{code_structure}",
        timestamp=datetime.now(),
        token_count=len(code_structure) // 4,
        relevance_score=0.7,
        metadata={"type": "code_structure", "source": "terminal"}
    ),
    ContextPacket(
        content=f"Recent commits:\n{recent_changes}",
        timestamp=datetime.now(),
        token_count=len(recent_changes) // 4,
        relevance_score=0.8,
        metadata={"type": "git_history", "source": "terminal"}
    )
]

# Include this information when building context
context = context_builder.build(
    user_query="How to refactor the user service module?",
    custom_packets=packets
)
```

## 9.6 Агент дальнего горизонта на практике: помощник по обслуживанию кодовой базы

Теперь давайте интегрируем ContextBuilder, NoteTool и TerminalTool, чтобы создать полноценный долгосрочный агент — **Помощник по обслуживанию кодовой базы**. Этот помощник может:

1. Изучите и поймите структуру кодовой базы
2. Записывайте обнаруженные проблемы и точки улучшения.
3. Отслеживайте долгосрочные задачи рефакторинга
4. Поддерживать согласованность в условиях ограничений контекстного окна.

### 9.6.1 Настройка сценария и анализ требований

**Бизнес-сценарий**

Предположим, мы поддерживаем веб-приложение Python среднего размера. Эта база кода содержит около 50 файлов Python, созданных с помощью платформы Flask и охватывающих модели данных, бизнес-логику, интерфейсы API и другие модули, а также имеет некоторый технический долг, который необходимо постепенно устранять. В этом сценарии нам нужен интеллектуальный помощник, который поможет нам изучить базу кода, понять структуру проекта, зависимости и стиль кода; выявлять проблемы в коде, такие как дублирование кода, чрезмерная сложность, отсутствие тестов и т. д.; отслеживать ход выполнения задач, записывать задачи, выполненную работу и встреченные блокировщики; и предоставлять последовательные рекомендации по рефакторингу, основанные на историческом контексте.

**Проблемы и решения**

Этот сценарий сталкивается с несколькими типичными проблемами долгосрочных задач. Во-первых, это проблема информации, выходящей за пределы контекстного окна: вся кодовая база может содержать десятки тысяч строк кода, которые невозможно поместить в контекстное окно сразу. Мы решаем эту проблему, используя TerminalTool для мгновенного исследования кода по требованию, просматривая определенные файлы только при необходимости. Во-вторых, это проблема управления состоянием между сеансами: задачи рефакторинга могут длиться несколько дней, и необходимо поддерживать прогресс на протяжении нескольких сеансов. Мы решаем эту проблему, используя NoteTool для записи поэтапного прогресса, задач и ключевых решений. Наконец, существует проблема качества и актуальности контекста: каждый разговор должен рассматривать соответствующую историческую информацию, но не должен быть перегружен нерелевантной информацией. Мы используем ContextBuilder для интеллектуальной фильтрации и организации контекста, обеспечивая высокую плотность сигнала.

### 9.6.2 Проектирование архитектуры системы

Наш помощник по обслуживанию кодовой базы использует трехуровневую архитектуру, как показано на рисунке 9.3:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/9-figures/9-3.png" alt="" width="85%"/>
  <p>Рисунок 9.3 Трехуровневая архитектура помощника по обслуживанию кодовой базы</p>
</div>

### 9.6.3 Основная реализация

Теперь давайте реализуем основной класс этой системы:

```python
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.context import ContextBuilder, ContextConfig, ContextPacket
from hello_agents.tools import MemoryTool, NoteTool, TerminalTool
from hello_agents.core.message import Message


class CodebaseMaintainer:
    """Codebase Maintenance Assistant - Long-horizon agent example

    Integrates ContextBuilder + NoteTool + TerminalTool + MemoryTool
    Implements cross-session codebase maintenance task management
    """

    def __init__(
        self,
        project_name: str,
        codebase_path: str,
        llm: Optional[HelloAgentsLLM] = None
    ):
        self.project_name = project_name
        self.codebase_path = codebase_path
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize LLM
        self.llm = llm or HelloAgentsLLM()

        # Initialize tools
        self.memory_tool = MemoryTool(user_id=project_name)
        self.note_tool = NoteTool(workspace=f"./{project_name}_notes")
        self.terminal_tool = TerminalTool(workspace=codebase_path, timeout=60)

        # Initialize context builder
        self.context_builder = ContextBuilder(
            memory_tool=self.memory_tool,
            rag_tool=None,  # This case does not use RAG
            config=ContextConfig(
                max_tokens=4000,
                reserve_ratio=0.15,
                min_relevance=0.2,
                enable_compression=True
            )
        )

        # Conversation history
        self.conversation_history: List[Message] = []

        # Statistics
        self.stats = {
            "session_start": datetime.now(),
            "commands_executed": 0,
            "notes_created": 0,
            "issues_found": 0
        }

        print(f"✅ Codebase maintenance assistant initialized: {project_name}")
        print(f"📁 Working directory: {codebase_path}")
        print(f"🆔 Session ID: {self.session_id}")

    def run(self, user_input: str, mode: str = "auto") -> str:
        """Run assistant

        Args:
            user_input: User input
            mode: Running mode
                - "auto": Automatically decide whether to use tools
                - "explore": Focus on code exploration
                - "analyze": Focus on problem analysis
                - "plan": Focus on task planning

        Returns:
            str: Assistant's answer
        """
        print(f"\n{'='*80}")
        print(f"👤 User: {user_input}")
        print(f"{'='*80}\n")

        # Step 1: Execute preprocessing based on mode
        pre_context = self._preprocess_by_mode(user_input, mode)

        # Step 2: Retrieve relevant notes
        relevant_notes = self._retrieve_relevant_notes(user_input)
        note_packets = self._notes_to_packets(relevant_notes)

        # Step 3: Build optimized context
        context = self.context_builder.build(
            user_query=user_input,
            conversation_history=self.conversation_history,
            system_instructions=self._build_system_instructions(mode),
            custom_packets=note_packets + pre_context
        )

        # Step 4: Call LLM
        print("🤖 Thinking...")
        response = self.llm.invoke(context)

        # Step 5: Post-processing
        self._postprocess_response(user_input, response)

        # Step 6: Update conversation history
        self._update_history(user_input, response)

        print(f"\n🤖 Assistant: {response}\n")
        print(f"{'='*80}\n")

        return response

    def _preprocess_by_mode(
        self,
        user_input: str,
        mode: str
    ) -> List[ContextPacket]:
        """Execute preprocessing based on mode, collect relevant information"""
        packets = []

        if mode == "explore" or mode == "auto":
            # Explore mode: Automatically view project structure
            print("🔍 Exploring codebase structure...")

            structure = self.terminal_tool.run({"command": "find . -type f -name '*.py' | head -n 20"})
            self.stats["commands_executed"] += 1

            packets.append(ContextPacket(
                content=f"[Codebase Structure]\n{structure}",
                timestamp=datetime.now(),
                token_count=len(structure) // 4,
                relevance_score=0.6,
                metadata={"type": "code_structure", "source": "terminal"}
            ))

        if mode == "analyze":
            # Analyze mode: Check code complexity and issues
            print("📊 Analyzing code quality...")

            # Count lines of code
            loc = self.terminal_tool.run({"command": "find . -name '*.py' -exec wc -l {} + | tail -n 1"})

            # Find TODO and FIXME
            todos = self.terminal_tool.run({"command": "grep -rn 'TODO\\|FIXME' --include='*.py' | head -n 10"})

            self.stats["commands_executed"] += 2

            packets.append(ContextPacket(
                content=f"[Code Statistics]\n{loc}\n\n[To-Do Items]\n{todos}",
                timestamp=datetime.now(),
                token_count=(len(loc) + len(todos)) // 4,
                relevance_score=0.7,
                metadata={"type": "code_analysis", "source": "terminal"}
            ))

        if mode == "plan":
            # Planning mode: Load recent notes
            print("📋 Loading task planning...")

            task_notes = self.note_tool.run({
                "action": "list",
                "note_type": "task_state",
                "limit": 3
            })

            if task_notes:
                content = "\n".join([f"- {note['title']}" for note in task_notes])
                packets.append(ContextPacket(
                    content=f"[Current Tasks]\n{content}",
                    timestamp=datetime.now(),
                    token_count=len(content) // 4,
                    relevance_score=0.8,
                    metadata={"type": "task_plan", "source": "notes"}
                ))

        return packets

    def _retrieve_relevant_notes(self, query: str, limit: int = 3) -> List[Dict]:
        """Retrieve relevant notes"""
        try:
            # Prioritize retrieving blockers
            blockers = self.note_tool.run({
                "action": "list",
                "note_type": "blocker",
                "limit": 2
            })

            # Search relevant notes
            search_results = self.note_tool.run({
                "action": "search",
                "query": query,
                "limit": limit
            })

            # Merge and deduplicate
            all_notes = {note.get('note_id') or note.get('id'): note for note in (blockers or []) + (search_results or [])}
            return list(all_notes.values())[:limit]

        except Exception as e:
            print(f"[WARNING] Note retrieval failed: {e}")
            return []

    def _notes_to_packets(self, notes: List[Dict]) -> List[ContextPacket]:
        """Convert notes to context packets"""
        packets = []

        for note in notes:
            # Set different relevance scores based on note type
            relevance_map = {
                "blocker": 0.9,
                "action": 0.8,
                "task_state": 0.75,
                "conclusion": 0.7
            }

            note_type = note.get('type', 'general')
            relevance = relevance_map.get(note_type, 0.6)

            content = f"[Note: {note.get('title', 'Untitled')}]\nType: {note_type}\n\n{note.get('content', '')}"

            packets.append(ContextPacket(
                content=content,
                timestamp=datetime.fromisoformat(note.get('updated_at', datetime.now().isoformat())),
                token_count=len(content) // 4,
                relevance_score=relevance,
                metadata={
                    "type": "note",
                    "note_type": note_type,
                    "note_id": note.get('note_id') or note.get('id')
                }
            ))

        return packets

    def _build_system_instructions(self, mode: str) -> str:
        """Build system instructions"""
        base_instructions = f"""You are the codebase maintenance assistant for the {self.project_name} project.

Your core capabilities:
1. Use TerminalTool to explore codebase (ls, cat, grep, find, etc.)
2. Use NoteTool to record discoveries and tasks
3. Provide coherent recommendations based on historical notes

Current session ID: {self.session_id}
"""

        mode_specific = {
            "explore": """
Current mode: Explore codebase

You should:
- Actively use terminal commands to understand code structure
- Identify key modules and files
- Record project architecture in notes
""",
            "analyze": """
Current mode: Analyze code quality

You should:
- Find code issues (duplication, complexity, TODOs, etc.)
- Evaluate code quality
- Record discovered issues as blocker or action notes
""",
            "plan": """
Current mode: Task planning

You should:
- Review historical notes and tasks
- Formulate next action plan
- Update task status notes
""",
            "auto": """
Current mode: Auto decision

You should:
- Flexibly choose strategies based on user needs
- Use tools when needed
- Maintain professionalism and practicality in responses
"""
        }

        return base_instructions + mode_specific.get(mode, mode_specific["auto"])

    def _postprocess_response(self, user_input: str, response: str):
        """Post-processing: Analyze response, automatically record important information"""

        # If issues found, automatically create blocker note
        if any(keyword in response.lower() for keyword in ["issue", "bug", "error", "blocker", "problem"]):
            try:
                self.note_tool.run({
                    "action": "create",
                    "title": f"Issue found: {user_input[:30]}...",
                    "content": f"## User Input\n{user_input}\n\n## Issue Analysis\n{response[:500]}...",
                    "note_type": "blocker",
                    "tags": [self.project_name, "auto_detected", self.session_id]
                })
                self.stats["notes_created"] += 1
                self.stats["issues_found"] += 1
                print("📝 Automatically created issue note")
            except Exception as e:
                print(f"[WARNING] Failed to create note: {e}")

        # If task planning, automatically create action note
        elif any(keyword in user_input.lower() for keyword in ["plan", "next", "task", "todo"]):
            try:
                self.note_tool.run({
                    "action": "create",
                    "title": f"Task planning: {user_input[:30]}...",
                    "content": f"## Discussion\n{user_input}\n\n## Action Plan\n{response[:500]}...",
                    "note_type": "action",
                    "tags": [self.project_name, "planning", self.session_id]
                })
                self.stats["notes_created"] += 1
                print("📝 Automatically created action plan note")
            except Exception as e:
                print(f"[WARNING] Failed to create note: {e}")

    def _update_history(self, user_input: str, response: str):
        """Update conversation history"""
        self.conversation_history.append(
            Message(content=user_input, role="user", timestamp=datetime.now())
        )
        self.conversation_history.append(
            Message(content=response, role="assistant", timestamp=datetime.now())
        )

        # Limit history length (keep recent 10 rounds of conversation)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    # === Convenience methods ===

    def explore(self, target: str = ".") -> str:
        """Explore codebase"""
        return self.run(f"Please explore the code structure of {target}", mode="explore")

    def analyze(self, focus: str = "") -> str:
        """Analyze code quality"""
        query = f"Please analyze code quality" + (f", focusing on {focus}" if focus else "")
        return self.run(query, mode="analyze")

    def plan_next_steps(self) -> str:
        """Plan next steps"""
        return self.run("Based on current progress, plan next steps", mode="plan")

    def execute_command(self, command: str) -> str:
        """Execute terminal command"""
        result = self.terminal_tool.run({"command": command})
        self.stats["commands_executed"] += 1
        return result

    def create_note(
        self,
        title: str,
        content: str,
        note_type: str = "general",
        tags: List[str] = None
    ) -> str:
        """Create note"""
        result = self.note_tool.run({
            "action": "create",
            "title": title,
            "content": content,
            "note_type": note_type,
            "tags": tags or [self.project_name]
        })
        self.stats["notes_created"] += 1
        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        duration = (datetime.now() - self.stats["session_start"]).total_seconds()

        # Get note summary
        try:
            note_summary = self.note_tool.run({"action": "summary"})
        except:
            note_summary = {}

        return {
            "session_info": {
                "session_id": self.session_id,
                "project": self.project_name,
                "duration_seconds": duration
            },
            "activity": {
                "commands_executed": self.stats["commands_executed"],
                "notes_created": self.stats["notes_created"],
                "issues_found": self.stats["issues_found"]
            },
            "notes": note_summary
        }

    def generate_report(self, save_to_file: bool = True) -> Dict[str, Any]:
        """Generate session report"""
        report = self.get_stats()

        if save_to_file:
            report_file = f"maintainer_report_{self.session_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            report["report_file"] = report_file
            print(f"📄 Report saved: {report_file}")

        return report
```

### 9.6.4 Полный пример использования

Теперь давайте продемонстрируем рабочий процесс этого долгосрочного агента на примере полного сценария использования:

```python
# ========== Initialize Assistant ==========

from hello_agents import HelloAgentsLLM

maintainer = CodebaseMaintainer(
    project_name="my_flask_app",
    codebase_path="./my_flask_app",
    llm=HelloAgentsLLM()
)


# ========== Day 1: Explore Codebase ==========
# 1. Initial exploration
response = maintainer.explore()
"""
🔍 Exploring codebase structure...
🤖 Thinking...

🤖 Assistant: I have scanned the codebase, this is a Flask web application, mainly containing the following modules:

📁 Project structure:
- app/
  ├── models/      # Data models (User, Product, Order, etc.)
  ├── routes/      # API routes
  ├── services/    # Business logic
  └── utils/       # Utility functions
- tests/           # Test files
- migrations/      # Database migrations
- config.py        # Configuration file

Total approximately 3,500 lines of Python code.

Recommended next steps:
1. Review core model definitions
2. Check routes and API design
3. Evaluate test coverage
"""

# 2. Deep dive into a specific module
response = maintainer.run("Please analyze the data model design in the app/models/ directory")
"""
🤖 Assistant: I reviewed the app/models/ directory and found the following data models:

1. User (user.py)
   - Fields: id, username, email, password_hash, created_at
   - Relationships: One-to-many Order
   - Issue: ⚠️ Missing index, email field not set with unique constraint

2. Product (product.py)
   - Fields: id, name, description, price, stock
   - Issue: ✅ Well designed

3. Order (order.py)
   - Fields: id, user_id, product_id, quantity, status
   - Issue: ⚠️ Missing creation time field, not conducive to data analysis

Recommendations:
1. Add unique constraint to User.email
2. Add created_at and updated_at fields to Order
3. Consider adding soft delete support

I have recorded these issues as blocker notes.
"""
# [Automatically created blocker note]


# ========== Day 2: Analyze Code Quality ==========

# 1. Overall quality analysis
response = maintainer.analyze()
"""
📊 Analyzing code quality...
🤖 Thinking...

🤖 Assistant: Code quality analysis report:

📊 Code statistics:
- Total lines: 3,542 lines
- Average file length: approximately 150 lines
- Largest file: services/order_service.py (456 lines)

⚠️ Issues found:

1. Code duplication (HIGH):
   - user_service.py and product_service.py have similar CRUD logic
   - Recommendation: Extract base class BaseService

2. Excessive complexity (MEDIUM):
   - order_service.py::process_order method has 8 levels of nesting
   - Recommendation: Split into multiple small methods

3. Lack of tests (HIGH):
   - Test coverage only 45%
   - services/ directory has no tests at all

4. TODO/FIXME (12 items):
   - Most are "optimize later" type comments
   - Recommendation: Clean up or convert to formal tasks

I have recorded these issues as notes and marked priorities.
"""
# [Automatically created multiple blocker notes]

# 2. View specific issue
response = maintainer.run("Please review the process_order method in order_service.py and provide refactoring recommendations")
"""
🤖 Assistant: I reviewed the code of the process_order method:

【Original Code】
def process_order(self, order_id):
    order = Order.query.get(order_id)
    if order:
        if order.status == 'pending':
            product = Product.query.get(order.product_id)
            if product:
                if product.stock >= order.quantity:
                    # ... 8 levels of nesting continue ...

【Problem Analysis】
1. Deep nesting leads to poor readability
2. Lack of error handling
3. Business logic mixed with data access

【Refactoring Recommendations】
def process_order(self, order_id):
    # 1. Early return pattern, reduce nesting
    order = self._get_order(order_id)
    if not order or order.status != 'pending':
        return False

    # 2. Extract methods, single responsibility
    if not self._check_stock(order):
        return False

    # 3. Use transactions to ensure consistency
    with db.transaction():
        self._update_stock(order)
        self._update_order_status(order, 'processing')

    return True

【Next Steps】
1. I have created a refactoring plan note
2. Recommend writing test cases first
3. Refactor gradually, keeping functionality unchanged
"""
# [Automatically created action note]


# ========== Day 3: Plan Refactoring Tasks ==========

# 1. Review progress
response = maintainer.plan_next_steps()
"""
📋 Loading task planning...
🤖 Thinking...

🤖 Assistant: Based on the exploration and analysis from the past two days, I have organized refactoring task priorities:

🔴 High priority (complete this week):
1. [blocker] Add unique constraint to User.email
   - Risk: Low, just database migration
   - Effort: 1 hour

2. [blocker] Extract BaseService to reduce code duplication
   - Risk: Medium, affects multiple service classes
   - Effort: Half a day

3. [blocker] Refactor process_order method
   - Risk: High, core business logic
   - Effort: 1 day (including writing tests)

🟡 Medium priority (next week):
4. Add unit tests for services/
5. Clean up TODO comments
6. Add time fields to Order

🟢 Low priority (TBD):
7. Performance optimization
8. Documentation updates

Recommendations:
- This week, first resolve data model issues (tasks 1, 6)
- Next week, conduct code refactoring (tasks 2, 3)
- Continuously increase test coverage (task 4)

I have updated task status notes, you can check progress anytime.
"""

# 2. Manually create detailed refactoring plan
maintainer.create_note(
    title="Weekly Refactoring Plan - Week 1",
    content="""## Objectives
Complete optimization of data model layer

## Task Checklist
- [ ] Add unique constraint to User.email
- [ ] Add created_at, updated_at fields to Order
- [ ] Write database migration scripts
- [ ] Update related test cases

## Schedule
- Monday: Design migration scripts
- Tuesday-Wednesday: Execute migration and test
- Thursday: Update test cases
- Friday: Code Review

## Risks
- Database migration may affect production environment, needs to be executed during off-peak hours
- Existing data may have duplicate emails, need to clean up first
""",
    note_type="task_state",
    tags=["refactoring", "week1", "high_priority"]
)

print("✅ Created detailed refactoring plan")


# ========== One Week Later: Check Progress ==========

# View note summary
summary = maintainer.note_tool.run({"action": "summary"})
print("📊 Note summary:")
print(json.dumps(summary, indent=2, ensure_ascii=False))
"""
{
  "total_notes": 8,
  "type_distribution": {
    "blocker": 3,
    "action": 2,
    "task_state": 2,
    "conclusion": 1
  },
  "recent_notes": [
    {
      "id": "note_20250119_160000_7",
      "title": "Weekly Refactoring Plan - Week 1",
      "type": "task_state",
      "updated_at": "2025-01-19T16:00:00"
    },
    ...
  ]
}
"""

# Generate complete report
report = maintainer.generate_report()
print("\n📄 Session report:")
print(json.dumps(report, indent=2, ensure_ascii=False))
"""
{
  "session_info": {
    "session_id": "session_20250119_150000",
    "project": "my_flask_app",
    "duration_seconds": 172800  # 2 days
  },
  "activity": {
    "commands_executed": 24,
    "notes_created": 8,
    "issues_found": 3
  },
  "notes": { ... }
}
"""
```

### 9.6.5 Анализ влияния бега

Благодаря этому полному тематическому исследованию мы можем увидеть несколько ключевых характеристик долгосрочных агентов. Во-первых, это межсессионная согласованность: агент поддерживает согласованность задач на протяжении нескольких дней и сеансов с помощью NoteTool. Проблемы, исследованные в первый день, автоматически учитываются в ходе анализа второго дня, планирование третьего дня может синтезировать все открытия, сделанные за предыдущие два дня, а полная история сохраняется при проверке неделю спустя. Во-вторых, это интеллектуальное управление контекстом: ContextBuilder обеспечивает высококачественный контекст для каждого разговора, автоматически собирая соответствующие заметки (особенно типы блокировщиков), динамически корректируя стратегии предварительной обработки в зависимости от режима разговора и выбирая наиболее релевантную информацию в рамках бюджета токена.

Третьей характеристикой является мгновенный доступ к файловой системе: TerminalTool поддерживает гибкое исследование кода без необходимости предварительной индексации всей кодовой базы, может мгновенно просматривать содержимое определенного файла и поддерживает сложную обработку текста (grep, awk и т. д.). В-четвертых, это автоматизированное управление знаниями: система автоматически управляет обнаруженными знаниями, автоматически создавая блокирующие заметки при обнаружении проблем, автоматически создавая заметки о действиях при обсуждении планов и автоматически сохраняя ключевую информацию в системе памяти. Наконец, это сотрудничество человека и машины — эта система поддерживает гибкие режимы сотрудничества человека и машины, в которых агенты могут автоматически выполнять исследование и анализ, люди могут вмешиваться и направлять систему заметок, а также поддерживает ручное создание подробных заметок по планированию.

Эта базовая структура может быть дополнительно расширена, например, за счет интеграции RAGTool для создания векторных индексов для кодовых баз в сочетании с семантическим поиском, разделения на специализированные проводники, анализаторы и планировщики для реализации многоагентного сотрудничества, интеграции инструментов тестирования для автоматической проверки результатов рефакторинга, выполнения команд git через TerminalTool для отслеживания изменений кода или создания визуальных интерфейсов с использованием Gradio/Streamlit.

## 9.7 Краткое содержание главы

В этой главе мы глубоко изучили теоретические основы и инженерные практики контекстной инженерии:

### Теоретический уровень

1. **Суть контекстной инженерии**: Эволюция от «быстрой разработки» к «контекстной разработке», ядром которой является управление ограниченным бюджетом внимания.
2. **Разрушение контекста**: понимание снижения производительности, вызванное длинными контекстами, признание контекста дефицитным ресурсом.
3. **Три основные стратегии**: уплотнение, структурированное ведение заметок, субагентная архитектура.

### Инженерная практика

1. **ContextBuilder**: реализует конвейер GSSC, предоставляет унифицированный интерфейс управления контекстом.
2. **NoteTool**: гибридный формат Markdown+YAML, поддерживает структурированную долговременную память.
3. **TerminalTool**: безопасный инструмент командной строки, поддерживает мгновенный доступ к файловой системе.
4. **Агент дальнего горизонта**: объединяет три основных инструмента и создает помощник по межсессионному обслуживанию кодовой базы.

### Основные выводы

- **Многоуровневый дизайн**: мгновенный доступ (TerminalTool) + сессионная память (MemoryTool) + постоянные заметки (NoteTool).
- **Интеллектуальная фильтрация**: механизм оценки на основе релевантности и новизны.
- **Безопасность прежде всего**: многоуровневые механизмы безопасности обеспечивают стабильность системы.
- **Взаимодействие человека и машины**: баланс между автоматизацией и управляемостью

Изучая эту главу, вы не только освоили основные технологии контекстной инженерии, но, что более важно, поняли, как создавать агентные системы, способные поддерживать согласованность и эффективность в течение длительных периодов времени. Эти навыки станут важной основой для создания приложений-агентов производственного уровня.

В следующей главе мы изучим протоколы связи агентов и узнаем, как дать возможность агентам более широко взаимодействовать с внешним миром.

## Упражнения

> **Примечание**. Для некоторых упражнений нет стандартных ответов. Основное внимание уделяется развитию у учащихся всестороннего понимания и практических способностей в области контекстной инженерии и управления долгосрочными задачами.

1. В этой главе была представлена ​​разница между контекстной инженерией и оперативной разработкой. Пожалуйста, проанализируйте:

   - В разделе 9.1 упоминается, что «контекст следует рассматривать как ограниченный ресурс с уменьшающейся предельной отдачей». Объясните, пожалуйста, что такое феномен «гниения контекста»? Почему нам по-прежнему необходимо тщательно управлять контекстом, даже если модели поддерживают контекстные окна размером 100 или даже 200 КБ?
   - Предположим, вы хотите создать «помощник по проверке кода», которому необходимо проанализировать базу кода, содержащую 50 файлов. Сравните две стратегии: (1) Одновременная загрузка всего содержимого файла в контекст; (2) Используйте контекст JIT (точно в срок), получая файлы по требованию с помощью инструментов. Проанализируйте преимущества, недостатки и применимые сценарии каждого из них.
   - В разделе 9.2.1 упоминались две крайние опасности системных подсказок: «чрезмерное кодирование» и «слишком расплывчатое кодирование». Пожалуйста, приведите практический пример каждого из них и объясните, как найти правильный баланс.

2. Конвейер GSSC (Gather-Select-Structure-Compress) является основной технологией этой главы. Пожалуйста, подумайте хорошенько:

> **Примечание**: это практический вопрос, рекомендуется использовать в реальных условиях.

   - В реализации ContextBuilder, описанной в разделе 9.3, каждый из четырех этапов имеет разные обязанности. Пожалуйста, проанализируйте: если на определенном этапе произойдет сбой (например, на этапе выбора выбрана ненужная информация или на этапе сжатия произойдет чрезмерное сжатие, приводящее к потере информации), какое влияние это окажет на конечную производительность агента?
   - На основе кода из раздела 9.3.4 добавьте в ContextBuilder функцию «оценки качества контекста»: после каждой сборки контекста автоматически оценивайте плотность информации, релевантность и полноту контекста и предоставляйте предложения по оптимизации.
   - На этапе «сжатия» в конвейере GSSC для интеллектуального суммирования используется LLM. Пожалуйста, подумайте: при каких обстоятельствах простые стратегии усечения или скользящего окна могут быть более подходящими, чем обобщение LLM? Разработайте гибридную стратегию сжатия, сочетающую в себе преимущества нескольких методов сжатия.

3. NoteTool и TerminalTool — ключевые инструменты, поддерживающие долгосрочные задачи. На основании разделов 9.4 и 9.5 выполните следующие действия по расширению:

> **Примечание**: это практический вопрос, рекомендуется использовать в реальных условиях.

   - NoteTool использует иерархическую систему заметок (заметки по проекту, заметки по задачам, временные заметки). Пожалуйста, разработайте механизм «автоматической организации заметок»: когда временные заметки накапливаются до определенного количества, агент может автоматически анализировать эти заметки, добавлять важную информацию в заметки к задачам или заметкам по проекту и очищать избыточный контент.
   - TerminalTool предоставляет возможности работы с файловой системой, но в разделе 9.5.2 особое внимание уделяется обеспечению безопасности. Пожалуйста, проанализируйте: достаточны ли текущие механизмы безопасности (проверка пути, белый список команд, проверка разрешений)? Если агенту необходимо получить доступ к конфиденциальным файлам или выполнить опасные операции, как следует разработать процесс «совместного утверждения человека и машины»?
   - Объединив NoteTool и TerminalTool, создайте «интеллектуального помощника по рефакторингу кода»: он может анализировать структуру кодовой базы, записывать планы рефакторинга, выполнять операции рефакторинга шаг за шагом, а также отслеживать прогресс и возникающие проблемы в заметках. Нарисуйте, пожалуйста, полную схему рабочего процесса.

4. В случае «управления долгосрочными задачами» в разделе 9.6 мы увидели ценность контекстной инженерии в практических приложениях. Пожалуйста, проанализируйте внимательно:

   - В корпусе используется стратегия «многоуровневого управления контекстом»: мгновенный доступ (TerminalTool) + сессионная память (MemoryTool) + постоянные заметки (NoteTool). Пожалуйста, проанализируйте: как должны координироваться эти три слоя? Какую информацию следует разместить в каком слое? Как избежать избыточности и противоречивости информации?
   - Предположим, во время выполнения задачи происходит прерывание (например, сбой системы, отключение сети), агенту необходимо восстановить состояние по заметкам и продолжить выполнение. Пожалуйста, разработайте механизм «возобновления с точки останова»: как записать достаточную информацию о состоянии в примечаниях? Как проверить правильность восстановленного состояния?
   - Задачи с длительным горизонтом часто предполагают параллельное или последовательное выполнение нескольких подзадач. Разработайте систему «управления зависимостями задач»: можно выражать отношения зависимости между задачами (например, «Задача B должна быть выполнена после завершения задачи A») и автоматически планировать порядок выполнения задач. Как эта система должна интегрироваться с NoteTool?

5. В этой главе неоднократно упоминалась концепция «постепенного раскрытия информации». Пожалуйста, подумайте:

   - В разделе 9.2.2 постепенное раскрытие описывается как «каждый шаг взаимодействия создает новый контекст, который, в свою очередь, определяет следующее решение». Пожалуйста, разработайте конкретный сценарий применения (например, написание научных работ, отладка сложных проблем), демонстрирующий, как постепенное раскрытие информации помогает агентам более эффективно выполнять задачи.
   - Потенциальным риском постепенного раскрытия информации является «неэффективное исследование»: агент может тратить время на неважные детали или упускать ключевую информацию. Пожалуйста, разработайте механизм «руководства по исследованию»: с помощью эвристических правил или метакогнитивных стратегий помогите агенту принимать более разумные решения о том, «что исследовать дальше».
   - Сравните «прогрессивное раскрытие» с традиционным «загружать весь контекст сразу»: в каких типах задач первое имеет очевидные преимущества? В каких типах задач последний может быть более уместным? Приведите не менее 3 примеров различных типов задач.

## Ссылки

[1] Антропная. Эффективная контекстная инженерия для ИИ-агентов.`https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents`

[2] Дэвид Ким. Контекстная инженерия (GitHub).`https://github.com/davidkimai/Context-Engineering`

