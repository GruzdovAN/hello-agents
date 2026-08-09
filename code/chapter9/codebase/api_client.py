"""
Клиентский модуль API
Для взаимодействия с внешними API
"""

import requests
from typing import Dict, Any, Optional


class APIClient:
    """Базовый класс клиента API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Инициализировать API-клиент
        
        Аргументы:
            base_url: базовый URL-адрес API
            api_key: ключ API
        """
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Отправить GET-запрос
        
        Аргументы:
            конечная точка: конечная точка API
            параметры: параметры запроса
            
        Возврат:
            данные ответа
        """
        # TODO: Добавить логику повтора
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Отправить POST-запрос
        
        Аргументы:
            конечная точка: конечная точка API
            данные: запросить данные
            
        Возврат:
            данные ответа
        """
        # TODO: Добавить обработку ошибок
        url = f"{self.base_url}/{endpoint}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Отправить запрос PUT
        
        Аргументы:
            конечная точка: конечная точка API
            данные: запросить данные
            
        Возврат:
            данные ответа
        """
        url = f"{self.base_url}/{endpoint}"
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str) -> None:
        """
        Отправить запрос на УДАЛЕНИЕ
        
        Аргументы:
            конечная точка: конечная точка API
        """
        # TODO: Добавить механизм подтверждения
        url = f"{self.base_url}/{endpoint}"
        response = self.session.delete(url)
        response.raise_for_status()

