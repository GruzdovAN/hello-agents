"""Инструмент поиска — нативная реализация поиска HelloAgents"""

import os
from typing import Optional, Dict, Any, List

from ..base import Tool, ToolParameter

class SearchTool(Tool):
    """
    Интеллектуальный гибридный поиск

    Поддерживает несколько бэкендов и выбирает лучший источник:
    1. Гибридный режим (hybrid) — TAVILY или SERPAPI
    2. Tavily API (tavily) — поиск с оптимизацией под ИИ
    3. SerpApi (serpapi) — классический Google-поиск
    """

    def __init__(self, backend: str = "hybrid", tavily_key: Optional[str] = None, serpapi_key: Optional[str] = None):
        super().__init__(
            name="search",
            description=(
                "Интеллектуальный веб-поиск. Поддерживает гибридный режим с автоматическим выбором источника. "
                "Используйте, когда нужны актуальные факты, события или информация, отсутствующая в базе знаний."
            )
        )
        self.backend = backend
        self.tavily_key = tavily_key or os.getenv("TAVILY_API_KEY")
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_API_KEY")
        self.available_backends = []
        self._setup_backends()

    def _setup_backends(self):
        """Настраивает бэкенды поиска"""
        # Проверка доступности Tavily
        if self.tavily_key:
            try:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=self.tavily_key)
                self.available_backends.append("tavily")
                print("✅ Поисковый движок Tavily инициализирован")
            except ImportError:
                print("⚠️ Tavily не установлен, поиск через Tavily недоступен")
        else:
            print("⚠️ TAVILY_API_KEY не задан")

        # Проверка доступности SerpApi
        if self.serpapi_key:
            try:
                import serpapi
                self.available_backends.append("serpapi")
                print("✅ Поисковый движок SerpApi инициализирован")
            except ImportError:
                print("⚠️ SerpApi не установлен, поиск через SerpApi недоступен")
        else:
            print("⚠️ SERPAPI_API_KEY не задан")

        # Определение итогового бэкенда
        if self.backend == "hybrid":
            if self.available_backends:
                print(f"🔧 Гибридный режим включён, доступные бэкенды: {', '.join(self.available_backends)}")
            else:
                print("⚠️ Нет доступных бэкендов поиска, настройте API-ключи")
        elif self.backend == "tavily" and "tavily" not in self.available_backends:
            print("⚠️ Tavily недоступен, проверьте TAVILY_API_KEY")
        elif self.backend == "serpapi" and "serpapi" not in self.available_backends:
            print("⚠️ SerpApi недоступен, проверьте SERPAPI_API_KEY")
        elif self.backend not in ["tavily", "serpapi", "hybrid"]:
            print("⚠️ Неподдерживаемый бэкенд, будет использован hybrid")
            self.backend = "hybrid"

    def run(self, parameters: Dict[str, Any]) -> str:
        """
        Выполняет поиск

        Args:
            parameters: словарь с параметром input

        Returns:
            Результаты поиска
        """
        query = parameters.get("input", "").strip()
        if not query:
            return "Ошибка: поисковый запрос не может быть пустым"

        print(f"🔍 Выполняется поиск: {query}")

        try:
            if self.backend == "hybrid":
                return self._search_hybrid(query)
            elif self.backend == "tavily":
                if "tavily" not in self.available_backends:
                    return self._get_api_config_message()
                return self._search_tavily(query)
            elif self.backend == "serpapi":
                if "serpapi" not in self.available_backends:
                    return self._get_api_config_message()
                return self._search_serpapi(query)
            else:
                return self._get_api_config_message()
        except Exception as e:
            return f"Ошибка при поиске: {str(e)}"

    def _search_hybrid(self, query: str) -> str:
        """Гибридный поиск — выбор лучшего источника"""
        if not self.available_backends:
            return self._get_api_config_message()

        # Сначала Tavily (поиск, оптимизированный под ИИ)
        if "tavily" in self.available_backends:
            try:
                print("🎯 Поиск через Tavily (ИИ-оптимизация)")
                return self._search_tavily(query)
            except Exception as e:
                print(f"⚠️ Поиск Tavily не удался: {e}")
                if "serpapi" in self.available_backends:
                    print("🔄 Переключение на SerpApi")
                    return self._search_serpapi(query)

        elif "serpapi" in self.available_backends:
            try:
                print("🎯 Поиск через SerpApi (Google)")
                return self._search_serpapi(query)
            except Exception as e:
                print(f"⚠️ Поиск SerpApi не удался: {e}")

        return "❌ Все источники поиска недоступны, проверьте сеть и API-ключи"

    def _search_tavily(self, query: str) -> str:
        """Поиск через Tavily"""
        response = self.tavily_client.search(
            query=query,
            search_depth="basic",
            include_answer=True,
            max_results=3
        )

        result = f"🎯 Результаты Tavily AI: {response.get('answer', 'прямой ответ не найден')}\n\n"

        for i, item in enumerate(response.get('results', [])[:3], 1):
            result += f"[{i}] {item.get('title', '')}\n"
            result += f"    {item.get('content', '')[:200]}...\n"
            result += f"    Источник: {item.get('url', '')}\n\n"

        return result

    def _search_serpapi(self, query: str) -> str:
        """Поиск через SerpApi"""
        try:
            from serpapi import SerpApiClient
        except ImportError:
            return "Ошибка: SerpApi не установлен, выполните pip install serpapi"

        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_key,
            "gl": "cn",
            "hl": "zh-cn",
        }

        client = SerpApiClient(params)
        results = client.get_dict()

        result_text = "🔍 Результаты SerpApi Google:\n\n"

        if "answer_box" in results and "answer" in results["answer_box"]:
            result_text += f"💡 Прямой ответ: {results['answer_box']['answer']}\n\n"

        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            result_text += f"📖 Граф знаний: {results['knowledge_graph']['description']}\n\n"

        if "organic_results" in results and results["organic_results"]:
            result_text += "🔗 Связанные результаты:\n"
            for i, res in enumerate(results["organic_results"][:3], 1):
                result_text += f"[{i}] {res.get('title', '')}\n"
                result_text += f"    {res.get('snippet', '')}\n"
                result_text += f"    Источник: {res.get('link', '')}\n\n"
            return result_text

        return f"К сожалению, информация по запросу '{query}' не найдена."

    def _get_api_config_message(self) -> str:
        """Возвращает подсказку по настройке API"""
        tavily_key = os.getenv("TAVILY_API_KEY")
        serpapi_key = os.getenv("SERPAPI_API_KEY")

        message = "❌ Нет доступных источников поиска, проверьте конфигурацию:\n\n"

        message += "1. Tavily API:\n"
        if not tavily_key:
            message += "   ❌ Переменная окружения TAVILY_API_KEY не задана\n"
            message += "   📝 Получить ключ: https://tavily.com/\n"
        else:
            try:
                import tavily
                message += "   ✅ API-ключ настроен, пакет установлен\n"
            except ImportError:
                message += "   ❌ API-ключ настроен, но нужен пакет: pip install tavily-python\n"

        message += "\n"

        message += "2. SerpAPI:\n"
        if not serpapi_key:
            message += "   ❌ Переменная окружения SERPAPI_API_KEY не задана\n"
            message += "   📝 Получить ключ: https://serpapi.com/\n"
        else:
            try:
                import serpapi
                message += "   ✅ API-ключ настроен, пакет установлен\n"
            except ImportError:
                message += "   ❌ API-ключ настроен, но нужен пакет: pip install google-search-results\n"

        message += "\nСпособ настройки:\n"
        message += "- Добавьте в .env: TAVILY_API_KEY=your_key_here\n"
        message += "- Или в окружении: export TAVILY_API_KEY=your_key_here\n"
        message += "\nПерезапустите программу после настройки."

        return message

    def get_parameters(self) -> List[ToolParameter]:
        """Возвращает определения параметров инструмента"""
        return [
            ToolParameter(
                name="input",
                type="string",
                description="Ключевые слова поискового запроса",
                required=True
            )
        ]

# Удобные функции
def search(query: str, backend: str = "hybrid") -> str:
    """
    Удобная функция поиска

    Args:
        query: ключевые слова запроса
        backend: бэкенд ("hybrid", "tavily", "serpapi")

    Returns:
        Результаты поиска
    """
    tool = SearchTool(backend=backend)
    return tool.run({"input": query})

def search_tavily(query: str) -> str:
    """Поиск через Tavily с ИИ-оптимизацией"""
    tool = SearchTool(backend="tavily")
    return tool.run({"input": query})

def search_serpapi(query: str) -> str:
    """Поиск через SerpApi (Google)"""
    tool = SearchTool(backend="serpapi")
    return tool.run({"input": query})

def search_hybrid(query: str) -> str:
    """Гибридный поиск с автоматическим выбором источника"""
    tool = SearchTool(backend="hybrid")
    return tool.run({"input": query})
