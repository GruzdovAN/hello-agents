import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

# Загрузить переменные окружения из .env
load_dotenv()

class HelloAgentsLLM:
    """
    LLM-клиент для книги «Hello Agents».
    Вызывает любой OpenAI-совместимый сервис; по умолчанию — потоковый ответ.
    """
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        """
        Инициализация. Сначала параметры конструктора, иначе — переменные окружения.
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("Нужны model id, API-ключ и base URL — в аргументах или в .env.")

        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        Запросить рассуждение у LLM и вернуть полный текст ответа.
        """
        print(f"🧠 Вызов модели {self.model}...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            # Обработка потокового ответа
            print("✅ Ответ LLM получен:")
            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print()  # перевод строки после стрима
            return "".join(collected_content)

        except Exception as e:
            print(f"❌ Ошибка вызова LLM API: {e}")
            return None

# --- Пример использования клиента ---
if __name__ == '__main__':
    try:
        llmClient = HelloAgentsLLM()
        
        exampleMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "Напиши алгоритм быстрой сортировки"}
        ]
        
        print("--- Вызов LLM ---")
        responseText = llmClient.think(exampleMessages)
        if responseText:
            print("\n\n--- Полный ответ модели ---")
            print(responseText)

    except ValueError as e:
        print(e)
