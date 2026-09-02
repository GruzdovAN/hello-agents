"""
Агент анализа показателей работоспособности
"""

import json
from typing import Dict, Any, List
from agents.base import BaseAgent

class HealthIndicatorAgent(BaseAgent):
    def __init__(self, task_id=None, llm=None):
        super().__init__(name="HealthIndicatorAgent",  task_id=task_id, llm=llm)
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        await self.validate_input(input_data)
        self.set_state("running")

        report_text = input_data["report_text"]

        prompt = f"""
Вы профессиональный помощник по анализу здоровья.
Пожалуйста, извлеките ключевые показатели здоровья из следующего медицинского осмотра или отчета о состоянии здоровья и оцените риски.

Содержание отчета:
{report_text}

Пожалуйста, верните JSON, строго следуя следующему формату:
{{
  "indicator_results": {{
"<Имя индикатора>": {{
"value": "<исходное значение или описание>",
      "status": "<normal | borderline | high | low | abnormal>",
      "risk_level": "<low | medium | high>",
"analysis": "<Краткий анализ значения этого показателя для здоровья>"
    }}
  }}
}}

Требовать:
- Анализируйте каждый показатель индивидуально, не давайте исчерпывающих выводов
- Не давайте никаких советов по поводу здоровья.
- Если в отчете не указано четкое числовое значение, можно использовать описательное суждение.
"""
        response = await self.think(prompt)
        indicators: List[Dict[str, Any]] = []

        try:
            result = json.loads(response)
            indicator_dict = result.get("indicator_results", {})
            for name, data in indicator_dict.items():
                indicators.append({
                    "name": name,
                    "value": data.get("value"),
                    "status": data.get("status"),
                    "risk_level": data.get("risk_level"),
                    "analysis": data.get("analysis")
                })
        except json.JSONDecodeError:
# Защита от исключений вывода LLM
            indicators = []

        self.set_state("completed")
        return {
            "indicators": indicators
        }
    
    def get_required_fields(self) -> List[str]:
        return ["report_text"]