# Глава 13. Умный помощник путешественника

В предыдущих главах мы создали платформу HelloAgents с нуля, реализовав основные функции, включая различные парадигмы агентов, системы инструментов, механизмы памяти, связь по протоколам и оценку производительности. Начиная с этой главы, мы вступаем в совершенно новую фазу: **интеграцию всех полученных знаний для создания полноценных практических приложений.**

Помните первого агента, которого мы создали в главе 1? Это был простой интеллектуальный помощник в путешествии, демонстрирующий основные принципы работы`Thought-Action-Observation`петля. Интеллектуальный помощник в путешествиях, описанный в этой главе, представляет собой полноценный проект, включающий следующие основные функции:

**(1) Интеллектуальное планирование маршрута**: пользователи вводят пункт назначения, даты, предпочтения и другую информацию, и система автоматически генерирует полный план маршрута, включая достопримечательности, рестораны и отели.

**(2) Визуализация карты**: отмечайте места достопримечательностей на карте и рисуйте маршруты экскурсий, чтобы сделать маршрут понятным с первого взгляда.

**(3) Расчет бюджета**: автоматически рассчитывайте расходы на билеты, проживание, питание и транспорт, отображая подробную информацию о бюджете.

**(4) Редактирование маршрута**: поддержка добавления, удаления и настройки достопримечательностей, обновление карты в режиме реального времени.

**(5) Функция экспорта**: поддержка экспорта в формате PDF или изображения, удобная для сохранения и обмена.

## 13.1 Обзор проекта и архитектурный дизайн

### 13.1.1 Why We Need an Intelligent Travel Assistant

Планирование поездки – это одновременно волнительно и неприятно. Вам нужно искать информацию о достопримечательностях в Интернете, сравнивать различные путеводители, проверять прогнозы погоды, бронировать отели, рассчитывать бюджет и планировать маршруты. Этот процесс может занять несколько часов или даже дней. И даже потратив столько времени, вы не уверены, разумен ли запланированный маршрут, пропустили ли вы какие-либо важные достопримечательности и верен ли бюджет.

Традиционные методы планирования путешествий имеют несколько болевых точек. Во-первых, это **разрозненная информация**. Информация о достопримечательностях находится на туристических веб-сайтах, информация о погоде — на веб-сайтах погоды, информация об отелях — на веб-сайтах бронирования — вам необходимо переключаться между несколькими веб-сайтами и вручную интегрировать эту информацию. Во-вторых, **отсутствие персонализации**. Большинство путеводителей носят общий характер и не учитывают ваши личные предпочтения, бюджетные ограничения, время в пути и другие факторы. Наконец, **трудность регулировки**. Если вы захотите изменить маршрут, вам, возможно, придется перепланировать всю поездку, поскольку порядок достопримечательностей, расписание и бюджет взаимосвязаны.

Технология искусственного интеллекта открывает новые возможности для решения этих проблем. Представьте, что вам нужно всего лишь сказать системе: «Я хочу посетить Пекин на 3 дня, например, история и культура, средний бюджет», и система может автоматически сгенерировать для вас полный план маршрута, в том числе, какие достопримечательности посещать каждый день, где поесть, в каком отеле остановиться и какой бюджет необходим. Причем этот план настраиваемый — вы можете удалить не понравившиеся достопримечательности, скорректировать порядок туров, а система автоматически обновит карту и бюджет.

Это интеллектуальный помощник в путешествиях, который мы хотим создать. Это не просто техническая демонстрация, а действительно полезное приложение. Благодаря этому проекту вы узнаете, как применять технологию искусственного интеллекта для решения практических задач, как проектировать многоагентные системы и как создавать полноценные веб-приложения.

### 13.1.2 Обзор технической архитектуры

В системе используется классическая **архитектура разделения клиентской и внутренней частей**, разделенная на четыре уровня, как показано на рисунке 13.1:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/13-figures/13-1.png" alt="" width="85%"/>
  <p>Рисунок 13.1 Техническая архитектура Intelligent Travel Assistant</p>
</div>

**(1) Интерфейсный уровень (Vue3+TypeScript)**: отвечает за взаимодействие с пользователем и отображение данных, включая ввод формы, отображение результатов и визуализацию карты.

**(2) Внутренний уровень (FastAPI)**: отвечает за маршрутизацию API, проверку данных и бизнес-логику.

**(3) Уровень агента (HelloAgents)**: отвечает за декомпозицию задач, вызов инструментов и интеграцию результатов. Включает в себя 4 специализированных агента.

**(4) Уровень внешнего сервиса**: предоставляет данные и возможности, включая Amap API, Unsplash API и LLM API.

Процесс потока данных выглядит следующим образом: Пользователь заполняет форму на внешнем интерфейсе → Серверная часть проверяет данные → Вызывает агентскую систему → Агенты последовательно вызывают поиск достопримечательностей, запрос погоды, рекомендации отелей, планирование маршрута. Агенты → Каждый агент вызывает внешние API через протокол MCP → Интегрирует результаты и возвращается на внешний интерфейс → Внешний интерфейс визуализирует и отображает.

Ссылка на структуру проекта приведена ниже и предназначена для облегчения поиска исходного кода:
```
helloagents-trip-planner/
├── backend/                    # Backend code
│   ├── app/
│   │   ├── agents/            # Agent implementation
│   │   ├── api/               # API routes
│   │   ├── models/            # Data models
│   │   ├── services/          # Service layer
│   │   └── config.py          # Configuration file
│   └── requirements.txt       # Python dependencies
│
└── frontend/                   # Frontend code
    ├── src/
    │   ├── views/             # Page components
    │   ├── services/          # API services
    │   ├── types/             # Type definitions
    │   └── router/            # Route configuration
    └── package.json           # npm dependencies
```

Подробное проектирование архитектуры и потока данных будет представлено в последующих разделах.

### 13.1.3 Быстрый опыт: запуск проекта за 5 минут

Прежде чем углубляться в детали реализации, давайте сначала запустим проект, чтобы увидеть конечный эффект. Таким образом, вы получите интуитивное понимание всей системы.

**Требования к среде:**

- Питон 3.10 или выше
- Node.js 16.0 или выше
- НПМ 8.0 или выше

**Получить ключи API:**

Вам необходимо подготовить следующие ключи API:

- LLM API (OpenAI, DeepSeek и т. д.)
- Ключ веб-службы Amap: посетите https://console.amap.com/, чтобы зарегистрироваться и создать приложение.
- Ключ доступа к Unsplash: посетите https://unsplash.com/developers, чтобы зарегистрироваться и создать приложение.

Поместите все ключи API в`.env`файл.

Запустите бэкэнд:

```bash
# 1. Enter backend directory
cd helloagents-trip-planner/backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env file, fill in your API keys

# 4. Start backend service
uvicorn app.api.main:app --reload
# or
python run.py
```

После успешного запуска посетитеhttp://localhost:8000/docsчтобы просмотреть документацию API.

Откройте новое окно терминала:

```bash
# 1. Enter frontend directory
cd helloagents-trip-planner/frontend

# 2. Install dependencies
npm install

# 3. Start frontend service
npm run dev
```

После успешного запуска посетитеhttp://localhost:5173использовать приложение.

Испытайте основные функции:

Сначала заполните город назначения, даты поездки, предпочтения, бюджет, транспорт и типы размещения в форме на главной странице. После нажатия кнопки «Начать планирование» система отобразит индикатор выполнения загрузки и быстро создаст страницу результатов, как показано на рисунке 13.2.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/13-figures/13-2.png" alt="" width="85%"/>
  <p>Рисунок 13.2 Страница хода выполнения планирования помощника по командировкам</p>
</div>

После успешной загрузки на странице будет четко отображаться обзор маршрута, сведения о бюджете, карта достопримечательностей, сведения о ежедневном маршруте и информация о погоде, как показано на рисунках 13.3 и 13.4.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/13-figures/13-3.png" alt="" width="85%"/>
  <p>Рисунок 13.3 Страница завершения планирования Travel Assistant</p>
</div>

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/13-figures/13-4.png" alt="" width="85%"/>
  <p>Рисунок 13.4 Страница завершения планирования Travel Assistant</p>
</div>

Если пользователям необходимы персональные настройки, они могут нажать кнопку «Редактировать маршрут», чтобы свободно изменить порядок достопримечательностей или удалить определенные достопримечательности, как показано на рисунке 13.5. После завершения планирования с помощью раскрывающегося меню «Экспорт маршрута» окончательный план можно легко сохранить в виде изображения или файла PDF для удобного использования в любое время.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/13-figures/13-5.png" alt="" width="85%"/>
  <p>Рисунок 13.5 Страница завершения планирования Travel Assistant</p>
</div>

## 13.2 Проектирование модели данных

### 13.2.1 Поток данных в веб-приложениях

При создании интеллектуального помощника по путешествиям нам необходимо решить основную проблему: **Как представлять и передавать данные плана путешествия?**

Нам необходимо понять, как передаются данные в законченном веб-приложении. Представьте, что происходит, когда пользователь нажимает кнопку «Начать планирование» в браузере?

Данные формы, заполненные пользователем на внешнем интерфейсе (пункт назначения, даты, бюджет и т. д.), необходимо отправить на внутренний сервер посредством HTTP-запросов. После того как серверная часть получит данные, она вызовет систему агента для обработки. Затем агенты будут вызывать внешние службы, такие как Amap API и Unsplash API, для получения данных. Форматы данных, возвращаемые этими внешними API, различны. Некоторые используют`lng`, некоторое использование`lon`, и некоторые используют`longitude`. Наконец, серверная часть должна вернуть обработанные данные во внешний интерфейс, который затем отображает их на странице, которую видит пользователь.

В этом процессе данные претерпевают несколько преобразований: внешняя форма → HTTP-запрос → внутренний объект Python → ответ внешнего API → внутренний объект Python → ответ HTTP → внешний объект TypeScript → отображение страницы. Без единого формата данных каждый шаг преобразования может пойти не так. Вот почему нам нужны **модели данных**.

### 13.2.2 От словарей к пидантическим моделям

Начнем с простого прототипа из главы 1. В этом прототипе мы использовали словари Python для представления данных о привлекательности:

```python
# Chapter 1 approach: using dictionaries
attraction = {
    "name": "Forbidden City",
    "location": {"lng": 116.397128, "lat": 39.916527},
    "price": 60
}

# Access data
lng = attraction["location"]["lng"]
```

Этот подход удобен на стадии прототипа, но в реальных проектах может возникнуть множество проблем. Во-первых, это проблема **несовместимых имен полей**. Данные о местоположении, возвращаемые Amap API, представляют собой строку типа`"116.397128,39.916527"`, который необходимо вручную разделить на долготу и широту. Unsplash API может использовать`longitude`и`latitude`. Если мы используем словари повсюду в коде, нам нужно учитывать эти различия в каждом месте.

Во-вторых, это проблема **типовой безопасности**. Предположим, мы случайно установили`price`как строка`"60"`, это не приведет к немедленной ошибке в Python, но вызовет проблемы при расчете общего бюджета. Хуже того, ошибки такого рода можно обнаружить только во время выполнения, и найти сообщение об ошибке может быть сложно.

Наконец, проблема **ремонтопригодности**. Когда нам нужно добавить новое поле к достопримечательностям (например,`rating`), нам нужно изменить несколько мест в коде. Если мы где-то пропустим, это приведет к несогласованности данных.

Pydantic предлагает решение. Это библиотека проверки данных Python, которая позволяет нам определять структуры данных с помощью классов и автоматически выполнять проверку, преобразование и сериализацию. Давайте посмотрим на простой пример:

```python
from pydantic import BaseModel, Field

class Location(BaseModel):
    longitude: float = Field(..., description="Longitude")
    latitude: float = Field(..., description="Latitude")

class Attraction(BaseModel):
    name: str
    location: Location
    ticket_price: int = 0

# Create object
attraction = Attraction(
    name="Forbidden City",
    location=Location(longitude=116.397128, latitude=39.916527),
    ticket_price=60
)

# Type-safe access
lng = attraction.location.longitude  # IDE will provide code completion
```

Этот подход имеет несколько преимуществ. Во-первых, если мы передадим неправильный тип (например, установив`ticket_price`в виде строки), Pydantic немедленно выдаст исключение, сообщающее нам, где находится ошибка. Во-вторых, IDE может обеспечить завершение кода и проверку типов на основе определений типов, что значительно снижает количество ошибок в написании. Наконец, когда нам нужно изменить структуру данных, нам нужно изменить только определение класса, и все места, использующие этот класс, автоматически обновятся.

### 13.2.3 Основные понятия Pydantic

Прежде чем углубиться в разработку моделей данных, давайте сначала разберемся с несколькими основными концепциями Pydantic. В основе Pydantic лежит`BaseModel`класс, и все модели данных должны наследовать от этого класса. В каждом поле можно указать тип, и Pydantic автоматически выполнит проверку и преобразование типов.

Field definition uses the`Field`function, which can specify default values, descriptions, validation rules, etc.`...`indicates that this field is required - if this field is not provided when creating an object, Pydantic will throw an exception. We can also use`Optional`для указания необязательных полей или непосредственного указания значений по умолчанию.

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class Attraction(BaseModel):
    name: str = Field(..., description="Attraction name")  # Required
    rating: float = Field(default=0.0, ge=0, le=5)  # Default value, range validation
    visit_duration: int = Field(default=60, gt=0)  # Greater than 0
    description: Optional[str] = None  # Optional field
```

Pydantic также поддерживает вложенные модели и списки. Мы можем использовать другую модель в качестве типа поля в одной модели, что позволит нам создавать сложные структуры данных. Например, достопримечательность содержит информацию о местоположении, а маршрут содержит несколько достопримечательностей.

```python
class DayPlan(BaseModel):
    date: str
    attractions: List[Attraction]  # Attraction list
    hotel: Optional[Hotel] = None  # Optional hotel information
```

Одна из самых мощных функций — **настраиваемые валидаторы**. Иногда формат данных, возвращаемый внешними API, не соответствует нашим требованиям, и мы можем использовать`field_validator`декоратор для настройки логики проверки и преобразования. Например, температура, возвращаемая Amap, представляет собой строку вида`"16°C"`, и нам нужно преобразовать его в число:

```python
from pydantic import field_validator

class WeatherInfo(BaseModel):
    temperature: int

    @field_validator('temperature', mode='before')
    def parse_temperature(cls, v):
        """Parse temperature string: "16°C" -> 16"""
        if isinstance(v, str):
            v = v.replace('°C', '').replace('℃', '').strip()
            return int(v)
        return v
```

Этот валидатор автоматически выполнится перед созданием объекта, преобразуя строку в целое число. Таким образом, нам не нужно вручную обрабатывать формат температуры в каждом месте кода.

### 13.2.4 Разработка модели снизу вверх

Теперь давайте приступим к разработке моделей данных для интеллектуального помощника в путешествии. Хороший принцип проектирования — **снизу вверх**: сначала определите самые базовые модели, а затем постепенно объединяйте их в сложные структуры. Преимущество этого подхода в том, что каждая модель проста, легка для понимания и обслуживания.

Самая базовая модель — **информация о местоположении**. Будь то достопримечательности, отели или рестораны, всем нужна информация о местоположении. Мы определяем`Location`класс для представления координат долготы и широты:

```python
class Location(BaseModel):
    """Location information (longitude and latitude coordinates)"""
    longitude: float = Field(..., description="Longitude", ge=-180, le=180)
    latitude: float = Field(..., description="Latitude", ge=-90, le=90)
```

Здесь мы используем проверку диапазона (`ge`означает больше или равно,`le`означает меньше или равно), чтобы гарантировать, что значения долготы и широты находятся в разумных пределах.

Далее идет **информация о достопримечательностях**. Аттракцион содержит название, адрес, местоположение, продолжительность посещения, описание, рейтинг, изображение и информацию о цене билета. Обратите внимание, что мы используем`Location`как тип поля, который представляет собой вложенную модель:

```python
class Attraction(BaseModel):
    """Attraction information"""
    name: str = Field(..., description="Attraction name")
    address: str = Field(..., description="Address")
    location: Location = Field(..., description="Longitude and latitude coordinates")
    visit_duration: int = Field(..., description="Recommended visit duration (minutes)", gt=0)
    description: str = Field(..., description="Attraction description")
    category: Optional[str] = Field(default="Attraction", description="Attraction category")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="Rating")
    image_url: Optional[str] = Field(default=None, description="Image URL")
    ticket_price: int = Field(default=0, ge=0, description="Ticket price (yuan)")
```

Аналогичным образом мы определяем **информацию о питании** и **информацию об отеле**. Эти модели имеют схожую структуру и все содержат базовую информацию, такую ​​как имя, адрес, местоположение и стоимость:

```python
class Meal(BaseModel):
    """Meal information"""
    type: str = Field(..., description="Meal type: breakfast/lunch/dinner/snack")
    name: str = Field(..., description="Meal name")
    address: Optional[str] = Field(default=None, description="Address")
    location: Optional[Location] = Field(default=None, description="Longitude and latitude coordinates")
    description: Optional[str] = Field(default=None, description="Description")
    estimated_cost: int = Field(default=0, description="Estimated cost (yuan)")

class Hotel(BaseModel):
    """Hotel information"""
    name: str = Field(..., description="Hotel name")
    address: str = Field(default="", description="Hotel address")
    location: Optional[Location] = Field(default=None, description="Hotel location")
    price_range: str = Field(default="", description="Price range")
    rating: str = Field(default="", description="Rating")
    distance: str = Field(default="", description="Distance to attractions")
    type: str = Field(default="", description="Hotel type")
    estimated_cost: int = Field(default=0, description="Estimated cost (yuan/night)")
```

**Информация о бюджете** – это специальная модель, которая не содержит информации о местоположении, но содержит сводку различных расходов:

```python
class Budget(BaseModel):
    """Budget information"""
    total_attractions: int = Field(default=0, description="Total attraction ticket cost")
    total_hotels: int = Field(default=0, description="Total hotel cost")
    total_meals: int = Field(default=0, description="Total meal cost")
    total_transportation: int = Field(default=0, description="Total transportation cost")
    total: int = Field(default=0, description="Total cost")
```

Теперь мы можем объединить эти базовые модели и построить **ежедневный маршрут**. Ежедневный маршрут содержит дату, описание, способ транспортировки, способ размещения, отель, список достопримечательностей и список питания:

```python
class DayPlan(BaseModel):
    """Daily itinerary"""
    date: str = Field(..., description="Date")
    day_index: int = Field(..., description="Day number (starting from 0)")
    description: str = Field(..., description="Daily itinerary description")
    transportation: str = Field(..., description="Transportation method")
    accommodation: str = Field(..., description="Accommodation arrangement")
    hotel: Optional[Hotel] = Field(default=None, description="Hotel information")
    attractions: List[Attraction] = Field(default_factory=list, description="Attraction list")
    meals: List[Meal] = Field(default_factory=list, description="Meal arrangements")
```

Обратите внимание, что мы используем`List[Attraction]`представлять список достопримечательностей, и`default_factory=list`означает, что значение по умолчанию — пустой список.

**Информация о погоде** требует особого обращения, поскольку формат температуры, возвращаемый Amap, нестандартен. Для этого мы используем собственный валидатор:

```python
class WeatherInfo(BaseModel):
    """Weather information"""
    date: str = Field(..., description="Date")
    day_weather: str = Field(..., description="Daytime weather")
    night_weather: str = Field(..., description="Nighttime weather")
    day_temp: int = Field(..., description="Daytime temperature (Celsius)")
    night_temp: int = Field(..., description="Nighttime temperature (Celsius)")
    wind_direction: str = Field(..., description="Wind direction")
    wind_power: str = Field(..., description="Wind power")

    @field_validator('day_temp', 'night_temp', mode='before')
    def parse_temperature(cls, v):
        """Parse temperature string: "16°C" -> 16"""
        if isinstance(v, str):
            v = v.replace('°C', '').replace('℃', '').replace('°', '').strip()
            try:
                return int(v)
            except ValueError:
                return 0  # Error tolerance
        return v
```

Наконец, мы определяем **полный план путешествия**. Это модель верхнего уровня, содержащая всю информацию:

```python
class TripPlan(BaseModel):
    """Travel plan"""
    city: str = Field(..., description="Destination city")
    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    days: List[DayPlan] = Field(default_factory=list, description="Daily itinerary")
    weather_info: List[WeatherInfo] = Field(default_factory=list, description="Weather information")
    overall_suggestions: str = Field(..., description="Overall suggestions")
    budget: Optional[Budget] = Field(default=None, description="Budget information")
```

Таким образом, мы завершили разработку всей модели данных. Из самого основного`Location`, к`Attraction`, `Meal`, `Hotel`, затем`DayPlan`и, наконец,`TripPlan`, образуя четкую иерархическую структуру.

### 13.2.5 Применение моделей данных в веб-приложениях

Теперь давайте посмотрим, как эти модели данных используются в реальных веб-приложениях. В FastAPI модели Pydantic можно напрямую использовать в качестве определений типов для запросов и ответов. FastAPI автоматически выполнит проверку данных, сериализацию и создание документации.

```python
from fastapi import FastAPI
from app.models.schemas import TripPlanRequest, TripPlan

app = FastAPI()

@app.post("/api/trip/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest) -> TripPlan:
    """
    Create travel plan

    FastAPI automatically:
    1. Validates request data (TripPlanRequest)
    2. Validates response data (TripPlan)
    3. Generates OpenAPI documentation
    """
    trip_plan = await generate_trip_plan(request)
    return trip_plan
```

Когда пользователь отправляет POST-запрос на`/api/trip/plan`, FastAPI автоматически преобразует данные JSON в`TripPlanRequest`объект. Если формат данных неверен (например, отсутствуют обязательные поля или несоответствие типов), FastAPI автоматически вернет ошибку 400 и сообщит пользователю, где находится ошибка.

Во внешнем интерфейсе нам также необходимо определить соответствующие типы TypeScript. Хотя TypeScript и Python — разные языки, структуры данных одинаковы:

```typescript
interface Location {
  longitude: number;
  latitude: number;
}

interface Attraction {
  name: string;
  address: string;
  location: Location;
  visit_duration: number;
  ticket_price: number;
}

interface TripPlan {
  city: string;
  start_date: string;
  end_date: string;
  days: DayPlan[];
}
```

Таким образом, интерфейсная и серверная части используют единый формат данных. Когда серверная часть возвращает`TripPlan`объект, интерфейсная часть может использовать его напрямую без какого-либо преобразования. Проверка типов TypeScript также может помочь нам избежать многих ошибок.

## 13.3 Проектирование многоагентного сотрудничества

### 13.3.1 Зачем нам нужен мультиагент

В главе 7 мы узнали, как создавать агенты с помощью SimpleAgent. Философия дизайна SimpleAgent проста и понятна: каждый раз, когда`run()`вызывается метод, Агент анализирует вопрос пользователя, решает, следует ли вызывать инструменты, а затем возвращает результат. Такая конструкция очень эффективна при решении простых задач, но при решении таких задач, как планирование поездки, возникают некоторые проблемы.

Если для планирования поездки мы используем одного агента, что должен делать этот агент? Во-первых, ему необходимо найти информацию о достопримечательностях, для чего необходимо вызвать инструмент поиска POI компании Amap. Затем ему необходимо запросить информацию о погоде, для чего необходимо вызвать инструмент запроса погоды. Далее ему необходимо найти информацию об отеле, что снова требует вызова инструмента поиска POI. Наконец, необходимо интегрировать всю эту информацию для создания полного плана поездки.

Звучит просто, но в реальной работе возникает первая проблема: **ограничения вызова инструментов**. SimpleAgent может запускать только один инструмент за раз.`run()`вызов. Это означает, что нам нужно вызвать`run()`метод несколько раз, при этом каждый вызов обрабатывает одну задачу. Но это порождает новую проблему: как передавать информацию между несколькими вызовами? Как передать информацию о привлекательности, полученную при первом вызове, на второй вызов? Нам приходится вручную управлять этими промежуточными результатами, и код становится очень сложным.

Конечно, мы можем использовать ReactAgent для решения этой проблемы. ReactAgent может запускать несколько инструментов за один вызов и автоматически выполнять несколько этапов обдумывания и действия. Но это приносит новые проблемы: **затраты времени**. Каждый раунд размышлений ReactAgent требует вызова LLM. Если нужно вызвать три инструмента, необходимо как минимум три раунда размышления, что означает как минимум три вызова LLM. Причем эти вызовы последовательные — следующий может начаться только после завершения предыдущего, поэтому общее время будет очень большим.

Вторая проблема — **быстрая сложность**. Если мы хотим, чтобы один Агент выполнял все задачи, нам необходимо в командной строке подробно описать логику выполнения каждой задачи. Например:

```python
COMPLEX_PROMPT = """You are a travel planning assistant. You need to:
1. Use maps_text_search to search for attractions, keywords determined by user preferences
2. Use maps_weather to query weather, get weather forecast for the next few days
3. Use maps_text_search to search for hotels, type determined by user needs
4. Integrate all information to generate travel plan, including daily attractions, dining, accommodation arrangements
Note: Must execute in order, each tool can only be called once, output must be in JSON format...
"""
```

У такого рода подсказок есть несколько проблем. Во-первых, **сложно поддерживать**. Если мы хотим изменить логику поиска достопримечательностей (например, добавить фильтрацию рейтингов), нам нужно изменить всю подсказку, что может легко повлиять на другие части. Во-вторых, **склонен к ошибкам**. LLM должен понимать требования нескольких задач одновременно, и он может легко перепутать форматы и параметры разных задач. Наконец, **сложно отлаживать**. Когда сгенерированный план не соответствует ожиданиям, трудно понять, что пошло не так: неточный ли поиск достопримечательностей, не удалось выполнить запрос погоды или возникла проблема с логикой интеграции?

Столкнувшись с этими проблемами, возникает естественная идея: можем ли мы разложить сложные задачи на несколько простых задач и позволить каждому агенту выполнять свою работу? Это основная идея многоагентного сотрудничества.

Представьте себе туристическое агентство в реальном мире. Когда вы идете в туристическое агентство, чтобы проконсультироваться по поводу плана путешествия, вас не будет обслуживать один человек. Обычно за рекомендации достопримечательностей отвечает специальный консультант по достопримечательностям; гостиничный консультант, отвечающий за бронирование отелей; и планировщик маршрута, ответственный за интеграцию всей информации в полный маршрут. Каждый человек сосредотачивается на своей области знаний, и, наконец, планировщик маршрута обобщает всю информацию. Такое разделение труда и сотрудничество гораздо эффективнее, чем когда все делает один человек.

### 13.3.2 Проектирование ролей агента

Основываясь на принципе декомпозиции задач, мы разработали четыре специализированных Агента, как показано на рисунке 13.6:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/13-figures/13-6.png" alt="" width="85%"/>
  <p>Рисунок 13.6. Схема многоагентной совместной работы</p>
</div>

- **AttractionSearchAgent (Эксперт по поиску достопримечательностей)** фокусируется на поиске информации о достопримечательностях. Ему нужно только понять предпочтения пользователя (например, «история и культура», «природные пейзажи»), а затем вызвать инструмент поиска POI Amap и вернуть список связанных достопримечательностей. Его подсказка очень проста: нужно только объяснить, как выбирать ключевые слова на основе предпочтений и как вызывать инструменты.

- **WeatherQueryAgent (Эксперт запросов погоды)** предназначен для запроса информации о погоде. Ему нужно только знать название города, затем вызвать инструмент запроса погоды и вернуть прогноз погоды на следующие несколько дней. Его задача очень ясна и практически безошибочна.

- **HotelAgent (Эксперт по рекомендациям отелей)** фокусируется на поиске информации об отелях. Ему необходимо понять потребности пользователей в размещении (например, «бюджет», «роскошь»), а затем вызвать инструмент поиска POI и вернуть список отелей, соответствующих требованиям.

- **PlannerAgent (Эксперт по планированию маршрутов)** отвечает за интеграцию всей информации. Он получает выходные данные от первых трех агентов, а также исходные требования пользователя (даты, бюджет и т. д.), а затем генерирует полный план поездки. Ему не нужно вызывать какие-либо внешние инструменты, достаточно сосредоточиться на интеграции информации и составлении маршрута.

Теперь давайте детально продумаем роль и приглашение для каждого Агента. При разработке подсказок нам необходимо рассмотреть несколько ключевых вопросов: Какие входные данные нужны этому агенту? Какую продукцию он должен производить? Какие инструменты ему нужно вызвать? С какими проблемами он может столкнуться?

Задача **AttractionSearchAgent** — поиск достопримечательностей на основе предпочтений пользователя. Вводимыми данными являются название города и предпочтения пользователя (например, «история и культура», «природные пейзажи»). Для этого необходимо вызвать`amap_maps_text_search`инструмент с параметрами, являющимися ключевыми словами и городом. Его выходные данные представляют собой список достопримечательностей, включая название, адрес, рейтинг и другую информацию.

```python
ATTRACTION_AGENT_PROMPT = """You are an attraction search expert.

**Tool Call Format:**
`[TOOL_CALL:amap_maps_text_search:keywords=attraction,city=city_name]`

**Examples:**
- `[TOOL_CALL:amap_maps_text_search:keywords=attraction,city=Beijing]`
- `[TOOL_CALL:amap_maps_text_search:keywords=museum,city=Shanghai]`

**Important:**
- Must use tools to search, don't fabricate information
- Search for attractions in {city} based on user preferences ({preferences})
"""
```

Это приглашение является кратким, но содержит всю необходимую информацию. В нем четко объясняется формат вызова инструментов, приводятся конкретные примеры и подчеркиваются два важных принципа: необходимо использовать инструменты (невозможно изготовить) и поиск на основе предпочтений пользователя.

Задача **WeatherQueryAgent** проще: нужно только запросить погоду. На входе — название города, а на выходе — информация о погоде.

```python
WEATHER_AGENT_PROMPT = """You are a weather query expert.

**Tool Call Format:**
`[TOOL_CALL:amap_maps_weather:city=city_name]`

Please query weather information for {city}.
"""
```

Задача **HotelAgent** — поиск отелей. На входе — название города и тип проживания, а на выходе — список отелей.

```python
HOTEL_AGENT_PROMPT = """You are a hotel recommendation expert.

**Tool Call Format:**
`[TOOL_CALL:amap_maps_text_search:keywords=hotel,city=city_name]`

Please search for {accommodation} hotels in {city}.
"""
```

**PlannerAgent** — самый сложный, поскольку ему необходимо интегрировать всю информацию. Его входные данные — это требования пользователя и выходные данные первых трех агентов, а выходные данные — полный план поездки (формат JSON).

```python
PLANNER_AGENT_PROMPT = """You are an itinerary planning expert.

**Output Format:**
Strictly return in the following JSON format:
{
  "city": "city name",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [...],
  "weather_info": [...],
  "overall_suggestions": "overall suggestions",
  "budget": {...}
}

**Planning Requirements:**
1. weather_info must include weather for each day
2. Temperature as pure numbers (without °C)
3. Arrange 2-3 attractions per day
4. Consider attraction distance and visit time
5. Include breakfast, lunch, and dinner
6. Provide practical suggestions
7. Include budget information
"""
```

### 13.3.3 Agent Collaboration Flow

Теперь давайте посмотрим, как эти четыре агента сотрудничают при выполнении задачи планирования поездки. Весь процесс можно разделить на пять этапов:

```python
class TripPlannerAgent:
    def __init__(self):
        self.attraction_agent = SimpleAgent(name="Attraction Search", prompt=ATTRACTION_PROMPT)
        self.weather_agent = SimpleAgent(name="Weather Query", prompt=WEATHER_PROMPT)
        self.hotel_agent = SimpleAgent(name="Hotel Recommendation", prompt=HOTEL_PROMPT)
        self.planner_agent = SimpleAgent(name="Itinerary Planning", prompt=PLANNER_PROMPT)

    def plan_trip(self, request: TripPlanRequest) -> TripPlan:
        # Step 1: Attraction search
        attraction_response = self.attraction_agent.run(
            f"Please search for {request.preferences} attractions in {request.city}"
        )

        # Step 2: Weather query
        weather_response = self.weather_agent.run(
            f"Please query weather for {request.city}"
        )

        # Step 3: Hotel recommendation
        hotel_response = self.hotel_agent.run(
            f"Please search for {request.accommodation} hotels in {request.city}"
        )

        # Step 4: Integrate and generate plan
        planner_query = self._build_planner_query(
            request, attraction_response, weather_response, hotel_response
        )
        planner_response = self.planner_agent.run(planner_query)

        # Step 5: Parse JSON
        trip_plan = self._parse_trip_plan(planner_response)
        return trip_plan
```

Этот поток последовательно выполняет четыре шага, при этом выходные данные каждого шага служат входными данными для следующего шага. Обратите внимание, что мы используем`TripPlanRequest`и`TripPlan`Пидантические модели, определенные в разделе 13.2.

### 13.3.4 Создание запроса

PlannerAgent необходимо интегрировать всю информацию. Этот запрос должен включать всю необходимую информацию и быть организован четко и упорядоченно, чтобы LLM мог точно понять его.

```python
def _build_planner_query(
    self,
    request: TripPlanRequest,
    attraction_response: str,
    weather_response: str,
    hotel_response: str
) -> str:
    """Build query for planning Agent"""
    return f"""
Please generate a {request.days}-day travel plan for {request.city} based on the following information:

**User Requirements:**
- Destination: {request.city}
- Dates: {request.start_date} to {request.end_date}
- Days: {request.days} days
- Preferences: {request.preferences}
- Budget: {request.budget}
- Transportation: {request.transportation}
- Accommodation: {request.accommodation}

**Attraction Information:**
{attraction_response}

**Weather Information:**
{weather_response}

**Hotel Information:**
{hotel_response}

Please generate a detailed travel plan, including daily attraction arrangements, dining recommendations, accommodation information, and budget details.
"""
```

Благодаря этой схеме совместной работы нескольких агентов мы разбиваем сложную задачу планирования поездки на четыре простых подзадачи. Каждый агент фокусируется на своей области знаний, а также закладывает хорошую основу для будущего расширения функций (например, добавление агента по рекомендации ресторанов, агента по планированию транспорта).

## 13.4 Детали интеграции инструмента MCP

### 13.4.1 Почему бы не вызывать API напрямую

В разделе 13.3 мы разработали четырех агентов для совместной работы над задачей планирования поездки. Среди них AttractionSearchAgent, WeatherQueryAgent и HotelAgent необходимо вызывать API Amap для получения данных. Естественный вопрос: почему бы не вызвать HTTP API Amap непосредственно в Агенте?

Давайте сначала посмотрим, как будет выглядеть прямой вызов API. Amap предоставляет API поиска POI, и нам нужно создавать HTTP-запросы, передавать параметры и анализировать ответы:

```python
import requests

def search_poi(keywords: str, city: str, api_key: str):
    """Directly call Amap POI search API"""
    url = "https://restapi.amap.com/v3/place/text"
    params = {
        "keywords": keywords,
        "city": city,
        "key": api_key,
        "output": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data
```

Этот подход выглядит простым, но при реальном использовании он сталкивается с рядом проблем. Во-первых, **Агент не может звонить автономно**. В нашей среде HelloAgents агенты вызывают инструменты, распознавая маркеры вызова инструментов в подсказках (например,`[TOOL_CALL:tool_name:arg1=value1]`). Если мы вызываем API непосредственно в коде, Агент теряет способность автономного принятия решений и становится простым вызовом функции.

Во-вторых, **сложная передача параметров**. API Amap имеет множество параметров. Например, поиск POI имеет более десятка параметров, таких как`keywords`, `city`, `types`, `offset`, `page`и т. д. Если мы хотим, чтобы Агент гибко использовал эти параметры, нам необходимо подробно объяснить в подсказке значение и формат каждого параметра, что сделает подсказку очень сложной.

В-третьих, **сложный анализ ответов**. Данные, возвращаемые Amap API, имеют формат JSON и имеют относительно сложную структуру. Нам нужно написать код для анализа этих данных и извлечения нужных нам полей. Если формат ответа API изменится, нам необходимо изменить код синтаксического анализа.

Наконец, **хаотичное управление инструментами**. Amap предоставляет более десятка различных API (поиск POI, запрос погоды, планирование маршрута и т. д.). Если мы напишем функцию для каждого API, а затем вручную зарегистрируем ее в списке инструментов Агента, код станет очень длинным. И когда мы хотим добавить новый API, нам нужно изменить несколько мест.

### 13.4.2 Интеграция Amap MCP

MCP (Model Context Protocol) — это стандартизированный протокол, предложенный Anthropic для подключения LLM и внешних инструментов. В этом разделе рассказывается, как интегрировать сервер Amap MCP в проект. В нашем проекте используется`amap-mcp-server`, который представляет собой сервер MCP, реализованный в Node.js:

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/13-figures/13-7.png" alt="" width="85%"/>
  <p>Рис. 13.7 Инструменты amap-mcp-server</p>
</div>

Сервер Amap MCP предоставляет различные инструменты, в основном разделенные на следующие категории, как показано в Таблице 13.1:

<div align="center">
  <p>Таблица 13.1 Категории инструментов Amap MCP</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/13-figures/13-table-1.png" alt="" width="85%"/>
</div>

Через протокол MCP мы можем легко интегрироваться в HelloAgents:

```python
from hello_agents.tools import MCPTool
from app.config import get_settings

settings = get_settings()

# Create MCP tool
mcp_tool = MCPTool(
    name="amap_mcp",
    command="npx",
    args=["-y", "@sugarforever/amap-mcp-server"],
    env={"AMAP_API_KEY": settings.amap_api_key},
    auto_expand=True
)
```

Что делает этот код? Первый,`command`и`args`укажите, как запустить MCP-сервер.`npx -y @sugarforever/amap-mcp-server`скачаем и запустим`amap-mcp-server`пакет из репозитория npm.`env`Параметр передает переменные среды, здесь мы передаем ключ API Amap.

**Примечание.** В некоторых примерах этого документа используется`npx`для запуска служб MCP (Model Context Protocol). Однако в репозитории кода, соответствующем этому разделу контента, мы фактически используем`uvx`. Важно отметить, что`npx`и`uvx`имеют почти одинаковые принципы проектирования — единственная разница заключается в их экосистемах:`npx`нацелен на JavaScript/Node.js (пакеты из npm), а`uvx`нацелен на Python (пакеты из PyPI). Между этими двумя методами нет превосходства или неполноценности. Пожалуйста, выбирайте в соответствии с вашими потребностями при их использовании.

Когда мы создаем`MCPTool`объект, он запустит процесс сервера MCP в фоновом режиме и будет взаимодействовать с сервером через стандартный ввод/вывод (stdin/stdout). Это особенность протокола MCP: использование межпроцессного взаимодействия вместо HTTP, что более эффективно и проще в управлении.

Наиболее критичным параметром является`auto_expand=True`. Если установлено значение True,`MCPTool`автоматически запросит, какие инструменты предоставляет сервер MCP, а затем создаст независимый объект Tool для каждого инструмента. Вот почему мы создали только один`MCPTool`, но Агенту досталось 16 инструментов. Давайте посмотрим на этот процесс:

```python
# Create one MCPTool
mcp_tool = MCPTool(..., auto_expand=True)
agent.add_tool(mcp_tool)

# Agent actually gets 16 tools!
print(list(agent.tools.keys()))
# ['amap_maps_text_search', 'amap_maps_weather', ...]
```

Предположим, что, как показано на рис. 13.8, пользователь хочет найти достопримечательности Пекина. AttractionSearchAgent получает запрос «Пожалуйста, найдите исторические и культурные достопримечательности в Пекине». Агент анализирует этот запрос и решает вызвать`amap_maps_text_search`инструмент с параметрами`keywords=attraction, city=Beijing`.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/13-figures/13-8.png" alt="" width="85%"/>
  <p>Рисунок 13.8. Процесс вызова инструмента MCP</p>
</div>

Агент генерирует маркер вызова инструмента:`[TOOL_CALL:amap_maps_text_search:keywords=attraction,city=Beijing]`. Платформа HelloAgents анализирует этот маркер, извлекает имя и параметры инструмента, а затем вызывает соответствующий объект Tool.

Объект Tool автоматически создается`MCPTool`, и он отправит запрос на вызов на сервер MCP. В частности, он создаст сообщение формата JSON-RPC и отправит его серверному процессу через стандартный ввод:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "amap_maps_text_search",
    "arguments": {
      "keywords": "attraction",
      "city": "Beijing"
    }
  }
}
```

Сервер MCP получает это сообщение, анализирует параметры, а затем вызывает HTTP API Amap. Он создаст HTTP-запрос, добавит ключ API, отправит запрос и получит ответ.

Amap API возвращает данные в формате JSON, содержащие список достопримечательностей, адрес, координаты и другую информацию. Сервер MCP анализирует эти данные, извлекает ключевые поля, а затем формирует ответное сообщение, возвращая его в`MCPTool`через стандартный вывод:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found the following attractions:\n1. Forbidden City Museum - Address: No. 4 Jingshan Front Street, Dongcheng District\n2. Temple of Heaven Park - Address: Tiantan Road, Dongcheng District\n..."
      }
    ]
  }
}
```

`MCPTool`получает ответ, извлекает текстовое содержимое и возвращает его Агенту. Агент использует этот результат как выходные данные вызова инструмента и продолжает генерировать окончательный ответ.

Этот процесс выглядит сложным, но Агенту достаточно знать, что существует инструмент под названием`amap_maps_text_search`который может искать достопримечательности. Все основные детали инкапсулированы протоколом MCP и`MCPTool`.

### 13.4.3 Совместное использование экземпляров MCP

В нашей мультиагентной системе три агента должны использовать инструменты Amap. Так должен ли каждый Агент создавать свои собственные`MCPTool`экземпляр или использовать один и тот же экземпляр?

Если каждый агент создает`MCPTool`Например, это означает, что три серверных процесса будут выполняться одновременно. Каждый процесс будет независимо вызывать API Amap, что может превышать ограничение скорости API. Более того, несколько процессов будут занимать больше памяти и ресурсов ЦП.

Лучший подход — позволить всем агентам использовать один и тот же`MCPTool`пример. Таким образом, необходимо запустить только один процесс сервера MCP, и все вызовы API проходят через этот процесс. Это не только экономит ресурсы, но и позволяет лучше контролировать частоту вызовов API.

В коде мы создаем`MCPTool`экземпляр в конструкторе`TripPlannerAgent`, а затем добавьте его в список инструментов каждого субагента:

```python
class TripPlannerAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = HelloAgentsLLM()

        # Create shared MCP tool instance (create only once)
        self.mcp_tool = MCPTool(
            name="amap_mcp",
            command="npx",
            args=["-y", "@sugarforever/amap-mcp-server"],
            env={"AMAP_API_KEY": settings.amap_api_key},
            auto_expand=True
        )

        # Create multiple Agents, sharing the same MCP tool
        self.attraction_agent = SimpleAgent(
            name="AttractionSearchAgent",
            llm=self.llm,
            system_prompt=ATTRACTION_AGENT_PROMPT
        )
        self.attraction_agent.add_tool(self.mcp_tool)  # Share

        self.weather_agent = SimpleAgent(
            name="WeatherQueryAgent",
            llm=self.llm,
            system_prompt=WEATHER_AGENT_PROMPT
        )
        self.weather_agent.add_tool(self.mcp_tool)  # Share

        self.hotel_agent = SimpleAgent(
            name="HotelAgent",
            llm=self.llm,
            system_prompt=HOTEL_AGENT_PROMPT
        )
        self.hotel_agent.add_tool(self.mcp_tool)  # Share
```

Таким образом, все три агента могут использовать 16 инструментов Amap, но под ним работает только один серверный процесс MCP. Когда мы вызываем`plan_trip`метод`TripPlannerAgent`, три агента будут последовательно вызывать инструменты, и все запросы отправляются в API Amap через один и тот же сервер MCP.

### 13.4.4 Интеграция API изображений Unsplash

Помимо Amap, нам также необходимо получить изображения достопримечательностей, чтобы сделать план путешествия более ярким и интуитивно понятным. Мы используем Unsplash API для поиска изображений достопримечательностей. Обратите внимание, что Unsplash — это зарубежный сервис и один из немногих API изображений, которые можно использовать бесплатно, поэтому результаты поиска могут быть недостаточно точными. В реальных проектах вы можете рассмотреть возможность использования API изображений POI Bing, Baidu или Amap, но эти услуги обычно требуют оплаты.

Интеграция Unsplash API относительно проста. Мы создаем`UnsplashService`класс для инкапсуляции вызовов API:

```python
# backend/app/services/unsplash_service.py
import requests
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class UnsplashService:
    """Unsplash image service"""

    def __init__(self, access_key: str):
        self.access_key = access_key
        self.base_url = "https://api.unsplash.com"

    def search_photos(self, query: str, per_page: int = 10) -> List[Dict]:
        """Search for images"""
        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "per_page": per_page,
                "client_id": self.access_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            # Extract image URLs
            photos = []
            for result in results:
                photos.append({
                    "url": result["urls"]["regular"],
                    "description": result.get("description", ""),
                    "photographer": result["user"]["name"]
                })

            return photos

        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return []

    def get_photo_url(self, query: str) -> Optional[str]:
        """Get single image URL"""
        photos = self.search_photos(query, per_page=1)
        return photos[0].get("url") if photos else None
```

Этот класс обслуживания предоставляет два метода:`search_photos`ищет несколько изображений и`get_photo_url`получает URL-адрес одного изображения. Мы используем этот сервис в маршруте API для получения изображений для каждого аттракциона:

```python
# backend/app/api/routes/trip.py
from app.services.unsplash_service import UnsplashService

unsplash_service = UnsplashService(settings.unsplash_access_key)

@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest) -> TripPlan:
    # Generate travel plan
    trip_plan = trip_planner_agent.plan_trip(request)

    # Get images for each attraction
    for day in trip_plan.days:
        for attraction in day.attractions:
            if not attraction.image_url:
                image_url = unsplash_service.get_photo_url(
                    f"{attraction.name} {trip_plan.city}"
                )
                attraction.image_url = image_url

    return trip_plan
```

Обратите внимание, что мы не инкапсулировали Unsplash как инструмент или инструмент MCP, а вызвали его непосредственно в маршруте API. Это связано с тем, что поиск изображений не требует интеллектуального принятия решений Агентом, это всего лишь простой шаг по улучшению данных. Если вы хотите, чтобы агент самостоятельно решал, нужны ли изображения, или выбирал разные источники изображений, вы можете рассмотреть возможность его инкапсуляции в качестве инструмента.

## 13.5 Детали внешней разработки

### 13.5.1 Веб-архитектура разделения клиентской и внутренней частей

Прежде чем приступить к разработке внешнего интерфейса, нам необходимо понять структуру архитектуры современных веб-приложений. На ранних этапах веб-разработки интерфейсная и серверная части были смешаны. Например, в таких технологиях, как PHP и JSP, HTML-шаблоны и код бизнес-логики были записаны в одном файле. Этот подход удобен в небольших проектах, но сталкивается со многими проблемами в крупных проектах: разработчикам внешнего и внутреннего интерфейса требуется частая координация, код сложно повторно использовать, а тестирование затруднено.

Современные веб-приложения обычно используют **архитектуру разделения клиентской и внутренней части**. Серверная часть отвечает только за предоставление интерфейсов API и возврат данных в формате JSON. Интерфейс — это независимое приложение, которое вызывает внутренние API через HTTP-запросы, получает данные и затем отображает страницы. Эта архитектура имеет несколько очевидных преимуществ: интерфейсную и серверную части можно разрабатывать, развертывать и тестировать независимо друг от друга; интерфейсным интерфейсом может быть веб-приложение, мобильное приложение или настольное приложение, использующее один и тот же набор внутренних API; интерфейсная часть может использовать современные платформы и цепочки инструментов для обеспечения лучшего взаимодействия с пользователем.

В нашем проекте интеллектуального помощника по путешествиям серверная часть реализована с помощью Python и FastAPI, обеспечивая основной интерфейс API.`POST /api/trip/plan`который получает требования к поездкам и возвращает планы поездок. Интерфейс реализован с помощью Vue 3 и TypeScript и представляет собой одностраничное приложение (SPA). Пользователи заполняют формы в браузере, нажимают кнопку «Начать планирование», внешний интерфейс отправляет HTTP-запрос на серверную часть, ждет ответа, а затем отображает страницу результатов. На протяжении всего этого процесса страница не обновляется, и работа пользователя очень плавная.

При выборе стека интерфейсных технологий необходимо учитывать несколько факторов: эффективность разработки, производительность, экосистему и кривую обучения. Как показано в Таблице 13.2, в проекте был выбран следующий стек технологий:

<div align="center">
  <p>Таблица 13.2. Стек интерфейсных технологий</p>
  <img src="https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/13-figures/13-table-2.png" alt="" width="85%"/>
</div>

Структура каталогов проекта следующая:

```
frontend/
├── src/
│   ├── views/              # Page components
│   │   ├── Home.vue        # Home page (form)
│   │   └── Result.vue      # Result page
│   ├── services/           # API services
│   │   └── api.ts
│   ├── types/              # Type definitions
│   │   └── index.ts
│   ├── router/             # Router configuration
│   │   └── index.ts
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
└── tsconfig.json
```

The`views`каталог хранит компоненты страницы,`services`в каталоге хранится логика вызовов API,`types`В каталоге хранятся определения типов TypeScript, а`router`В каталоге хранится конфигурация маршрутизатора.

### 13.5.2 Определения типов

В разделе 13.2 мы использовали Pydantic для определения моделей данных на серверной стороне, таких как`Location`, `Attraction`, `DayPlan`, `TripPlan`и т. д. Во внешнем интерфейсе нам необходимо определить соответствующие типы TypeScript.

Давайте посмотрим, как определить эти типы. Сначала самое основное`Location`тип, представляющий координаты долготы и широты:

```typescript
// frontend/src/types/index.ts
export interface Location {
  longitude: number
  latitude: number
}
```

Это определение типа в точности соответствует внутренней модели Pydantic. Обратите внимание, что TypeScript использует`interface`Ключевое слово для определения типов, типы полей разделяются двоеточиями, значения по умолчанию не требуются.

Далее идет`Attraction`тип, представляющий информацию о достопримечательности:

```typescript
export interface Attraction {
  name: string
  address: string
  location: Location
  visit_duration: number
  description: string
  category?: string
  rating?: number
  image_url?: string
  ticket_price?: number
}
```

Обратите внимание, что мы используем`Location`введите здесь тип поля, который является вложенным типом. Вопросительный знак`?`указывает на необязательное поле, соответствующее`Optional`во внутренней модели Pydantic.

Аналогичным образом мы определяем такие типы, как`Meal`, `Hotel`, `Budget`, `WeatherInfo`и т. д. Наконец, верхний уровень`TripPlan`тип:

```typescript
export interface TripPlan {
  city: string
  start_date: string
  end_date: string
  days: DayPlan[]
  weather_info: WeatherInfo[]
  overall_suggestions: string
  budget?: Budget
}
```

Также есть тип запроса`TripPlanRequest`, соответствующий модели внутреннего запроса:

```typescript
export interface TripPlanRequest {
  city: string
  start_date: string
  end_date: string
  days: number
  preferences: string
  budget: string
  transportation: string
  accommodation: string
}
```

Для чего нужны эти определения типов? Во-первых, когда мы вызываем API, TypeScript проверит, соответствуют ли передаваемые нами данные`TripPlanRequest`тип. Если мы случайно напишем`days`в виде строки TypeScript немедленно сообщит об ошибке. Во-вторых, когда мы получим ответ API, TypeScript проверит, соответствуют ли данные ответа`TripPlan`тип. Если структура данных серверной части изменится, интерфейсная часть немедленно обнаружит это. Наконец, IDE может обеспечить завершение кода на основе определений типов. Когда мы печатаем`tripPlan.`, IDE автоматически выведет список всех доступных полей.

### 13.5.3 Инкапсуляция службы API

С помощью определений типов мы можем инкапсулировать вызовы API. Мы создаем`api.ts`файл и используйте Axios для отправки HTTP-запросов:

```typescript
import axios from 'axios'
import type { TripPlanRequest, TripPlan } from '../types'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 120000, // 2-minute timeout
  headers: {
    'Content-Type': 'application/json'
  }
})
```

Здесь мы создаем экземпляр Axios и настраиваем базовый URL-адрес, тайм-аут и заголовки запросов. Почему таймаут установлен на 2 минуты? Поскольку для создания плана поездки требуется вызов нескольких агентов, каждому агенту необходимо вызвать LLM и внешние API, и весь процесс может занять 10–30 секунд. Если таймаут слишком мал, запрос будет прерван.

Далее мы добавляем перехватчики. Перехватчики могут выполнять некоторую общую логику перед отправкой запросов и после получения ответов, например ведение журнала, обработку ошибок, аутентификацию и т. д.:

```typescript
// Request interceptor
api.interceptors.request.use(
  config => {
    console.log('Sending request:', config)
    return config
  },
  error => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  response => {
    console.log('Received response:', response)
    return response
  },
  error => {
    console.error('Request failed:', error)
    return Promise.reject(error)
  }
)
```

Наконец, мы определяем функцию API, которая является единственной точкой входа для внешнего интерфейса для вызова внутреннего интерфейса:

```typescript
// Generate travel plan
export const generateTripPlan = async (request: TripPlanRequest): Promise<TripPlan> => {
  const response = await api.post<TripPlan>('/trip/plan', request)
  return response.data
}
```

Обратите внимание на сигнатуру типа этой функции: параметр имеет тип`TripPlanRequest`, а возвращаемое значение имеет тип`Promise<TripPlan>`. Это означает, что TypeScript проверит, соответствуют ли параметры, переданные вызывающей стороной, требованиям, а также проверит правильность использования возвращаемого значения.

### 13.5.4 Дизайн домашней формы

Домашняя страница — это точка входа пользователя, содержащая форму, в которой пользователи могут заполнить требования к поездке. Мы используем Composition API Vue 3 для организации кода:

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateTripPlan } from '@/services/api'
import type { TripPlanRequest } from '@/types'

const router = useRouter()
const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

const formData = ref<TripPlanRequest>({
  city: '',
  start_date: '',
  end_date: '',
  days: 3,
  preferences: 'History and Culture',
  budget: 'Medium',
  transportation: 'Public Transportation',
  accommodation: 'Budget Hotel'
})
</script>
```

Здесь мы используем`ref`для создания реактивных переменных.`formData`это данные формы типа`TripPlanRequest`. `loading`указывает, загружается ли он,`loadingProgress`указывает ход загрузки, и`loadingStatus`указывает текст состояния загрузки.

Логика отправки формы следующая:

```typescript
const handleSubmit = async () => {
  loading.value = true
  loadingProgress.value = 0

  // Simulate progress updates
  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += 10
      if (loadingProgress.value <= 30) loadingStatus.value = '🔍 Searching for attractions...'
      else if (loadingProgress.value <= 50) loadingStatus.value = '🌤️ Querying weather...'
      else if (loadingProgress.value <= 70) loadingStatus.value = '🏨 Recommending hotels...'
      else loadingStatus.value = '📋 Generating itinerary...'
    }
  }, 500)

  try {
    const response = await generateTripPlan(formData.value)
    clearInterval(progressInterval)
    loadingProgress.value = 100
    router.push({ name: 'result', state: { tripPlan: response } })
  } catch (error) {
    clearInterval(progressInterval)
    message.error('Failed to generate plan, please try again')
  } finally {
    loading.value = false
  }
}
```

Этот код делает несколько вещей. Во-первых, он устанавливает`loading`значение true, чтобы отобразить состояние загрузки. Затем он запускает таймер, который обновляет индикатор выполнения и текст состояния каждые 500 миллисекунд. Это смоделированный прогресс, поскольку мы не можем точно знать ход обработки серверной части. Но это позволяет пользователям знать, что система работает, а не зависает.

Далее он вызывает`generateTripPlan`функция для отправки запроса API. Это асинхронная операция, и мы используем`await`дождаться ответа. Если запрос успешен, очистите таймер, установите прогресс на 100 %, затем перейдите на страницу результатов и передайте данные плана поездки. Если запрос не выполнен, отобразите сообщение об ошибке. Наконец, независимо от того, успешно это или нет, установите`loading`значение false, чтобы скрыть состояние загрузки.

Часть шаблона использует компоненты Ant Design Vue:

```vue
<template>
  <div class="home-container">
    <div class="page-header">
      <h1 class="page-title">✈️ Intelligent Travel Assistant</h1>
      <p class="page-subtitle">AI-Powered Personalized Travel Planning</p>
    </div>

    <a-card class="form-card">
      <a-form :model="formData" @finish="handleSubmit">
        <a-form-item label="Destination City" name="city" :rules="[{ required: true }]">
          <a-input v-model:value="formData.city" placeholder="e.g., Beijing" />
        </a-form-item>

        <!-- More form items... -->

        <a-form-item>
          <a-button type="primary" html-type="submit" size="large" :loading="loading">
            Start Planning
          </a-button>
        </a-form-item>

        <!-- Loading progress bar -->
        <a-form-item v-if="loading">
          <a-progress :percent="loadingProgress" status="active" />
          <p>{{ loadingStatus }}</p>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>
```

Обратите внимание на`v-model:value`директива, реализующая двустороннюю привязку данных. Когда пользователи вводят в поле ввода,`formData.city`автоматически обновляется. Когда значение`formData.city`изменяется, содержимое поля ввода также автоматически обновляется.

### 13.5.5 Отображение страницы результатов

Страница результатов является ядром всего приложения и отображает созданный план поездки. Эта страница состоит из нескольких частей: обзор маршрута, сведения о бюджете, визуализация карты, сведения о ежедневном маршруте и информация о погоде.

Во-первых, это визуализация карты. Мы используем Amap JS API, чтобы отмечать места достопримечательностей на карте:

```typescript
import AMapLoader from '@amap/amap-jsapi-loader'

const initMap = async () => {
  const AMap = await AMapLoader.load({
    key: 'your_amap_web_key',
    version: '2.0'
  })

  map = new AMap.Map('amap-container', {
    zoom: 12,
    center: [116.397128, 39.916527]
  })

  // Add attraction markers
  tripPlan.value.days.forEach((day) => {
    day.attractions.forEach((attraction, index) => {
      const marker = new AMap.Marker({
        position: [attraction.location.longitude, attraction.location.latitude],
        title: attraction.name,
        label: { content: `${index + 1}`, direction: 'top' }
      })
      map.add(marker)
    })
  })
}
```

Этот код сначала загружает Amap SDK, затем создает экземпляр карты и, наконец, перебирает все достопримечательности, создавая для каждой маркер. Положение маркера — это координаты долготы и широты достопримечательности, которые получаются из серверной части`Attraction`объект.

Функция экспорта использует`html2canvas`и`jsPDF`библиотеки.`html2canvas`можем преобразовать элементы DOM в Canvas, а затем экспортировать Canvas как изображение или PDF:

```typescript
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

// Export as image
const exportAsImage = async () => {
  const element = document.getElementById('trip-plan-content')
  const canvas = await html2canvas(element, { scale: 2 })
  const link = document.createElement('a')
  link.download = `${tripPlan.value.city} Travel Plan.png`
  link.href = canvas.toDataURL()
  link.click()
}

// Export as PDF
const exportAsPDF = async () => {
  const element = document.getElementById('trip-plan-content')
  const canvas = await html2canvas(element, { scale: 2 })
  const imgData = canvas.toDataURL('image/png')
  const pdf = new jsPDF('p', 'mm', 'a4')
  const imgWidth = 210
  const imgHeight = (canvas.height * imgWidth) / canvas.width
  pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight)
  pdf.save(`${tripPlan.value.city} Travel Plan.pdf`)
}
```

С помощью этих интерфейсных технологий мы реализовали полноценное веб-приложение. Пользователи могут заполнять формы в браузере, отправлять запросы, ждать, пока ИИ создаст планы поездок, затем просматривать подробные маршруты, видеть места достопримечательностей на карте и экспортировать их в виде изображений или PDF-файлов. Весь процесс плавный и естественный — в этом прелесть современных веб-приложений.

## 13.6 Детали реализации функции

В этом разделе представлены основные реализации интеллектуального помощника по путешествиям, включая расчет бюджета, индикатор выполнения загрузки, редактирование маршрута, функции экспорта и боковую навигацию.

### 13.6.1 Функция расчета бюджета

При планировании поездки бюджет является очень важным фактором. Пользователям необходимо примерно знать, сколько будет стоить такая поездка и куда пойдут деньги. Наш интеллектуальный помощник по путешествиям обеспечивает функцию автоматического расчета бюджета, разделяя расходы на четыре основные категории: билеты на аттракционы, проживание в отеле, питание и транспорт.

Где реализована логика расчета бюджета? Мы решили реализовать его в PlannerAgent серверной части. Почему бы не посчитать на фронтенде? Потому что оценка бюджета должна основываться на ценах на билеты на аттракционы, ценовых диапазонах отелей, стандартах питания и другой информации, которая уже получена PlannerAgent при создании маршрута. Если рассчитывать на внешнем интерфейсе, нам нужно будет продублировать эту логику, и она может быть неточной.

В приглашении PlannerAgent мы явно требуем, чтобы LLM генерировал информацию о бюджете:

```python
PLANNER_AGENT_PROMPT = """
You are an itinerary planning expert.

**Output Format:**
Strictly return in the following JSON format:
{
  ...
  "budget": {
    "total_attractions": 180,
    "total_hotels": 1200,
    "total_meals": 480,
    "total_transportation": 200,
    "total": 2060
  }
}

**Planning Requirements:**
...
7. Include budget information, estimate based on attraction tickets, hotel prices, dining standards, and transportation methods
"""
```

LLM оценит стоимость каждого предмета с учетом достопримечательностей, отелей и условий питания в маршруте. Например, если маршрут включает Запретный город (билет 60 юаней), Храм Неба (билет 15 юаней) и Летний дворец (билет 30 юаней), то общая стоимость билета на аттракцион составит 105 юаней. Если это поездка на 3 дня и 2 ночи с бюджетными отелями (300 юаней за ночь), то общая стоимость гостиницы составит 600 юаней.

На внешнем интерфейсе мы используем компонент статистики Ant Design Vue для отображения информации о бюджете. Этот компонент специально разработан для отображения статистических данных и поддерживает анимацию чисел, префиксы/суффиксы, пользовательские стили и т. д.:

```vue
<a-card v-if="tripPlan.budget" title="💰 Budget Details">
  <a-row :gutter="16">
    <a-col :span="6">
      <a-statistic title="Attraction Tickets" :value="tripPlan.budget.total_attractions" suffix="yuan" />
    </a-col>
    <a-col :span="6">
      <a-statistic title="Hotel Accommodation" :value="tripPlan.budget.total_hotels" suffix="yuan" />
    </a-col>
    <a-col :span="6">
      <a-statistic title="Dining Expenses" :value="tripPlan.budget.total_meals" suffix="yuan" />
    </a-col>
    <a-col :span="6">
      <a-statistic title="Transportation" :value="tripPlan.budget.total_transportation" suffix="yuan" />
    </a-col>
  </a-row>
  <a-divider />
  <a-row>
    <a-col :span="24" style="text-align: center;">
      <a-statistic
        title="Estimated Total Cost"
        :value="tripPlan.budget.total"
        suffix="yuan"
        :value-style="{ color: '#cf1322', fontSize: '32px', fontWeight: 'bold' }"
      />
    </a-col>
  </a-row>
</a-card>
```

Этот код использует макет сетки (`a-row`и`a-col`), чтобы отобразить четыре статьи расходов рядом. Для каждой статьи расходов используется`a-statistic`компонент для отображения заголовка и значения. Наконец, делитель (`a-divider`) разделяет их, а ниже для наглядности отображается общая стоимость крупным красным шрифтом.

Обратите внимание на условный рендеринг`v-if="tripPlan.budget"`. Поскольку информация о бюджете не является обязательной (определяется как`Optional[Budget]`в модели Pydantic), если LLM не генерирует информацию о бюджете, эта карточка не будет отображаться. Это отражает устойчивость внешнего интерфейса к ошибкам данных.

### 13.6.2 Индикатор выполнения загрузки

Составление плана путешествия — трудоемкая операция. Серверной части необходимо последовательно вызывать AttractionSearchAgent, WeatherQueryAgent, HotelAgent и PlannerAgent, и каждый агент должен вызывать LLM и внешние API. Весь процесс может занять 10-30 секунд. Если пользователь нажмет кнопку «Начать планирование», а на странице нет обратной связи, он подумает, что система зависла, и может обновить страницу или щелкнуть несколько раз.

Чтобы улучшить взаимодействие с пользователем, мы добавили индикатор выполнения загрузки и подсказки о состоянии. В настоящее время это просто симуляция прогресса, но она позволяет пользователям узнать, что система работает.

```typescript
const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

const handleSubmit = async () => {
  loading.value = true
  loadingProgress.value = 0

  // Simulate progress updates
  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += 10
      if (loadingProgress.value <= 30) loadingStatus.value = '🔍 Searching for attractions...'
      else if (loadingProgress.value <= 50) loadingStatus.value = '🌤️ Querying weather...'
      else if (loadingProgress.value <= 70) loadingStatus.value = '🏨 Recommending hotels...'
      else loadingStatus.value = '📋 Generating itinerary...'
    }
  }, 500)

  try {
    const response = await generateTripPlan(formData.value)
    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '✅ Complete!'
    router.push({ name: 'result', state: { tripPlan: response } })
  } catch (error) {
    clearInterval(progressInterval)
    message.error('Failed to generate plan')
  } finally {
    loading.value = false
  }
}
```

### 13.6.3 Функция редактирования маршрута

Хотя планы поездок, созданные с помощью ИИ, являются интеллектуальными, они могут не полностью отвечать личным потребностям пользователей. Например, пользователям может не понравиться определенная достопримечательность и они захотят удалить ее или изменить порядок достопримечательностей. Мы предоставляем функцию редактирования маршрута, которая позволяет пользователям настраивать свой маршрут.

Основой функции редактирования является **управление состоянием**. Нам необходимо поддерживать два состояния: текущий план маршрута и исходный план маршрута. Когда пользователи входят в режим редактирования, мы сохраняем копию исходного плана. Если пользователи отменяют редактирование, мы восстанавливаем исходный план. Если пользователи сохраняют изменения, мы обновляем текущий план:

```typescript
const editMode = ref(false)
const originalPlan = ref<TripPlan | null>(null)

// Enter edit mode
const toggleEditMode = () => {
  editMode.value = true
  originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
}
```

Обратите внимание, что мы используем`JSON.parse(JSON.stringify(...))`для глубокого копирования объекта. Почему бы не назначить напрямую? Поскольку объекты в JavaScript являются ссылочными типами, то если мы присваиваем их напрямую,`originalPlan`и`tripPlan`будет указывать на один и тот же объект, и изменение одного повлияет на другой. Глубокое копирование создает полностью независимую копию.

Логика перемещения аттракционов заключается в смене позиций двух элементов массива:

```typescript
// Move attraction
const moveAttraction = (dayIndex: number, attractionIndex: number, direction: 'up' | 'down') => {
  const attractions = tripPlan.value.days[dayIndex].attractions
  const newIndex = direction === 'up' ? attractionIndex - 1 : attractionIndex + 1

  if (newIndex >= 0 && newIndex < attractions.length) {
    [attractions[attractionIndex], attractions[newIndex]] =
    [attractions[newIndex], attractions[attractionIndex]]
  }
}
```

Здесь используется синтаксис деструктуризации присваивания ES6 для замены двух элементов.`[a, b] = [b, a]`— это элегантный способ обмена без использования временной переменной.

Удаление достопримечательностей использует массив`splice`метод:

```typescript
// Delete attraction
const deleteAttraction = (dayIndex: number, attractionIndex: number) => {
  tripPlan.value.days[dayIndex].attractions.splice(attractionIndex, 1)
}
```

При сохранении изменений нам необходимо повторно инициализировать карту, поскольку позиции достопримечательностей могли измениться:

```typescript
// Save changes
const saveChanges = () => {
  editMode.value = false
  message.success('Changes saved')
  initMap()  // Reinitialize map
}

// Cancel editing
const cancelEdit = () => {
  if (originalPlan.value) {
    tripPlan.value = originalPlan.value
  }
  editMode.value = false
}
```

В шаблоне мы отображаем разные пользовательские интерфейсы в зависимости от значения`editMode`. В режиме редактирования рядом с каждым аттракционом отображаются кнопки «вверх», «вниз» и «удалить»:

```vue
<div v-if="editMode" class="edit-buttons">
  <a-button size="small" @click="moveAttraction(dayIndex, index, 'up')">Up</a-button>
  <a-button size="small" @click="moveAttraction(dayIndex, index, 'down')">Down</a-button>
  <a-button size="small" danger @click="deleteAttraction(dayIndex, index)">Delete</a-button>
</div>
```

### 13.6.4 Функциональность экспорта

После того как пользователи составят удовлетворительный план путешествия, они могут захотеть сохранить его или поделиться им с друзьями. Мы предоставляем два метода экспорта: экспорт как изображение и экспорт в PDF.

Основой функции экспорта является`html2canvas`библиотека. Эта библиотека может конвертировать элементы DOM в Canvas, а затем мы можем экспортировать Canvas как изображение. Но здесь есть техническая проблема: карта отображается с использованием Canvas, и`html2canvas`имеет проблемы совместимости при работе с вложенным Canvas.

Мы попробовали несколько решений, включая преобразование Canvas карты в изображение перед экспортом, но из-за механизма рендеринга Canvas Amap и ограничений между источниками это решение не решило проблему полностью. В реальных проектах вам может потребоваться рассмотреть следующие альтернативные решения:

1. **Используйте API статических карт Amap**: вызовите инструмент «maps_staticmap», чтобы создать изображения статических карт для замены динамических карт.
2. **Экспортировать отдельно**: экспортируйте карту и содержимое маршрута отдельно, а затем объедините их на серверной стороне.
3. **Используйте службу снимков экрана**: используйте автономные браузеры, такие как Puppeteer, чтобы делать снимки экрана на стороне сервера.
4. **Упрощение экспорта контента**: скройте карту при экспорте, экспортируйте только текстовый контент.

В текущей реализации мы применили упрощенный подход, временно скрывая часть карты при экспорте и экспортируя только текстовое содержимое и информацию о достопримечательностях маршрута. Хотя это не идеальное решение, оно обеспечивает возможность использования функции экспорта.

Логика экспорта в виде изображения проста:

```typescript
import html2canvas from 'html2canvas'

const exportAsImage = async () => {
  const element = document.getElementById('trip-plan-content')
  if (!element) return

  const canvas = await html2canvas(element, {
    backgroundColor: '#ffffff',
    scale: 2,
    useCORS: true
  })

  const link = document.createElement('a')
  link.download = `${tripPlan.value.city} Travel Plan.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
  message.success('Export successful!')
}
```

`scale: 2`означает использование 2-кратного разрешения, что делает экспортированное изображение более четким.`useCORS: true`позволяет загружать изображения из разных источников, что важно для привлечения изображений (из Unsplash).

Экспорт в PDF требует дополнительных шагов: сначала конвертируйте в Canvas, затем конвертируйте в изображение и, наконец, добавьте в PDF:

```typescript
import jsPDF from 'jspdf'

const exportAsPDF = async () => {
  // First capture map image
  await captureMapImage()

  const element = document.getElementById('trip-plan-content')
  if (!element) return

  const canvas = await html2canvas(element, {
    backgroundColor: '#ffffff',
    scale: 2,
    useCORS: true,
    allowTaint: true
  })

  // Restore map
  restoreMap()

  const pdf = new jsPDF('p', 'mm', 'a4')
  const imgData = canvas.toDataURL('image/png')
  const imgWidth = 210  // A4 width
  const imgHeight = (canvas.height * imgWidth) / canvas.width

  pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight)
  pdf.save(`${tripPlan.value.city} Travel Plan.pdf`)
  message.success('Export successful!')
}
```

Здесь нам нужно рассчитать высоту изображения, чтобы сохранить соотношение сторон. Ширина бумаги формата А4 составляет 210 мм, и мы рассчитываем соответствующую высоту на основе соотношения сторон холста.

### 13.6.5 Боковая навигация и переход от якоря

Страница результатов содержит много контента, включая обзор маршрута, сведения о бюджете, карту, ежедневный маршрут, информацию о погоде и т. д. Если пользователи хотят быстро перейти к определенному разделу, им необходимо прокрутить большое расстояние. Мы предоставляем боковую навигацию и функцию перехода к якорю, что позволяет пользователям быстро находить нужные объекты.

Боковая навигация использует компонент меню Ant Design Vue:

```vue
<a-menu
  v-model:selectedKeys="[activeSection]"
  mode="inline"
  @click="scrollToSection"
>
  <a-menu-item key="overview">📋 Itinerary Overview</a-menu-item>
  <a-menu-item key="budget">💰 Budget Details</a-menu-item>
  <a-menu-item key="map">🗺️ Map</a-menu-item>
  <a-menu-item key="days">📅 Daily Itinerary</a-menu-item>
  <a-menu-item key="weather">🌤️ Weather</a-menu-item>
</a-menu>
```

При нажатии на пункт меню вызывается`scrollToSection`функция:

```typescript
const activeSection = ref('overview')

// Scroll to specified section
const scrollToSection = ({ key }: { key: string }) => {
  activeSection.value = key
  const element = document.getElementById(key)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
```

`scrollIntoView`— это собственный API браузера, который может прокручивать элемент в видимую область.`behavior: 'smooth'`означает плавную прокрутку, а не мгновенный прыжок.`block: 'start'`означает, что верхняя часть элемента совпадает с верхней частью видимой области.

В различных частях страницы нам нужно добавить соответствующие идентификаторы:

```vue
<div id="overview">
  <!-- Itinerary overview content -->
</div>

<div id="budget">
  <!-- Budget details content -->
</div>

<div id="map">
  <!-- Map content -->
</div>
```

Таким образом, когда пользователи нажимают на пункт меню в боковой навигации, страница плавно прокручивается до соответствующего раздела.

Благодаря реализации этих функций наш интеллектуальный помощник по путешествиям не только создает планы поездок, но и предоставляет богатые интерактивные функции: расчет бюджета позволяет пользователям понять затраты, индикатор выполнения загрузки делает ожидание менее тревожным, редактирование маршрута делает планы более персонализированными, функция экспорта позволяет делиться планами и сохранять их, а боковая навигация упрощает просмотр длинных страниц. Комбинация этих функций образует законченное, удобное и практичное веб-приложение.

## 13.7 Заключение

Поздравляем с завершением главы 13!

Из этой главы вы не только узнали, как создать полноценное интеллектуальное приложение-помощник в путешествии, но, что более важно, освоили:

1. **Системное проектное мышление**: как разложить сложные проблемы на несколько простых задач.
2. **Возможности инженерной практики**: Как превратить теоретические знания в работоспособный код.
3. **Возможность полнофункциональной разработки**: как интегрировать стеки интерфейсных и серверных технологий.
4. **Разработка приложений ИИ**: как использовать LLM для создания практических приложений

Этот проект является отправной точкой, а не конечной точкой. На основе этого проекта вы сможете:

- Добавить больше функций
- Оптимизируйте пользовательский опыт
- Распространение на другие области (например, интеллектуальный помощник в покупках, интеллектуальный помощник в обучении и т. д.).
- Развертывание в производственной среде для обслуживания реальных пользователей.

Лучший способ учиться – это практика. Не просто читайте код — изменяйте, расширяйте и оптимизируйте его самостоятельно. Каждая практика углубит ваше понимание мультиагентных систем.

Желаем вам успехов в разработке приложений искусственного интеллекта!

