"""Маршрутизация API картографического сервиса"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ...models.schemas import (
    POISearchRequest,
    POISearchResponse,
    RouteRequest,
    RouteResponse,
    WeatherResponse
)
from ...services.amap_service import get_amap_service

router = APIRouter(prefix="/map", tags=["картографический сервис"])


@router.get(
    "/poi",
    response_model=POISearchResponse,
    summary="Поиск POI",
    description="Поиск POI (достопримечательностей) по ключевым словам"
)
async def search_poi(
    keywords: str = Query(..., description="Ключевые слова для поиска", example="Запретный город"),
    city: str = Query(..., description="Город", example="Пекин"),
    citylimit: bool = Query(True, description="Ограничено ли это пределами города?")
):
    """
    Поиск POI
    
    Аргументы:
        ключевые слова: ключевые слова для поиска
        город: город
        citylimit: ограничивать ли его пределами города
        
    Возврат:
        Результаты поиска POI
    """
    try:
        # Получить экземпляр службы
        service = get_amap_service()
        
        # Поиск POI
        pois = service.search_poi(keywords, city, citylimit)
        
        return POISearchResponse(
            success=True,
            message="Поиск POI успешен",
            data=pois
        )
        
    except Exception as e:
        print(f"❌ Не удалось найти POI: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось выполнить поиск POI: {str(e)}"
        )


@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="Проверьте погоду",
    description="Запрос информации о погоде для указанного города"
)
async def get_weather(
    city: str = Query(..., description="название города", example="Пекин")
):
    """
    Проверьте погоду
    
    Аргументы:
        город: название города
        
    Возврат:
        информация о погоде
    """
    try:
        # Получить экземпляр службы
        service = get_amap_service()
        
        # Проверьте погоду
        weather_info = service.get_weather(city)
        
        return WeatherResponse(
            success=True,
            message="Запрос погоды успешен",
            data=weather_info
        )
        
    except Exception as e:
        print(f"❌ Ошибка запроса погоды: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось выполнить запрос погоды: {str(e)}"
        )


@router.post(
    "/route",
    response_model=RouteResponse,
    summary="Спланировать маршрут",
    description="Спланируйте маршрут между двумя точками"
)
async def plan_route(request: RouteRequest):
    """
    Спланировать маршрут
    
    Аргументы:
        запрос: запрос на планирование маршрута
        
    Возврат:
        информация о маршруте
    """
    try:
        # Получить экземпляр службы
        service = get_amap_service()
        
        # Спланировать маршрут
        route_info = service.plan_route(
            origin_address=request.origin_address,
            destination_address=request.destination_address,
            origin_city=request.origin_city,
            destination_city=request.destination_city,
            route_type=request.route_type
        )
        
        return RouteResponse(
            success=True,
            message="Планирование маршрута прошло успешно.",
            data=route_info
        )
        
    except Exception as e:
        print(f"❌ Не удалось спланировать маршрут: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось спланировать маршрут: {str(e)}"
        )


@router.get(
    "/health",
    summary="проверка здоровья",
    description="Проверьте, нормально ли работает картографический сервис"
)
async def health_check():
    """проверка здоровья"""
    try:
        # Проверьте, доступна ли услуга
        service = get_amap_service()
        
        return {
            "status": "healthy",
            "service": "map-service",
            "mcp_tools_count": len(service.mcp_tool._available_tools)
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Сервис недоступен: {str(e)}"
        )

