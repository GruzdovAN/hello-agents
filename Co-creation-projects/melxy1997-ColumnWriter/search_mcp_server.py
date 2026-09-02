"""MCP-сервер поиска для агента"""

import os
from typing import Optional
try:
    from fastmcp import FastMCP
except ImportError:
    print("▸️  Установите fastmcp: pip install fastmcp")
    exit(1)

mcp = FastMCP("search-server")


@mcp.tool()
def web_search(query: str, max_results: int = 3) -> str:
    """
    Инструмент поиска в интернете

    Args:
        query: поисковый запрос
        max_results: число результатов (по умолчанию 3)

    Returns:
        Сводка результатов поиска
    """
    print(f"▸ Поиск: {query}")

    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            response = client.search(query=query, max_results=max_results)

            result = ""
            if response.get('answer'):
                result += f"▸ AI-ответ: {response['answer']}\n\n"

            result += "▸ Релевантные результаты:\n"
            for i, item in enumerate(response.get('results', [])[:max_results], 1):
                result += f"[{i}] {item.get('title', '')}\n"
                result += f"    {item.get('content', '')[:200]}...\n"
                result += f"    Источник: {item.get('url', '')}\n\n"

            return result
        except Exception as e:
            print(f"▸️  Ошибка Tavily: {e}")

    serpapi_key = os.getenv("SERPAPI_API_KEY")
    if serpapi_key:
        try:
            from serpapi import GoogleSearch

            search = GoogleSearch({
                "q": query,
                "api_key": serpapi_key,
                "num": max_results,
                "gl": "ru",
                "hl": "ru"
            })

            results = search.get_dict()

            result = "▸ Результаты поиска:\n"

            if "answer_box" in results and "answer" in results["answer_box"]:
                result += f"▸ Прямой ответ: {results['answer_box']['answer']}\n\n"

            if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
                result += f"▸ Knowledge graph: {results['knowledge_graph']['description']}\n\n"

            if "organic_results" in results:
                for i, res in enumerate(results["organic_results"][:max_results], 1):
                    result += f"[{i}] {res.get('title', '')}\n"
                    result += f"    {res.get('snippet', '')}\n"
                    result += f"    {res.get('link', '')}\n\n"

            return result
        except Exception as e:
            print(f"▸️  Ошибка SerpAPI: {e}")

    return """▸ Поиск недоступен. Настройте один из API-ключей:

1. Tavily API (рекомендуется)
   - Переменная окружения: TAVILY_API_KEY
   - Получить: https://tavily.com/
   - Установка: pip install tavily-python

2. SerpAPI
   - Переменная окружения: SERPAPI_API_KEY
   - Получить: https://serpapi.com/
   - Установка: pip install google-search-results

Перезапустите систему после настройки."""


@mcp.tool()
def search_recent_info(topic: str) -> str:
    """
    Поиск актуальной информации (новости, обновления)

    Args:
        topic: тема поиска

    Returns:
        Сводка актуальной информации
    """
    query = f"{topic} latest 2024"
    return web_search(query, max_results=3)


@mcp.tool()
def search_code_examples(technology: str, task: str) -> str:
    """
    Поиск примеров кода

    Args:
        technology: стек (Python, JavaScript)
        task: описание задачи

    Returns:
        Примеры кода и пояснения
    """
    query = f"{technology} {task} code example tutorial"
    return web_search(query, max_results=3)


@mcp.tool()
def verify_facts(statement: str) -> str:
    """
    Проверка фактов

    Args:
        statement: утверждение для проверки

    Returns:
        Результат проверки
    """
    query = f"{statement} fact check"
    return web_search(query, max_results=3)


if __name__ == "__main__":
    print("▸ Запуск MCP-сервера поиска...")
    print("   Инструменты: web_search, search_recent_info, search_code_examples, verify_facts")
    mcp.run()
