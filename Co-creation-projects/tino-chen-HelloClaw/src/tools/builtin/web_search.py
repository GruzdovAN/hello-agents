"""Инструмент веб-поиска — поиск в Интернете с помощью API Brave Search."""

import os
import json
from typing import List, Dict, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from hello_agents.tools import Tool, ToolParameter, ToolResponse, tool_action


class WebSearchTool(Tool):
    """Инструмент веб-поиска

    Используйте Brave Search API для выполнения веб-поиска.
    Вам необходимо настроить переменную среды BRAVE_API_KEY или передать ключ API во время инициализации."""

    def __init__(
        self,
        api_key: str = None,
        max_results: int = 5,
        timeout: int = 10,
    ):
        """Инициализировать инструмент веб-поиска

        Аргументы:
            api_key: API-ключ Brave Search. Если он не указан, он будет прочитан из переменной среды BRAVE_API_KEY.
            max_results: максимальное количество возвращаемых результатов, по умолчанию 5.
            таймаут: таймаут запроса (секунды), по умолчанию 10"""
        super().__init__(
            name="web_search",
            description="Веб-поиск",
            expandable=True
        )

        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        self.max_results = max_results
        self.timeout = timeout
        self._base_url = "https://api.search.brave.com/res/v1/web/search"

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        """Выполнить поиск (поведение по умолчанию)"""
        query = parameters.get("query", "")
        count = parameters.get("count", self.max_results)
        return self._search(query, count)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
description="Поискслового запроса",
                required=True
            ),
            ToolParameter(
                name="count",
                type="integer",
                description=f"返回结果数量，по умолчанию {self.max_results}",
                required=False
            ),
        ]

    def _search(self, query: str, count: int = None) -> ToolResponse:
        """Основная реализация для выполнения поиска

        Аргументы:
            запрос: поисковый запрос
            count: количество возвращенных результатов

        Возврат:
            ToolResponse: Результаты поиска"""
        if not query:
            return ToolResponse.error(
                code="INVALID_INPUT",
                message="Поиск查询не может быть пустым"
            )

        if not self.api_key:
            return ToolResponse.error(
                code="MISSING_API_KEY",
message="неконфигурация Brave API Key. Пожалуйста, установите переменную среды BRAVE_API_KEY или передайте параметр api_key во время инициализации"
            )

        try:
            # Запрос на сборку

            params = {
                "q": query,
                "count": count or self.max_results,
            }

            url = f"{self._base_url}?q={query}&count={params['count']}"
            request = Request(url)
            request.add_header("Accept", "application/json")
            request.add_header("Accept-Encoding", "gzip")
            request.add_header("X-Subscription-Token", self.api_key)

            # Отправить запрос

            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))

            # Результаты анализа

            results = self._parse_search_results(data)

            if not results:
                return ToolResponse.success(
                    text=f"Не найдено совпадений для '{query}' 相关的结果",
                    data={"query": query, "results": []}
                )

            # Форматированный вывод

            formatted = self._format_results(results)

            return ToolResponse.success(
                text=formatted,
                data={
                    "query": query,
                    "results": results,
                    "count": len(results),
                }
            )

        except HTTPError as e:
            if e.code == 401:
                return ToolResponse.error(
                    code="AUTH_ERROR",
                    message="API Key недопустимый或ужеустаревший"
                )
            elif e.code == 429:
                return ToolResponse.error(
                    code="RATE_LIMIT",
                    message="API запрос频率超限，Пожалуйста,稍后再试"
                )
            else:
                return ToolResponse.error(
                    code="HTTP_ERROR",
                    message=f"Поискзапросошибка (HTTP {e.code}): {e.reason}"
                )
        except URLError as e:
            return ToolResponse.error(
                code="NETWORK_ERROR",
                message=f"Сетевая ошибка: {str(e)}"
            )
        except Exception as e:
            return ToolResponse.error(
                code="SEARCH_ERROR",
                message=f"Поискошибка: {str(e)}"
            )

    def _parse_search_results(self, data: dict) -> List[dict]:
        """Анализ ответов Brave Search API

        Аргументы:
            данные: данные ответа API

        Возврат:
            Список результатов поиска"""
        results = []

        # Извлечение результатов веб-поиска

        web_results = data.get("web", {}).get("results", [])

        for item in web_results:
            result = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
            }
            results.append(result)

        return results

    def _format_results(self, results: List[dict]) -> str:
        """Форматировать результаты поиска

        Аргументы:
            результаты: список результатов поиска

        Возврат:
            форматированный текст"""
        lines = [f"Найдено {len(results)} 个结果:\n"]

        for i, result in enumerate(results, 1):
            lines.append(f"{i}. **{result['title']}**")
            lines.append(f"   URL: {result['url']}")
            if result['description']:
                lines.append(f"   {result['description'][:200]}")
            lines.append("")

        return "\n".join(lines)

@tool_action("search_web", "Информация о поисковой сети")
    def _search_action(self, query: str, count: int = None) -> str:
        """Поиск в Интернете

        Аргументы:
            запрос: термин поискового запроса
            count: количество возвращенных результатов (необязательно)"""
        response = self._search(query, count)
        return response.text
