from dotenv import load_dotenv
# Загрузить переменные окружения из .env
load_dotenv()

import os
from serpapi import SerpApiClient
from typing import Dict, Any

def search(query: str) -> str:
    """
    Практический инструмент веб-поиска на базе SerpApi.
    Разбирает выдачу и по возможности возвращает прямой ответ или данные knowledge graph.
    """
    print(f"🔍 Выполняется веб-поиск [SerpApi]: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "Ошибка: SERPAPI_API_KEY не задан в файле .env."

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # код страны
            "hl": "zh-cn", # код языка
        }
        
        client = SerpApiClient(params)
        results = client.get_dict()
        
        # Приоритет самым прямым ответам
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # Нет прямого ответа — краткие выдержки из топ-3 органических результатов
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        
        return f"К сожалению, по запросу '{query}' ничего не найдено."

    except Exception as e:
        return f"Ошибка при поиске: {e}"
    
from typing import Dict, Any

class ToolExecutor:
    """
    Исполнитель инструментов: регистрирует и вызывает tool-функции.
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        """
        Зарегистрировать новый инструмент в наборе.
        """
        if name in self.tools:
            print(f"Предупреждение: инструмент '{name}' уже есть и будет перезаписан.")
        
        self.tools[name] = {"description": description, "func": func}
        print(f"Инструмент '{name}' зарегистрирован.")

    def getTool(self, name: str) -> callable:
        """
        Получить callable инструмента по имени.
        """
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """
        Отформатированное описание всех доступных инструментов.
        """
        return "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])


# --- Инициализация и пример использования ---
if __name__ == '__main__':
    # 1. Инициализация исполнителя
    toolExecutor = ToolExecutor()

    # 2. Регистрация боевого поискового инструмента
    search_description = "Веб-поисковик. Используй, когда нужны актуальные факты или сведения, которых нет в твоей базе знаний."
    toolExecutor.registerTool("Search", search_description, search)
    
    # 3. Список доступных инструментов
    print("\n--- Доступные инструменты ---")
    print(toolExecutor.getAvailableTools())

    # 4. Пример Action агента — актуальный вопрос
    print("\n--- Выполнение Action: Search['Какая последняя модель GPU у NVIDIA'] ---")
    tool_name = "Search"
    tool_input = "Какая последняя модель GPU у NVIDIA"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- Наблюдение (Observation) ---")
        print(observation)
    else:
        print(f"Ошибка: инструмент '{tool_name}' не найден.")
