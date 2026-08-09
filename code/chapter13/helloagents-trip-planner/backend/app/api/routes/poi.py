"""Маршрутизация API, связанная с POI"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from ...services.amap_service import get_amap_service
from ...services.unsplash_service import get_unsplash_service

router = APIRouter(prefix="/poi", tags=["POI"])


class POIDetailResponse(BaseModel):
    """Ответ с подробностями POI"""
    success: bool
    message: str
    data: Optional[dict] = None


@router.get(
    "/detail/{poi_id}",
    response_model=POIDetailResponse,
    summary="Получить подробную информацию о POI",
    description="Получите подробную информацию на основе идентификатора POI, включая изображения."
)
async def get_poi_detail(poi_id: str):
    """
    Получить подробную информацию о POI
    
    Аргументы:
        poi_id: идентификатор POI
        
    Возврат:
        Ответ с подробностями POI
    """
    try:
        amap_service = get_amap_service()
        
        # Вызовите API сведений о POI Amap.
        result = amap_service.get_poi_detail(poi_id)
        
        return POIDetailResponse(
            success=True,
            message="Получите подробную информацию о POI успешно",
            data=result
        )
        
    except Exception as e:
        print(f"❌ Не удалось получить сведения о POI: {str(e)}.")
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось получить сведения о POI: {str(e)}."
        )


@router.get(
    "/search",
    summary="Поиск POI",
    description="Поиск POI по ключевым словам"
)
async def search_poi(keywords: str, city: str = "Пекин"):
    """
    Поиск POI

    Аргументы:
        ключевые слова: ключевые слова для поиска
        город: название города

    Возврат:
        Результаты поиска
    """
    try:
        amap_service = get_amap_service()
        result = amap_service.search_poi(keywords, city)

        return {
            "success": True,
            "message": "Поиск успешен",
            "data": result
        }

    except Exception as e:
        print(f"❌ Не удалось найти POI: {str(e)}.")
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось найти POI: {str(e)}."
        )


@router.get(
    "/photo",
    summary="Получите фотографии достопримечательностей",
    description="Получите изображения из Unsplash на основе названий достопримечательностей."
)
async def get_attraction_photo(name: str):
    """
    Получите фотографии достопримечательностей

    Аргументы:
        название: Название достопримечательности

    Возврат:
        URL-адрес изображения
    """
    try:
        unsplash_service = get_unsplash_service()

        # Поиск фотографий достопримечательностей
        photo_url = unsplash_service.get_photo_url(f"{name} China landmark")

        if not photo_url:
            # Если не найдено, попробуйте выполнить поиск только по названию достопримечательности.
            photo_url = unsplash_service.get_photo_url(name)

        return {
            "success": True,
            "message": "Изображение получено успешно",
            "data": {
                "name": name,
                "photo_url": photo_url
            }
        }

    except Exception as e:
        print(f"❌ Не удалось получить фотографии живописных мест: {str(e)}.")
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось получить фотографии живописных мест: {str(e)}."
        )

