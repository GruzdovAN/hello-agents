"""Определение модели данных"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import date


# ============ Модель запроса ============

class TripRequest(BaseModel):
    """запрос на планирование поездки"""
    city: str = Field(..., description="город назначения", example="Пекин")
    start_date: str = Field(..., description="Дата начала ГГГГ-ММ-ДД", example="2025-06-01")
    end_date: str = Field(..., description="Дата окончания ГГГГ-ММ-ДД", example="2025-06-03")
    travel_days: int = Field(..., description="Дни путешествия", ge=1, le=30, example=3)
    transportation: str = Field(..., description="Транспорт", example="общественный транспорт")
    accommodation: str = Field(..., description="Предпочтения по размещению", example="Бюджетный отель")
    preferences: List[str] = Field(default=[], description="Тег предпочтений путешествия", example=["история и культура", "изысканная еда"])
    free_text_input: Optional[str] = Field(default="", description="дополнительные требования", example="Я надеюсь организовать больше музеев")
    
    class Config:
        json_schema_extra = {
            "example": {
                "city": "Пекин",
                "start_date": "2025-06-01",
                "end_date": "2025-06-03",
                "travel_days": 3,
                "transportation": "общественный транспорт",
                "accommodation": "Бюджетный отель",
                "preferences": ["история и культура", "изысканная еда"],
                "free_text_input": "Я надеюсь организовать больше музеев"
            }
        }


class POISearchRequest(BaseModel):
    """Запрос на поиск POI"""
    keywords: str = Field(..., description="Ключевые слова для поиска", example="Запретный город")
    city: str = Field(..., description="Город", example="Пекин")
    citylimit: bool = Field(default=True, description="Ограничено ли это пределами города?")


class RouteRequest(BaseModel):
    """запрос на планирование маршрута"""
    origin_address: str = Field(..., description="Начальный адрес", example="№ 6, Восточная улица Футун, район Чаоян, Пекин")
    destination_address: str = Field(..., description="Конечный адрес", example="№ 10, 10-я улица Шанди, район Хайдянь, Пекин")
    origin_city: Optional[str] = Field(default=None, description="стартовый город")
    destination_city: Optional[str] = Field(default=None, description="Конечный город")
    route_type: str = Field(default="walking", description="Тип маршрута: пешеходный/автомобильный/транзитный")


# ============ Модель ответа ============

class Location(BaseModel):
    """географическое положение"""
    longitude: float = Field(..., description="долгота")
    latitude: float = Field(..., description="широта")


class Attraction(BaseModel):
    """Информация о достопримечательностях"""
    name: str = Field(..., description="Название достопримечательности")
    address: str = Field(..., description="адрес")
    location: Location = Field(..., description="Координаты широты и долготы")
    visit_duration: int = Field(..., description="Рекомендуемое время экскурсии (минуты)")
    description: str = Field(..., description="Описание достопримечательности")
    category: Optional[str] = Field(default="Достопримечательности", description="Категория достопримечательности")
    rating: Optional[float] = Field(default=None, description="счет")
    photos: Optional[List[str]] = Field(default_factory=list, description="Список URL-адресов изображений достопримечательностей")
    poi_id: Optional[str] = Field(default="", description="POI ID")
    image_url: Optional[str] = Field(default=None, description="URL-адрес изображения")
    ticket_price: int = Field(default=0, description="Стоимость билета (юани)")


class Meal(BaseModel):
    """Информация о питании"""
    type: str = Field(..., description="Тип питания: завтрак/обед/ужин/перекус.")
    name: str = Field(..., description="Название заведения")
    address: Optional[str] = Field(default=None, description="адрес")
    location: Optional[Location] = Field(default=None, description="Координаты широты и долготы")
    description: Optional[str] = Field(default=None, description="описывать")
    estimated_cost: int = Field(default=0, description="Ориентировочная стоимость (юань)")


class Hotel(BaseModel):
    """Информация об отеле"""
    name: str = Field(..., description="Название отеля")
    address: str = Field(default="", description="Адрес отеля")
    location: Optional[Location] = Field(default=None, description="Расположение отеля")
    price_range: str = Field(default="", description="ценовой диапазон")
    rating: str = Field(default="", description="счет")
    distance: str = Field(default="", description="Расстояние от достопримечательностей")
    type: str = Field(default="", description="Тип отеля")
    estimated_cost: int = Field(default=0, description="Ориентировочная стоимость (юаней/ночь)")


class DayPlan(BaseModel):
    """Маршрут на один день"""
    date: str = Field(..., description="Дата ГГГГ-ММ-ДД")
    day_index: int = Field(..., description="День (начиная с 0)")
    description: str = Field(..., description="Описание маршрута дня")
    transportation: str = Field(..., description="Транспорт")
    accommodation: str = Field(..., description="оставаться")
    hotel: Optional[Hotel] = Field(default=None, description="Рекомендуемые отели")
    attractions: List[Attraction] = Field(default=[], description="Список достопримечательностей")
    meals: List[Meal] = Field(default=[], description="Список питания")


class WeatherInfo(BaseModel):
    """информация о погоде"""
    date: str = Field(..., description="Дата ГГГГ-ММ-ДД")
    day_weather: str = Field(default="", description="дневная погода")
    night_weather: str = Field(default="", description="ночная погода")
    day_temp: Union[int, str] = Field(default=0, description="дневная температура")
    night_temp: Union[int, str] = Field(default=0, description="ночная температура")
    wind_direction: str = Field(default="", description="направление ветра")
    wind_power: str = Field(default="", description="сила ветра")

    @field_validator('day_temp', 'night_temp', mode='before')
    @classmethod
    def parse_temperature(cls, v):
        """Разобрать температуру, удалить единицы измерения, такие как °C"""
        if isinstance(v, str):
            # Удалите символы единиц измерения, такие как °C, ℃ и т. д.
            v = v.replace('°C', '').replace('℃', '').replace('°', '').strip()
            try:
                return int(v)
            except ValueError:
                return 0
        return v


class Budget(BaseModel):
    """информация о бюджете"""
    total_attractions: int = Field(default=0, description="Общая стоимость билетов на аттракционы")
    total_hotels: int = Field(default=0, description="общая стоимость отеля")
    total_meals: int = Field(default=0, description="общая стоимость еды")
    total_transportation: int = Field(default=0, description="общая стоимость перевозки")
    total: int = Field(default=0, description="общая стоимость")


class TripPlan(BaseModel):
    """планирование поездки"""
    city: str = Field(..., description="город назначения")
    start_date: str = Field(..., description="Дата начала")
    end_date: str = Field(..., description="дата окончания")
    days: List[DayPlan] = Field(..., description="Ежедневный маршрут")
    weather_info: List[WeatherInfo] = Field(default=[], description="информация о погоде")
    overall_suggestions: str = Field(..., description="Общие рекомендации")
    budget: Optional[Budget] = Field(default=None, description="информация о бюджете")


class TripPlanResponse(BaseModel):
    """ответ по планированию поездки"""
    success: bool = Field(..., description="Это успешно?")
    message: str = Field(default="", description="информация")
    data: Optional[TripPlan] = Field(default=None, description="данные планирования поездки")


class POIInfo(BaseModel):
    """Информация о POI"""
    id: str = Field(..., description="POI ID")
    name: str = Field(..., description="имя")
    type: str = Field(..., description="тип")
    address: str = Field(..., description="адрес")
    location: Location = Field(..., description="Координаты широты и долготы")
    tel: Optional[str] = Field(default=None, description="Телефон")


class POISearchResponse(BaseModel):
    """Ответ на поиск POI"""
    success: bool = Field(..., description="Это успешно?")
    message: str = Field(default="", description="информация")
    data: List[POIInfo] = Field(default=[], description="Список POI")


class RouteInfo(BaseModel):
    """информация о маршруте"""
    distance: float = Field(..., description="Расстояние (метры)")
    duration: int = Field(..., description="время (секунды)")
    route_type: str = Field(..., description="тип маршрута")
    description: str = Field(..., description="описание маршрута")


class RouteResponse(BaseModel):
    """ответ на планирование маршрута"""
    success: bool = Field(..., description="Это успешно?")
    message: str = Field(default="", description="информация")
    data: Optional[RouteInfo] = Field(default=None, description="информация о маршруте")


class WeatherResponse(BaseModel):
    """Ответ на запрос погоды"""
    success: bool = Field(..., description="Это успешно?")
    message: str = Field(default="", description="информация")
    data: List[WeatherInfo] = Field(default=[], description="информация о погоде")


# ============ Ответ об ошибке ============

class ErrorResponse(BaseModel):
    """ответ об ошибке"""
    success: bool = Field(default=False, description="Это успешно?")
    message: str = Field(..., description="сообщение об ошибке")
    error_code: Optional[str] = Field(default=None, description="код ошибки")

