from typing import Any, Dict

from app.config import settings
from app.prompts.standard_prompt import STANDARD_PROMPT
from app.services.llm_service import LLMService
from app.tools.mermaid_validator_tool import MermaidValidatorTool

from .agent_factory import build_agent
from .code_utils import extract_mermaid, extract_optimized_text


class MermaidPipeline:
    def __init__(self, validator: MermaidValidatorTool):
        self.validator = validator

    def generate_once(self, mode: str, prompt: str) -> str:
        agent = build_agent(mode, self.validator)
        agent.clear_history()
        result_text = agent.run(prompt)
        return extract_mermaid(result_text)

    def generate_standard(self, prompt: str) -> Dict[str, str]:
        optimize_messages = [
            {
                "role": "system",
                "content": (
                    STANDARD_PROMPT
                    + "\nДополнительное требование: сейчас выполняется только [Шаг 1: оптимизация текста]. "
                    "Выводите только полный оптимизированный текст, без заголовков, без кода Mermaid и без блоков кода."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        optimized_resp = LLMService.create_llm().invoke(optimize_messages)
        optimized_text = extract_optimized_text(optimized_resp.content)
        source_text = optimized_text.strip() or (optimized_resp.content or "").strip()

        code_agent = build_agent("standard-code", self.validator)
        code_agent.clear_history()
        raw_code_text = code_agent.run(source_text)

        return {
            "optimized_text": source_text,
            "mermaid_code": extract_mermaid(raw_code_text),
            "generated_from_optimized": bool(source_text),
        }

    def repair_once(self, bad_code: str, reason: str) -> str:
        messages = [
            {"role": "system", "content": "Вы — исправитель Mermaid; выводите только исправленный код Mermaid."},
            {
                "role": "user",
                "content": (
                    "Исправьте следующий код Mermaid, чтобы его можно было отрендерить."
                    f"\nСообщение об ошибке: {reason}\n\nКод:\n{bad_code}"
                ),
            },
        ]
        response = LLMService.create_llm().invoke(messages)
        return extract_mermaid(response.content)

    def post_validate(self, code: str) -> Dict[str, Any]:
        current = code
        attempts = 0
        repair_limit = min(settings.validator_max_retries, 1)

        while attempts <= repair_limit:
            attempts += 1
            result = self.validator.run({"code": current})
            valid = bool(result.data.get("valid"))
            fixed_code = result.data.get("fixed_code", current)

            if valid:
                return {
                    "valid": True,
                    "attempts": attempts,
                    "mermaid_code": fixed_code,
                    "message": "validated",
                }

            if attempts > repair_limit:
                return {
                    "valid": False,
                    "attempts": attempts,
                    "mermaid_code": fixed_code,
                    "message": "; ".join(result.data.get("errors", [])) or "validate failed",
                }

            reason = "; ".join(result.data.get("errors", [])) or "unknown syntax issue"
            current = self.repair_once(fixed_code, reason)

        return {
            "valid": False,
            "attempts": attempts,
            "mermaid_code": current,
            "message": "validate failed",
        }
