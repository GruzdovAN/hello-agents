# my_advanced_search.py
import os
from typing import Optional, List, Dict, Any
from hello_agents import ToolRegistry

class MyAdvancedSearchTool:
    """
    Пользовательский инструмент умного поиска.
    Демонстрирует объединение нескольких источников и выбор лучшего результата.
    """

    def __init__(self):
        self.name = "my_advanced_search"
        self.description = "Умный поиск: несколько источников, автоматический выбор лучшего результата"
        self.search_sources = []
        self._setup_search_sources()

    def _setup_search_sources(self):
        """Настроить доступные источники поиска"""
        # Tavily
        if os.getenv("TAVILY_API_KEY"):
            try:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
                self.search_sources.append("tavily")
                print("✅ Источник Tavily включён")
            except ImportError:
                print("⚠️ Библиотека Tavily не установлена")

        # SerpApi
        if os.getenv("SERPAPI_API_KEY"):
            try:
                import serpapi
                self.search_sources.append("serpapi")
                print("✅ Источник SerpApi включён")
            except ImportError:
                print("⚠️ Библиотека SerpApi не установлена")

        if self.search_sources:
            print(f"🔧 Доступные источники: {', '.join(self.search_sources)}")
        else:
            print("⚠️ Нет доступных источников — настройте API-ключи")

    def search(self, query: str) -> str:
        """Выполнить умный поиск"""
        if not query.strip():
            return "❌ Ошибка: поисковый запрос не может быть пустым"

        if not self.search_sources:
            return """❌ Нет доступных источников. Настройте один из API-ключей:

1. Tavily API: переменная окружения TAVILY_API_KEY
   Получить: https://tavily.com/

2. SerpAPI: переменная окружения SERPAPI_API_KEY
   Получить: https://serpapi.com/

После настройки перезапустите программу."""

        print(f"🔍 Умный поиск: {query}")

        # Перебор источников, вернуть лучший результат
        for source in self.search_sources:
            try:
                if source == "tavily":
                    result = self._search_with_tavily(query)
                    if result and "не найдено" not in result.lower() and "не найдено" not in result:
                        return f"📊 Результат Tavily AI:\n\n{result}"

                elif source == "serpapi":
                    result = self._search_with_serpapi(query)
                    if result and "не найдено" not in result.lower() and "не найдено" not in result:
                        return f"🌐 Результат SerpApi Google:\n\n{result}"

            except Exception as e:
                print(f"⚠️ Поиск через {source} не удался: {e}")
                continue

        return "❌ Все источники поиска недоступны. Проверьте сеть и API-ключи."

    def _search_with_tavily(self, query: str) -> str:
        """Поиск через Tavily"""
        response = self.tavily_client.search(query=query, max_results=3)

        if response.get('answer'):
            result = f"💡 Прямой ответ ИИ: {response['answer']}\n\n"
        else:
            result = ""

        result += "🔗 Связанные результаты:\n"
        for i, item in enumerate(response.get('results', [])[:3], 1):
            result += f"[{i}] {item.get('title', '')}\n"
            result += f"    {item.get('content', '')[:150]}...\n\n"

        return result

    def _search_with_serpapi(self, query: str) -> str:
        """Поиск через SerpApi"""
        import serpapi

        search = serpapi.GoogleSearch({
            "q": query,
            "api_key": os.getenv("SERPAPI_API_KEY"),
            "num": 3
        })

        results = search.get_dict()

        result = "🔗 Результаты Google:\n"
        if "organic_results" in results:
            for i, res in enumerate(results["organic_results"][:3], 1):
                result += f"[{i}] {res.get('title', '')}\n"
                result += f"    {res.get('snippet', '')}\n\n"

        return result

def create_advanced_search_registry():
    """Создать реестр с инструментом расширенного поиска"""
    registry = ToolRegistry()

    search_tool = MyAdvancedSearchTool()

    registry.register_function(
        name="advanced_search",
        description="Расширенный поиск: объединяет Tavily и SerpAPI для более полных результатов",
        func=search_tool.search
    )

    return registry
