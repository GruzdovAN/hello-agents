"""Шаг 1: клиент LLM — совместим с интерфейсом OpenAI и поддерживает потоковую передачу ответов"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()


class HelloAgentsLLM:
    def __init__(self, model: str = None, apiKey: str = None,
                 baseUrl: str = None, timeout: int = None):
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))

        if not all([self.model, apiKey, baseUrl]):
поднять ValueError("Пожалуйста, настройте LLM_MODEL_ID, LLM_API_KEY, LLM_BASE_URL в .env")

        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
print(f"\n[{self.model}] Думаю...")
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages,
                temperature=temperature, stream=True,
            )
            collected = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
# Фильтровать недопустимые суррогатные символы (суррогаты)
                clean = content.encode("utf-8", errors="surrogateescape").decode("utf-8", errors="replace")
                print(clean, end="", flush=True)
                collected.append(clean)
            print()
            result = "".join(collected)
            return result
        except Exception as e:
print(f"[ERR] Ошибка вызова LLM: {e}")
# Попробуйте повторить попытку без потоковой передачи
            try:
print("Попробуйте повторную попытку без потоковой передачи...")
                response = self.client.chat.completions.create(
                    model=self.model, messages=messages,
                    temperature=temperature, stream=False,
                )
                content = response.choices[0].message.content or ""
                clean = content.encode("utf-8", errors="surrogateescape").decode("utf-8", errors="replace")
                print(clean)
                return clean
            except Exception as e2:
print(f"[ERR] Непотоковая передача также не удалась: {e2}")
                raise RuntimeError(f"LLM调用完全失败: {e2}")
