from __future__ import annotations

from dataclasses import dataclass
from urllib.request import Request, urlopen
import json
import re


@dataclass(slots=True)
class LLMClient:
    model_name: str
    api_key: str
    base_url: str
    timeout_seconds: int
    json_mode: bool = True

    def is_enabled(self) -> bool:
        return bool(self.model_name and self.api_key and self.base_url)

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self.is_enabled():
            raise RuntimeError("LLM client is not configured. Check .env.")

        payload = {
            "model": self.model_name,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}

        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urlopen(request, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError(f"Unexpected LLM response: {raw}")
            message = choices[0].get("message") or {}
            return (message.get("content") or "").strip()


SUMMARY_SYSTEM_PROMPT = """
Ты редактор технических дайджестов высокого стандарта для читателей, следящих за AI/LLM, инженерной практикой и технологическим бизнесом.

Твоя задача — не дословный перевод, а качественная структурированная карточка для чтения на русском.

Правила:
1. Только JSON, без пояснений снаружи.
2. Для технических статей: проблема, метод, ограничения, инженерный смысл.
3. Для отраслевых: ключевой тезис, основания, бизнес-эффект, возможные искажения.
4. При низкой плотности информации — низкий балл и совет пропустить.
5. Язык естественный, точный, без воды.
6. Ключевые термины по возможности оставляй на английском.
"""


TRANSLATION_SYSTEM_PROMPT = """
Ты технический переводчик-редактор. Переводи англоязычные технические или бизнес-статьи на естественный, точный русский для технической аудитории.

Правила:
1. Ключевые термины — английский оригинал, при первом упоминании краткое пояснение по-русски.
2. Не теряй важные оговорки и выводы.
3. Без лишней литературщины, без искажения смысла.
4. Только JSON.
"""


def build_summary_prompt(title: str, source_name: str, category: str, article_text: str) -> str:
    trimmed = article_text[:14000]
    return f"""
Прочитай статью и выведи один JSON-объект со всеми полями.

Заголовок: {title}
Источник: {source_name}
Категория: {category}

JSON schema:
{{
  "article_type": "Техпрактика | Обновление модели/продукта | Отраслевой комментарий | Бизнес-анализ | Длинное исследование | Новость/анонс",
  "score": целое 0-100,
  "worth_reading": "Читать внимательно | Выборочно | Можно пропустить",
  "one_line": "Одна фраза-вывод, 20-40 слов",
  "summary": "4-6 предложений на русском — о чём статья",
  "key_points": ["3 ключевых пункта"],
  "why_it_matters": "Почему это важно тем, кто следит за AI/LLM и tech-индустрией",
  "engineering_takeaway": "Инженерный вывод для техстатей; для отраслевых — практический вывод для решений",
  "business_signal": "Бизнес-сигнал для продуктов/рынка; иначе краткая отраслевая оценка",
  "limitations": "Что автор мог упустить, границы применимости, слабости материала",
  "keywords": ["3-5 ключевых слов"],
  "recommended_action": "Что делать дальше: читать оригинал / хватит summary / пропустить"
}}

Шкала:
- 85-100: высокая плотность, в приоритете
- 70-84: есть ценность
- 50-69: немного ценности, не срочно
- 0-49: много шума, можно пропустить

Текст статьи:
{trimmed}
"""


def build_translation_prompt(title: str, article_text: str) -> str:
    trimmed = article_text[:16000]
    return f"""
Переведи англоязычную статью на естественный русский для технических читателей.

Вывод JSON:
{{
  "translation": "полный русский перевод"
}}

Требования:
1. Сохрани ключевые тезисы.
2. Термины при первом упоминании — с английским оригиналом.
3. Чёткие абзацы, естественный язык.

Заголовок: {title}

Текст:
{trimmed}
"""


def parse_json_response(text: str) -> dict:
    text = text.strip()
    if not text:
        raise ValueError("Empty LLM response")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))
