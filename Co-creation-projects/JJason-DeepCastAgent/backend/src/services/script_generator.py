"""Сервис, конвертирующий исследовательские отчеты в сценарии подкастов."""

from __future__ import annotations

import json
import logging
import re

from openai import OpenAI

from config import Configuration
from models import SummaryState
from prompts import script_writer_instructions

logger = logging.getLogger(__name__)

# Схема JSON для сценария подкаста
SCRIPT_JSON_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "role": {
                "type": "string",
                "enum": ["Host", "Guest"],
                "description": "对话角色，Host 为主持人，Guest 为嘉宾"
            },
            "content": {
                "type": "string",
"description": "Содержимое разговора"
            }
        },
        "required": ["role", "content"]
    },
    "minItems": 6,
    "maxItems": 15
}


class ScriptGenerationService:
"""Создание сценариев бесед на основе исследовательских отчетов (с использованием структурированного вывода)."""

    def __init__(
        self,
        config: Configuration,
        script_agent: OpenAI | None = None,
    ) -> None:
        """
Инициализируйте службу.

        Args:
config: глобальный объект конфигурации.
script_agent: дополнительный пользовательский скрипт для создания клиента/агента.
                如果提供，将直接使用该客户端；否则将基于配置创建默认的 OpenAI 客户端。
        """
        self._config = config
# Предпочитайте использование внедренных пользовательских клиентов для обеспечения обратной совместимости и тестируемости;
# Если не указано, создайте клиент OpenAI по умолчанию на основе конфигурации для поддержки структурированного вывода.
        self._client = script_agent or OpenAI(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
        )
        # 使用 fast_llm_model（ecnu-max）进行脚本生成，它支持结构化输出
        self._model = config.fast_llm_model or "ecnu-max"

    def generate_script(self, state: SummaryState) -> list[dict[str, str]]:
"""Создание сценариев подкастов на основе структурированных отчетов (с использованием структурированного вывода)."""
        if not state.structured_report:
            logger.warning("No structured report available for script generation.")
            return []
        
        report_length = len(state.structured_report)
        logger.info("Generating script from report (%d chars) using structured output...", report_length)

        user_prompt = f"<RESEARCH_REPORT>\n{state.structured_report}\n</RESEARCH_REPORT>"

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": script_writer_instructions.strip()},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=4096,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "podcast_script",
                        "schema": SCRIPT_JSON_SCHEMA
                    },
                },
            )
            
            content = response.choices[0].message.content
            logger.info("Received structured response (%d chars)", len(content) if content else 0)
            
            if not content:
                logger.error("Empty response from LLM")
                return []
            
# Попробуйте проанализировать JSON (решить различные проблемы с форматом)
            script = self._parse_script_json(content)
            
            if script is None:
                return []
            
            if not isinstance(script, list):
                logger.error("Script output is not a list: %s", type(script))
                return []
            
# Проверка и стандартизация
            valid_script = []
            for item in script:
                if isinstance(item, dict) and "role" in item and "content" in item:
                    role = item["role"]
                    content = item["content"]
# Стандартизированные имена ролей
                    if role.lower() in ["host", "xiayu"]:
                        role = "Host"
                    elif role.lower() in ["guest", "liwa"]:
                        role = "Guest"
                    valid_script.append({"role": role, "content": content})
            
            logger.info("Generated script with %d dialogue turns.", len(valid_script))
            return valid_script

        except json.JSONDecodeError as e:
            logger.error("JSON decode error (should not happen with structured output): %s", e)
            return []
        except Exception as e:
            logger.error("Script generation failed: %s", e)
            return []

    def _parse_script_json(self, content: str) -> list | None:
        """
Попробуйте различные способы разбора JSON скрипта.
        
        Args:
контент: исходный контент, возвращаемый LLM.
            
        Returns:
Разобранный список, возвращающий None в случае неудачи
        """
#1. Непосредственно попробовать разобрать
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.debug("Direct JSON parse failed at char %d: %s", e.pos, e.msg)
        
# 2. Попробуйте извлечь блок кода из уценки
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if json_match:
            try:
                result = json.loads(json_match.group(1).strip())
                logger.info("Extracted JSON from markdown code block")
                return result
            except json.JSONDecodeError:
                pass
        
# 3. Извлечь часть массива JSON
        start_idx = content.find('[')
        end_idx = content.rfind(']')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx + 1]
            
№ 3а. Попробуйте напрямую
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.debug("Array extraction failed at char %d: %s", e.pos, e.msg)
# Запишите содержимое рядом с местом ошибки
                error_start = max(0, e.pos - 50)
                error_end = min(len(json_str), e.pos + 50)
                logger.debug("Content around error: ...%s...", json_str[error_start:error_end])
            
№ 3б. Попробуйте исправить распространенные проблемы
            fixed_json = self._fix_json_issues(json_str)
            try:
                result = json.loads(fixed_json)
                logger.info("Parsed JSON after fixing common issues")
                return result
            except json.JSONDecodeError:
                pass
        
# 4. Последняя попытка: разбор объекта за объектом
        result = self._parse_objects_individually(content)
        if result:
            logger.info("Parsed %d objects individually", len(result))
            return result
        
        logger.error("Could not parse JSON from response. First 500 chars: %s", content[:500])
        return None
    
    def _fix_json_issues(self, json_str: str) -> str:
"""Попытайтесь исправить распространенные проблемы с форматом JSON."""
        fixed = json_str
        
# Заменить китайские кавычки английскими кавычками
        fixed = fixed.replace('"', '"').replace('"', '"')
        fixed = fixed.replace(''', "'").replace(''', "'")
        
# Удалить возможные спецификации или другие невидимые символы
        fixed = fixed.strip('\ufeff\u200b\u200c\u200d')
        
# Исправление неэкранированных символов новой строки (внутри строковых значений)
# Это упрощенное решение, которое может быть не идеальным.
        def escape_newlines_in_strings(match):
            return match.group(0).replace('\n', '\\n').replace('\r', '\\r')
        
# Соответствие строковому значению JSON
        fixed = re.sub(r'"[^"]*"', escape_newlines_in_strings, fixed)
        
        return fixed
    
    def _parse_objects_individually(self, content: str) -> list | None:
        """
Попробуйте проанализировать объекты JSON один за другим.
        
Если общий синтаксический анализ не удался, попробуйте извлечь каждый объект {role, content}.
        """
        results = []
        
        # 匹配 {"role": "...", "content": "..."} 模式
# Используйте нежадное сопоставление
        pattern = r'\{\s*"role"\s*:\s*"(Host|Guest)"\s*,\s*"content"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            role = match.group(1)
# Обработка escape-символов
            content_text = match.group(2)
            try:
# Используйте json.loads для правильной обработки экранирования
                content_text = json.loads(f'"{content_text}"')
            except Exception:
                pass
            results.append({"role": role, "content": content_text})
        
        if results:
            return results
        
        return None