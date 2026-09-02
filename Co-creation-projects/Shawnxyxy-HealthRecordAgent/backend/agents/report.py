"""
Агент создания отчетов о состоянии здоровья
"""

import json
from typing import Dict, Any, List
from agents.base import BaseAgent
from core.exceptions import AgentException

class ReportAgent(BaseAgent):
    def __init__(self, task_id=None, llm=None):
        super().__init__(name="ReportAgent",  task_id=task_id, llm=llm)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.set_state("running")

        indicators = input_data.get("indicators", [])
        risk_assessment = input_data.get("risk_assessment", {})
        advice = input_data.get("advice") or {}
        confidence = risk_assessment.get("confidence", 0.5)
извлекаемая_память = str(input_data.get("полученная_память") или "(Пока нет вызванной памяти)")

        advice_list = advice.get("advice", [])

        prompt = self._build_prompt(
            indicators, risk_assessment, advice_list, confidence, retrieved_memory
        )
        response = await self.think(prompt)

        try:
            result = json.loads(response)
            summary = result.get("summary", "根据当前分析生成的健康报告摘要。")
        except json.JSONDecodeError:
            result = {
"summary": "Парсинг не удался, верните исходный результат",
                "raw_response": response
            }

# Построить окончательный отчет
        report = {
"title": "Отчет об оценке личного здоровья",
            "summary": summary,
            "indicator_section": indicators,
            "risk_section": risk_assessment,
            "advice_section": advice_list,
            "confidence": confidence,
            "disclaimer": "本报告仅供健康管理参考，不构成医疗诊断。"
        }

        self.set_state("completed")

        return {
            "report": {
                **report,
                "report_text": summary
            }
        }
    
    def _build_prompt(
    self,
    indicators: List[Dict[str, Any]],
    risk_assessment: Dict[str, Any],
    advice_list: List[Dict[str, Any]],
    confidence: float,
    retrieved_memory: str,
) -> str:

        return f"""
Вы помощник по организации отчетов о состоянии здоровья.
Пожалуйста, подготовьте четкий, профессиональный и легкий для чтения отчет об оценке состояния здоровья на основе следующих результатов структурированного анализа.

Результаты анализа показателей здоровья:
{json.dumps(indicators, ensure_ascii=False, indent=2)}

Результаты оценки риска для здоровья:
{json.dumps(risk_assessment, ensure_ascii=False, indent=2)}

Советы по здоровью:
{json.dumps(advice_list, ensure_ascii=False, indent=2)}

Общая уверенность:
{confidence}

Восстановление исторической памяти (RAG):
{retrieved_memory}

Требовать:
- Никаких новых выводов анализа добавляться не будет.
- Не изменять существующие решения
- Понятный язык и понятная структура.
- Для обычных пользователей

Пожалуйста, верните формат JSON:
{{
  "summary": "..."
}}
"""

    def get_required_fields(self) -> list[str]:
        return []