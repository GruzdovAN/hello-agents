"""Общие утилиты"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List


class JSONExtractor:
    """
    Универсальный извлекатель JSON

    Извлекает JSON из ответов LLM:
    - чистый JSON
    - JSON в Markdown-блоках
    - формат Finish[...] (ReAct)
    - JSON в смешанном тексте
    """

    @staticmethod
    def extract(
        response: str,
        required_fields: Optional[List[str]] = None,
        fallback_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Извлечь JSON из ответа

        Args:
            response: текст ответа LLM
            required_fields: обязательные поля для проверки и приоритета
            fallback_fields: значения по умолчанию при отсутствии полей

        Returns:
            извлечённый dict JSON

        Raises:
            ValueError: если валидный JSON не найден
        """
        if not response or not response.strip():
            raise ValueError("Пустой ответ")

        fallback_fields = fallback_fields or {}
        required_fields = required_fields or []

        extractors = [
            JSONExtractor._extract_from_finish,
            JSONExtractor._extract_direct_json,
            JSONExtractor._extract_from_markdown_json,
            JSONExtractor._extract_from_markdown,
            JSONExtractor._extract_from_braces,
        ]

        last_error = None
        for extractor in extractors:
            try:
                result = extractor(response)
                if result is not None:
                    for key, default_value in fallback_fields.items():
                        if key not in result:
                            result[key] = default_value

                    if required_fields:
                        missing = [f for f in required_fields if f not in result]
                        if not missing:
                            return result
                    else:
                        return result
            except Exception as e:
                last_error = e
                continue

        try:
            result = JSONExtractor._extract_from_history(response)
            if result is not None:
                for key, default_value in fallback_fields.items():
                    if key not in result:
                        result[key] = default_value
                return result
        except Exception as e:
            last_error = e

        raise ValueError(f"В ответе не найден валидный JSON: {last_error}")

    @staticmethod
    def _extract_from_finish(response: str) -> Optional[Dict[str, Any]]:
        """Извлечение из Finish[...]"""
        match = re.search(r"Finish\[(.*)\]", response, re.DOTALL)
        if match:
            content = match.group(1).strip()
            return JSONExtractor._parse_json_with_retry(content)
        return None

    @staticmethod
    def _extract_direct_json(response: str) -> Optional[Dict[str, Any]]:
        """Прямой парсинг JSON"""
        stripped = response.strip()
        if stripped.startswith('{'):
            return JSONExtractor._parse_json_with_retry(stripped)
        return None

    @staticmethod
    def _extract_from_markdown_json(response: str) -> Optional[Dict[str, Any]]:
        """Из блока ```json"""
        if "```json" not in response:
            return None

        json_start = response.find("```json") + 7
        json_end = response.find("```", json_start)
        if json_end == -1:
            return None

        json_str = response[json_start:json_end].strip()
        return JSONExtractor._parse_json_with_retry(json_str)

    @staticmethod
    def _extract_from_markdown(response: str) -> Optional[Dict[str, Any]]:
        """Из обычного блока ```"""
        if "```" not in response:
            return None

        json_start = response.find("```") + 3
        json_end = response.find("```", json_start)
        if json_end == -1:
            return None

        json_str = response[json_start:json_end].strip()
        if json_str.startswith("json"):
            json_str = json_str[4:].strip()

        if json_str.startswith('{'):
            return JSONExtractor._parse_json_with_retry(json_str)
        return None

    @staticmethod
    def _extract_from_braces(response: str) -> Optional[Dict[str, Any]]:
        """Все JSON-объекты из фигурных скобок"""
        json_candidates = []
        i = 0

        while i < len(response):
            if response[i] == '{':
                brace_count = 0
                brace_start = i
                brace_end = i

                for j in range(i, len(response)):
                    if response[j] == '{':
                        brace_count += 1
                    elif response[j] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            brace_end = j + 1
                            break

                if brace_end > brace_start:
                    json_str = response[brace_start:brace_end]
                    try:
                        parsed = JSONExtractor._parse_json_with_retry(json_str)
                        if isinstance(parsed, dict):
                            json_candidates.append((parsed, len(parsed)))
                    except Exception:
                        pass
                    i = brace_end
                else:
                    i += 1
            else:
                i += 1

        if json_candidates:
            for parsed, _ in json_candidates:
                if 'content' in parsed and parsed.get('content'):
                    return parsed

            return max(json_candidates, key=lambda x: x[1])[0]

        return None

    @staticmethod
    def _extract_from_history(response: str) -> Optional[Dict[str, Any]]:
        """Из формата истории (PlanAndSolve)"""
        if "шаг" not in response.casefold() and "результат" not in response.casefold():
            return None

        json_matches = re.findall(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if not json_matches:
            json_matches = re.findall(r'(\{"column_title".*?"topics".*?\})', response, re.DOTALL)

        for json_str in json_matches:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue

        return None

    @staticmethod
    def _parse_json_with_retry(json_str: str) -> Dict[str, Any]:
        """Несколько способов парсинга JSON"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        fixed = json_str.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        result = JSONExtractor._rebuild_json_from_fields(json_str)
        if result:
            return result

        raise json.JSONDecodeError("Не удалось распарсить JSON", json_str, 0)

    @staticmethod
    def _rebuild_json_from_fields(json_str: str) -> Optional[Dict[str, Any]]:
        """Реконструкция JSON из полей"""
        title_match = re.search(r'"title"\s*:\s*"([^"]*)"', json_str)
        level_match = re.search(r'"level"\s*:\s*(\d+)', json_str)
        word_count_match = re.search(r'"word_count"\s*:\s*(\d+)', json_str)
        needs_expansion_match = re.search(r'"needs_expansion"\s*:\s*(true|false)', json_str)

        content_match = re.search(r'"content"\s*:\s*"(.*?)"(?=\s*[,}])', json_str, re.DOTALL)
        if not content_match:
            content_match = re.search(r'"content"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', json_str, re.DOTALL)

        if not any([title_match, level_match, content_match]):
            return None

        result = {}
        if title_match:
            result['title'] = title_match.group(1)
        if level_match:
            result['level'] = int(level_match.group(1))
        if content_match:
            content = content_match.group(1)
            content = content.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
            result['content'] = content
        if word_count_match:
            result['word_count'] = int(word_count_match.group(1))
        else:
            result['word_count'] = len(result.get('content', ''))
        if needs_expansion_match:
            result['needs_expansion'] = needs_expansion_match.group(1) == 'true'
        else:
            result['needs_expansion'] = False

        result.setdefault('subsections', [])
        result.setdefault('metadata', {})

        return result


def parse_react_output(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Парсинг вывода ReAct Agent

    Форматы:
    - ReAct: Thought: ... Action: ...
    - русский: Рассуждение: ... Действие: ...
    - Finish[...]

    Args:
        text: сырой ответ LLM

    Returns:
        (thought, action)
    """
    if not text or not text.strip():
        print("▸️  Внимание: LLM вернул пустой ответ")
        return None, None

    thought = None
    thought_end_pos = 0
    thought_patterns = [
        r"Thought:\s*(.*?)(?=\nAction:|\nFinish:|$)",
        r"Рассуждение:\s*(.*?)(?=\nДействие:|\nГотово:|$)",
    ]

    for pattern in thought_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            thought = match.group(1).strip()
            if thought:
                thought_end_pos = match.end()
                break

    action = None
    action_patterns = [
        r"Action:\s*(.*?)(?=\nThought:|\nObservation:|\nFinish:|$)",
        r"Действие:\s*(.*?)(?=\nРассуждение:|\nНаблюдение:|\nГотово:|$)",
        r"Finish\[(.*?)\]",
    ]

    for pattern in action_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            action = match.group(1).strip()
            if action:
                if pattern == r"Finish\[(.*?)\]":
                    action = f"Finish[{action}]"
                break

    if not action:
        finish_patterns = [
            r"Finish\s*\[(.*?)\]",
            r"Готово\s*\[(.*?)\]",
            r"Финальный ответ:\s*(.*?)(?=\n|$)",
        ]
        for pattern in finish_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:
                    action = f"Finish[{content}]"
                    break

    if not action:
        action = _try_extract_complete_content(text, thought, thought_end_pos)

    if not action:
        print(f"▸️  Внимание: не удалось распарсить Action")
        print(f"   Ответ (первые 500 символов): {text[:500]}")
        print(f"   Thought: {thought[:100] if thought else 'None'}...")

    return thought, action


def _try_extract_complete_content(
    text: str,
    thought: Optional[str],
    thought_end_pos: int
) -> Optional[str]:
    """
    Извлечь полный контент и обернуть в Finish

    Args:
        text: исходный текст
        thought: распознанный thought
        thought_end_pos: позиция конца thought

    Returns:
        action или None
    """
    json_match = None
    brace_start = text.find('{')
    if brace_start != -1:
        brace_end = text.rfind('}')
        if brace_end > brace_start:
            potential_json = text[brace_start:brace_end + 1]
            if '"content"' in potential_json or "'content'" in potential_json:
                json_match = re.search(r'\{.*?"content".*?\}', potential_json, re.DOTALL)

    if thought:
        remaining_text = text[thought_end_pos:].strip()
        if not remaining_text:
            remaining_text = thought
    else:
        remaining_text = text.strip()

    remaining_text = re.sub(
        r'^(Action|Finish|Действие|Готово)[:：]\s*',
        '',
        remaining_text,
        flags=re.IGNORECASE,
    )

    if not remaining_text and not json_match:
        return None

    if json_match:
        remaining_text = json_match.group(0)
        json_str = remaining_text
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        json_complete = (open_braces == close_braces) and open_braces > 0
    else:
        json_complete = False
        json_match_check = re.search(r'\{.*?"content".*?\}', remaining_text, re.DOTALL)
        if json_match_check:
            json_str = json_match_check.group(0)
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            json_complete = (open_braces == close_braces) and open_braces > 0

    has_ending = bool(re.search(
        r'(итог|конец|заключение|в конце|end|conclusion)',
        remaining_text[-500:] if len(remaining_text) > 500 else remaining_text,
        re.IGNORECASE
    ))
    has_continuation = bool(re.search(
        r'(продолжение следует|to be continued)',
        remaining_text,
        re.IGNORECASE
    ))

    content_length = len(remaining_text)
    is_substantial = content_length > 200

    is_complete = False
    completion_reason = []

    if json_complete:
        is_complete = True
        completion_reason.append("полная JSON-структура")
    elif has_ending:
        is_complete = True
        completion_reason.append("маркер конца")
    elif is_substantial and not has_continuation:
        is_complete = True
        completion_reason.append("достаточная длина без маркера продолжения")

    if is_complete:
        print(f"▸ Полный текст ({content_length} симв.), добавлен префикс Finish")
        print(f"   - Основание: {', '.join(completion_reason)}")
        return f"Finish[{remaining_text}]"
    else:
        print(f"▸️  Частичный текст ({content_length} симв.), возможно не завершён")
        if has_continuation:
            print(f"   - Маркер продолжения; цикл для завершения")
        elif not is_substantial:
            print(f"   - Недостаточная длина; цикл для завершения")
        return None


def get_current_timestamp() -> str:
    """Текущая timestamp (ISO)"""
    return datetime.now().isoformat()
