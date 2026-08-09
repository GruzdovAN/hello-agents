"""Пакет услуг Amap MCP"""

from typing import List, Dict, Any, Optional
from hello_agents.tools import MCPTool
from ..config import get_settings
from ..models.schemas import Location, POIInfo, WeatherInfo

# Пример глобального инструмента MCP
_amap_mcp_tool = None


def get_amap_mcp_tool() -> MCPTool:
    """
    Получите экземпляр инструмента Amap MCP (одиночный режим)
    
    Возврат:
        Экземпляр MCPTool
    """
    global _amap_mcp_tool
    
    if _amap_mcp_tool is None:
        settings = get_settings()
        
        if not settings.amap_api_key:
            raise ValueError("Ключ AMAP API не настроен, установите AMAP_API_KEY в файле .env.")
        
        # Создание инструментов MCP
        _amap_mcp_tool = MCPTool(
            name="amap",
            description="Сервис Amap поддерживает поиск POI, планирование маршрута, запрос погоды и другие функции.",
            server_command=["uvx", "amap-mcp-server"],
            env={"AMAP_MAPS_API_KEY": settings.amap_api_key},
            auto_expand=True  # Автоматически расширяться до независимых инструментов
        )
        
        print(f"✅ Инструмент Amap MCP успешно инициализирован")
        print(f"   Количество инструментов: {len(_amap_mcp_tool._available_tools)}")
        
        # Распечатать список доступных инструментов
        if _amap_mcp_tool._available_tools:
            print("   Доступные инструменты:")
            for tool in _amap_mcp_tool._available_tools[:5]:  # Распечатайте только первые 5
                print(f"     - {tool.get('name', 'unknown')}")
            if len(_amap_mcp_tool._available_tools) > 5:
                print(f"     ... и инструменты {len(_amap_mcp_tool._available_tools) – 5}")
    
    return _amap_mcp_tool


class AmapService:
    """Класс инкапсуляции сервиса Amap"""
    
    def __init__(self):
        """Инициализировать службу"""
        self.mcp_tool = get_amap_mcp_tool()
    
    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[POIInfo]:
        """
        Поиск POI
        
        Аргументы:
            ключевые слова: ключевые слова для поиска
            город: город
            citylimit: ограничивать ли его пределами города
            
        Возврат:
            Список информации о POI
        """
        try:
            # Вызов инструмента MCP
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_text_search",
                "arguments": {
                    "keywords": keywords,
                    "city": city,
                    "citylimit": str(citylimit).lower()
                }
            })
            
            # Результаты анализа
            # Примечание. Инструмент MCP возвращает строку, которую необходимо проанализировать.
            # Здесь обработка упрощена, JSON фактически должен анализироваться.
            print(f"Результаты поиска POI: {result[:200]}...")  # Распечатать первые 200 символов
            
            # ЗАДАЧА: проанализировать фактические данные POI
            return []
            
        except Exception as e:
            print(f"❌ Не удалось найти POI: {str(e)}")
            return []
    
    def get_weather(self, city: str) -> List[WeatherInfo]:
        """
        Проверьте погоду
        
        Аргументы:
            город: название города
            
        Возврат:
            Список информации о погоде
        """
        try:
            # Вызов инструмента MCP
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_weather",
                "arguments": {
                    "city": city
                }
            })
            
            print(f"Результаты запроса погоды: {result[:200]}...")
            
            # ЗАДАЧА: Анализ фактических данных о погоде
            return []
            
        except Exception as e:
            print(f"❌ Ошибка запроса погоды: {str(e)}")
            return []
    
    def plan_route(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        route_type: str = "walking"
    ) -> Dict[str, Any]:
        """
        Спланировать маршрут
        
        Аргументы:
            origin_address: исходный адрес
            Destination_address: адрес назначения
            origin_city: стартовый город
            Destination_city: город назначения
            route_type: тип маршрута (пешеходный/автомобильный/транзитный)
            
        Возврат:
            информация о маршруте
        """
        try:
            # Выбор инструментов в зависимости от типа маршрута
            tool_map = {
                "walking": "maps_direction_walking_by_address",
                "driving": "maps_direction_driving_by_address",
                "transit": "maps_direction_transit_integrated_by_address"
            }
            
            tool_name = tool_map.get(route_type, "maps_direction_walking_by_address")
            
            # Параметры сборки
            arguments = {
                "origin_address": origin_address,
                "destination_address": destination_address
            }
            
            # Общественный транспорт требует городских параметров
            if route_type == "transit":
                if origin_city:
                    arguments["origin_city"] = origin_city
                if destination_city:
                    arguments["destination_city"] = destination_city
            else:
                # Другие типы маршрутов также могут предоставлять параметры города для повышения точности.
                if origin_city:
                    arguments["origin_city"] = origin_city
                if destination_city:
                    arguments["destination_city"] = destination_city
            
            # Вызов инструмента MCP
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": tool_name,
                "arguments": arguments
            })
            
            print(f"Результаты планирования маршрута: {result[:200]}...")
            
            # TODO: проанализировать фактические данные маршрута
            return {}
            
        except Exception as e:
            print(f"❌ Не удалось спланировать маршрут: {str(e)}")
            return {}
    
    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """
        Геокодирование (адрес по координатам)

        Аргументы:
            адрес: адрес
            город: город

        Возврат:
            Координаты широты и долготы
        """
        try:
            arguments = {"address": address}
            if city:
                arguments["city"] = city

            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_geo",
                "arguments": arguments
            })

            print(f"Результаты геокодирования: {result[:200]}...")

            # TODO: проанализировать фактические данные координат
            return None

        except Exception as e:
            print(f"❌ Ошибка геокодирования: {str(e)}")
            return None

    def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """
        Получить подробную информацию о POI

        Аргументы:
            poi_id: идентификатор POI

        Возврат:
            Детали POI
        """
        try:
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_search_detail",
                "arguments": {
                    "id": poi_id
                }
            })

            print(f"Подробные результаты POI: {result[:200]}...")

            # Анализ результатов и извлечение изображений
            import json
            import re

            # Попробуйте извлечь JSON из результата
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data

            return {"raw": result}

        except Exception as e:
            print(f"❌ Не удалось получить сведения о POI: {str(e)}.")
            return {}


# Создайте глобальный экземпляр службы
_amap_service = None


def get_amap_service() -> AmapService:
    """Получить экземпляр службы Amap (одиночный режим)"""
    global _amap_service
    
    if _amap_service is None:
        _amap_service = AmapService()
    
    return _amap_service

