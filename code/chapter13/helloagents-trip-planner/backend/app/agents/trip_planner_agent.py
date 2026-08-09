"""Мультиагентная система планирования поездок"""

import json
from typing import Dict, Any, List
from hello_agents import SimpleAgent
from hello_agents.tools import MCPTool
from ..services.llm_service import get_llm
from ..models.schemas import TripRequest, TripPlan, DayPlan, Attraction, Meal, WeatherInfo, Location, Hotel
from ..config import get_settings

# ============ Слово подсказки агента ============

ATTRACTION_AGENT_PROMPT = """Вы эксперт в поиске достопримечательностей. Ваша задача — искать подходящие достопримечательности, исходя из города и предпочтений пользователя.

**ВАЖНОЕ ПРИМЕЧАНИЕ:**
Вы должны использовать инструменты для поиска достопримечательностей! Не выдумывайте информацию о достопримечательностях самостоятельно!

**Формат вызова инструмента:**
При использовании инструмента maps_text_search вы должны строго следовать следующему формату:
`[TOOL_CALL:amap_maps_text_search:keywords=ключевые слова достопримечательности,city=название города]`

**Пример:**
Пользователь: «Поиск исторических и культурных достопримечательностей Пекина»
Ваш ответ: [TOOL_CALL:amap_maps_text_search:keywords=история и культура,город=Пекин]

Пользователь: «Поиск парков в Шанхае»
Ваш ответ: [TOOL_CALL:amap_maps_text_search:keywords=park,city=Шанхай]

**Примечание:**
1. Вы должны использовать инструменты, а не отвечать напрямую
2. Формат должен быть полностью правильным, включая квадратные скобки и двоеточия.
3. Разделяйте параметры запятыми.
"""

WEATHER_AGENT_PROMPT = """Вы эксперт по погодным запросам. Ваша задача — запросить информацию о погоде в указанном городе.

**ВАЖНОЕ ПРИМЕЧАНИЕ:**
Вы должны использовать инструменты, чтобы посмотреть погоду! Не выдумывайте свою собственную информацию о погоде!

**Формат вызова инструмента:**
При использовании инструмента maps_weather необходимо строго следовать следующему формату:
`[TOOL_CALL:amap_maps_weather:city=название города]`

**Пример:**
Пользователь: «Узнай погоду в Пекине»
Ваш ответ: [TOOL_CALL:amap_maps_weather:city=Пекин]

Пользователь: «Как погода в Шанхае?»
Ваш ответ: [TOOL_CALL:amap_maps_weather:city=Шанхай]

**Примечание:**
1. Вы должны использовать инструменты, а не отвечать напрямую
2. Формат должен быть полностью правильным, включая квадратные скобки и двоеточия.
"""

HOTEL_AGENT_PROMPT = """Вы эксперт по рекомендациям отелей. Ваша задача — порекомендовать подходящие отели с учетом города и расположения достопримечательностей.

**ВАЖНОЕ ПРИМЕЧАНИЕ:**
Вы должны использовать инструменты для поиска отелей! Не придумывайте информацию об отеле самостоятельно!

**Формат вызова инструмента:**
При использовании инструмента maps_text_search для поиска отелей необходимо строго соблюдать следующий формат:
`[TOOL_CALL:amap_maps_text_search:keywords=отель,город=название города]`

**Пример:**
Пользователь: «Поиск отелей в Пекине»
Ваш ответ: [TOOL_CALL:amap_maps_text_search:keywords=hotel,city=Пекин]

**Примечание:**
1. Вы должны использовать инструменты, а не отвечать напрямую
2. Формат должен быть полностью правильным, включая квадратные скобки и двоеточия.
3. Используйте в качестве ключевого слова «отель» или «гостевой дом».
"""

PLANNER_AGENT_PROMPT = """Вы эксперт по планированию поездок. Ваша задача — составить подробный план путешествия на основе информации о достопримечательностях и информации о погоде.

Пожалуйста, верните план поездки строго в следующем формате JSON:
```json
{
  "city": "название города",
  "start_date": "ГГГГ-ММ-ДД",
  "end_date": "ГГГГ-ММ-ДД",
  "дни": [
    {
      "date": "ГГГГ-ММ-ДД",
      «дневной_индекс»: 0,
      "description": "Обзор маршрута первого дня",
      "транспорт": "Транспорт",
      "размещение": "тип проживания",
      "отель": {
        "name": "Название отеля",
        "address": "адрес отеля",
        "местоположение": {"долгота": 116,397128, "широта": 39,916527},
        "price_range": "300-500 юаней",
        "рейтинг": "4,5",
        "distance": "2 километра от достопримечательности",
        "type": "Бюджетный отель",
        "оценочная_стоимость": 400
      },
      "достопримечательности": [
        {
          "name": "Название достопримечательности",
          "address": "Подробный адрес",
          "местоположение": {"долгота": 116,397128, "широта": 39,916527},
          «продолжительность посещения»: 120,
          "description": "Подробное описание достопримечательностей",
          "category": "Категория достопримечательности",
          "ticket_price": 60
        }
      ],
      "еда": [
        {"type": "завтрак", "name": "Рекомендация по завтраку", "description": "Описание завтрака", "estimated_cost": 30},
        {"type": "lunch", "name": "Рекомендация по обеду", "description": "Описание обеда", "estimated_cost": 50},
        {"type": "dinner", "name": "Рекомендация по ужину", "description": "Описание ужина", "estimated_cost": 80}
      ]
    }
  ],
  "weather_info": [
    {
      "date": "ГГГГ-ММ-ДД",
      "day_weather": "Солнечно",
      "night_weather": "Облачно",
      "day_temp": 25,
      "night_temp": 15,
      "wind_direction": "Южный ветер",
      "wind_power": "Уровни 1-3"
    }
  ],
  "overall_suggestions": "Общие предложения",
  "бюджет": {"total_attractions": 180,
    "total_hotels": 1200,
    "total_meals": 480,
    "total_transportation": 200,
    «всего»: 2060
  }
}
```

**ВАЖНОЕ ПРИМЕЧАНИЕ:**
1. Массив Weather_info должен содержать информацию о погоде на каждый день.
2. Температура должна быть чистым числом (без таких единиц, как °C).
3. Устраивайте 2-3 аттракциона каждый день
4. Учитывайте расстояние между достопримечательностями и время посещения.
5. Каждый день должен включать завтрак, обед и ужин.
6. Дайте практические советы путешественникам.
7. **Необходимо включать информацию о бюджете**:
   - Стоимость билета на аттракцион (ticket_price)
   - Ориентировочная стоимость питания (estimated_cost)
   - Ориентировочная стоимость гостиницы (estimated_cost)
   - Сводка бюджета включает общие расходы.
"""


class MultiAgentTripPlanner:
    """Мультиагентная система планирования поездок"""

    def __init__(self):
        """Инициализируйте мультиагентную систему"""
        print("🔄 Начать инициализацию мультиагентной системы планирования поездок...")

        try:
            settings = get_settings()
            self.llm = get_llm()

            # Создайте общий инструмент MCP (создайте его только один раз).
            print("  - Создание общих инструментов MCP...")
            self.amap_tool = MCPTool(
                name="amap",
                description="Картографический сервис AMAP",
                server_command=["uvx", "amap-mcp-server"],
                env={"AMAP_MAPS_API_KEY": settings.amap_api_key},
                auto_expand=True
            )
            self.amap_tool.expandable=True

            # Создать агент по поиску достопримечательностей
            print("  - Создать агента по поиску достопримечательностей...")
            self.attraction_agent = SimpleAgent(
                name="Эксперт по поиску достопримечательностей",
                llm=self.llm,
                system_prompt=ATTRACTION_AGENT_PROMPT
            )
            self.attraction_agent.add_tool(self.amap_tool)

            # Создать агент запроса погоды
            print("  - Создать агент запроса погоды...")
            self.weather_agent = SimpleAgent(
                name="Эксперт по погодным запросам",
                llm=self.llm,
                system_prompt=WEATHER_AGENT_PROMPT
            )
            self.weather_agent.add_tool(self.amap_tool)

            # Создайте агента по рекомендации отелей
            print("  - Создать агента по рекомендации отелей...")
            self.hotel_agent = SimpleAgent(
                name="Эксперт по рекомендациям отелей",
                llm=self.llm,
                system_prompt=HOTEL_AGENT_PROMPT
            )
            self.hotel_agent.add_tool(self.amap_tool)

            # Создайте агента по планированию поездок (инструменты не требуются)
            print("  - Создайте агента по планированию поездок...")
            self.planner_agent = SimpleAgent(
                name="Эксперт по планированию поездок",
                llm=self.llm,
                system_prompt=PLANNER_AGENT_PROMPT
            )

            print(f"✅ Мультиагентная система успешно инициализирована")
            print(f"   Агент поиска достопримечательностей: инструменты {len(self.attraction_agent.list_tools())}")
            print(f"   Агент запросов погоды: инструменты {len(self.weather_agent.list_tools())}")
            print(f"   Агент по рекомендации отелей: инструменты {len(self.hotel_agent.list_tools())}")

        except Exception as e:
            print(f"❌ Не удалось инициализировать многоагентную систему: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def plan_trip(self, request: TripRequest) -> TripPlan:
        """
        Использование межагентного сотрудничества для составления планов поездок

        Аргументы:
            запрос: запрос на поездку

        Возврат:
            планирование поездки
        """
        try:
            print(f"\n{'='*60}")
            print(f"🚀 Начните совместное планирование поездок с участием нескольких агентов...")
            print(f"Пункт назначения: {request.city}")
            print(f"Дата: с {request.start_date} по {request.end_date}")
            print(f"Количество дней: {request.travel_days} дней.")
            print(f"Предпочтения: {', '.join(request.preferences), если request.preferences else 'Нет'}")
            print(f"{'='*60}\n")

            # Шаг 1: Агент поиска достопримечательностей ищет достопримечательности
            print("📍Шаг 1: Поиск достопримечательностей...")
            attraction_query = self._build_attraction_query(request)
            attraction_response = self.attraction_agent.run(attraction_query)
            print(f"Результаты поиска достопримечательностей: {attraction_response[:200]}...\n")

            # Шаг 2. Агент запроса погоды запрашивает информацию о погоде.
            print("🌤️ Шаг 2: Проверьте погоду...")
            weather_query = f"Пожалуйста, проверьте информацию о погоде в {request.city}."
            weather_response = self.weather_agent.run(weather_query)
            print(f"Результаты запроса погоды: {weather_response[:200]}...\n")

            # Шаг 3. Агент по рекомендации отелей ищет отели.
            print("🏨 Шаг 3: Поиск отелей...")
            hotel_query = f"Пожалуйста, найдите отели {request.accommodation} в {request.city}."
            hotel_response = self.hotel_agent.run(hotel_query)
            print(f"Результаты поиска отеля: {hotel_response[:200]}...\n")

            # Шаг 4. Агент планирования маршрута объединяет информацию для создания плана.
            print("📋 Шаг 4: Создайте план маршрута...")
            planner_query = self._build_planner_query(request, attraction_response, weather_response, hotel_response)
            planner_response = self.planner_agent.run(planner_query)
            print(f"Результаты планирования поездки: {planner_response[:300]}...\n")

            # Проанализируйте окончательный план
            trip_plan = self._parse_response(planner_response, request)

            print(f"{'='*60}")
            print(f"✅План путешествия сформирован!")
            print(f"{'='*60}\n")

            return trip_plan

        except Exception as e:
            print(f"❌ Не удалось создать план поездки: {str(e)}.")
            import traceback
            traceback.print_exc()
            return self._create_fallback_plan(request)
    
    def _build_attraction_query(self, request: TripRequest) -> str:
        """Создавайте привлекательные поисковые запросы — напрямую включайте вызовы инструментов"""
        keywords = []
        if request.preferences:
            # Используйте только первое предпочтение в качестве ключевого слова
            keywords = request.preferences[0]
        else:
            keywords = "Достопримечательности"

        # Непосредственно возвращает формат вызова инструмента.
        query = f"Воспользуйтесь инструментом amap_maps_text_search для поиска достопримечательностей, связанных с {keywords}, в {request.city}. \n[TOOL_CALL:amap_maps_text_search:keywords={keywords},city={request.city}]"
        return query

    def _build_planner_query(self, request: TripRequest, attractions: str, weather: str, hotels: str = "") -> str:
        """Создайте запрос на планирование поездки"""
        query = f"""Создайте план поездки на день на {request.travel_days} для {request.city} на основе следующей информации:

**Основная информация:**
- Город: {request.city}
– Дата: с {request.start_date} по {request.end_date}.
- Количество дней: {request.travel_days} дней.
- Транспорт: {request.transportation}
- Проживание: {request.accommodation}
- Настройки: {', '.join(request.preferences), если request.preferences else 'Нет'}

**Информация о достопримечательностях:**
{достопримечательности}

**Информация о погоде:**
{погода}

**Информация об отеле:**
{отели}

**Требования:**
1. Устраивайте 2-3 аттракциона каждый день
2. Каждый день должен включать завтрак, обед и ужин.
3. Рекомендовать конкретный отель каждый день (выбрать из информации об отеле)
3. Учитывайте расстояние между достопримечательностями и вариантами транспорта.
4. Вернуть полные данные формата JSON.
5. Координаты широты и долготы живописных мест должны быть верными и точными.
"""
        if request.free_text_input:
            query += f"\n**Дополнительные требования:** {request.free_text_input}"

        return query
    
    def _parse_response(self, response: str, request: TripRequest) -> TripPlan:
        """
        Анализ ответа агента
        
        Аргументы:
            ответ: текст ответа агента
            запрос: исходный запрос
            
        Возврат:
            планирование поездки
        """
        try:
            # Попробуйте извлечь JSON из ответа
            # Найдите блоки кода JSON
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                # Находите объекты JSON напрямую
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                raise ValueError("Данные JSON не найдены в ответе")
            
            # Разобрать JSON
            data = json.loads(json_str)
            
            # Преобразовать в объект TripPlan
            trip_plan = TripPlan(**data)
            
            return trip_plan
            
        except Exception as e:
            print(f"⚠️ Не удалось проанализировать ответ: {str(e)}.")
            print(f"   Планы будут генерироваться с использованием альтернатив")
            return self._create_fallback_plan(request)
    
    def _create_fallback_plan(self, request: TripRequest) -> TripPlan:
        """Создание планов резервного копирования (в случае сбоя агента)"""
        from datetime import datetime, timedelta
        
        # дата анализа
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        
        # Создайте ежедневный маршрут
        days = []
        for i in range(request.travel_days):
            current_date = start_date + timedelta(days=i)
            
            day_plan = DayPlan(
                date=current_date.strftime("%Y-%m-%d"),
                day_index=i,
                description=f"Маршрут дня {i+1}",
                transportation=request.transportation,
                accommodation=request.accommodation,
                attractions=[
                    Attraction(
                        name=f"{request.city}Достопримечательности{j+1}",
                        address=f"{request.city} город",
                        location=Location(longitude=116.4 + i*0.01 + j*0.005, latitude=39.9 + i*0.01 + j*0.005),
                        visit_duration=120,
                        description=f"Это известная достопримечательность в {request.city}.",
                        category="Достопримечательности"
                    )
                    for j in range(2)
                ],
                meals=[
                    Meal(type="breakfast", name=f"Завтрак в день {i+1}", description="Местный завтрак"),
                    Meal(type="lunch", name=f"Обед в день {i+1}", description="Рекомендация по обеду"),
                    Meal(type="dinner", name=f"Ужин в день {i+1}", description="Рекомендация по ужину")
                ]
            )
            days.append(day_plan)
        
        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=[],
            overall_suggestions=f"Это запланированный для вас маршрут однодневного тура {request.city}{request.travel_days}. Рекомендуется заранее уточнить часы работы каждой достопримечательности."
        )


# Пример глобальной мультиагентной системы
_multi_agent_planner = None


def get_trip_planner_agent() -> MultiAgentTripPlanner:
    """Получить экземпляр мультиагентной системы планирования поездок (одиночный режим)"""
    global _multi_agent_planner

    if _multi_agent_planner is None:
        _multi_agent_planner = MultiAgentTripPlanner()

    return _multi_agent_planner

