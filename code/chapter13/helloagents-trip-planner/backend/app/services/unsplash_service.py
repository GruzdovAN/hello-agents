"""Сервис изображений Unsplash"""

import requests
from typing import List, Optional
from ..config import get_settings

class UnsplashService:
    """Класс обслуживания изображений Unsplash"""
    
    def __init__(self):
        """Инициализировать службу"""
        settings = get_settings()
        self.access_key = settings.unsplash_access_key
        self.base_url = "https://api.unsplash.com"
    
    def search_photos(self, query: str, per_page: int = 5) -> List[dict]:
        """
        Поиск изображений
        
        Аргументы:
            запрос: ключевое слово поиска
            per_page: количество на странице
            
        Возврат:
            Список изображений
        """
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
            
            # Извлечь URL-адрес изображения
            photos = []
            for photo in results:
                photos.append({
                    "id": photo.get("id"),
                    "url": photo.get("urls", {}).get("regular"),
                    "thumb": photo.get("urls", {}).get("thumb"),
                    "description": photo.get("description") or photo.get("alt_description"),
                    "photographer": photo.get("user", {}).get("name")
                })
            
            return photos
            
        except Exception as e:
            print(f"❌ Ошибка поиска Unsplash: {str(e)}")
            return []
    
    def get_photo_url(self, query: str) -> Optional[str]:
        """
        Получить URL-адрес одного изображения

        Аргументы:
            запрос: ключевое слово поиска

        Возврат:
            URL-адрес изображения
        """
        photos = self.search_photos(query, per_page=1)
        if photos:
            return photos[0].get("url")
        return None


# Глобальный экземпляр службы
_unsplash_service = None


def get_unsplash_service() -> UnsplashService:
    """Получите экземпляр службы Unsplash (одиночный режим)"""
    global _unsplash_service
    
    if _unsplash_service is None:
        _unsplash_service = UnsplashService()
    
    return _unsplash_service

