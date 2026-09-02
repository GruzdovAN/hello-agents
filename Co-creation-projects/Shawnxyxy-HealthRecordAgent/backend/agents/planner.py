"""
Планировщик медицинских записей HealthRecord (агент планировщика)
Отвечает за демонтаж и планирование задач по анализу медицинских файлов и отчетов о физическом осмотре.
"""

import os
import json
from datetime import datetime
from core.exceptions import AgentException
from typing import Dict, Any, List
from agents.base import BaseAgent

class PlannerAgent(BaseAgent):
"""Агент планирования задач"""
    def __init__(self, task_id=None, llm=None):
        super().__init__(name="Planner", task_id=task_id, llm=llm)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Planner 的唯一入口
        """
        await self.validate_input(input_data)
        self.set_state("running")

        try:
            goal = input_data["goal"]
            context = input_data.get("context", {})

            prompt = self._build_planner_prompt(goal, context)

            response = await self.think(prompt)

            plan = self._parse_plan(response)

            self.set_state("completed")
            self._add_to_history(f"生成计划，包含 {len(plan)} 个步骤")

            result = {
                "status": "success",
                "goal": goal,
                "plan": plan,
                "created_at": datetime.now().isoformat()
            }

            self.set_state("completed")

            return result

        except Exception as e:
            self.set_state("error")
            raise AgentException(f"PlannerAgent 执行失败: {str(e)}")
    
    def get_required_fields(self) -> List[str]:
        """
Планировщик заботится только о цели
        """
        return ["goal"]

    # ======================
# Внутренний метод
    # ======================
    def _build_planner_prompt(self, goal: str, context: Dict[str, Any]) -> str:
        """
Подсказка планировщика конструкции (Plan-And-Solve)
        """
        return f"""
Вы — агент-планировщик, который отлично умеет разбивать сложные цели на выполнимые подзадачи.

【Общая цель】
{goal}

[Контекстная информация]
{json.dumps(context, ensure_ascii=False, indent=2)}

Пожалуйста, следуйте этим рекомендациям:
1. Разбейте цель на 3–6 четких и практических шагов.
2. Делайте только одно действие на каждом этапе
3. Уточните, какой тип агента лучше всего подходит для выполнения этого шага.
4. Между шагами должна быть логическая последовательность
5. Не выполняйте задачи, просто планируйте

[Примеры доступных типов агентов]
- HealthAnalyzer: анализ данных о состоянии здоровья.
- RiskEvaluator: оценка рисков
- KnowledgeRetriever: запрос медицинских знаний
- ReportWriter: создание сводки и предложений.

[Формат вывода]
Пожалуйста, выводите строго в формате JSON и не включайте лишние пояснения:

{{
  "plan": [
    {{
      "step": 1,
      "agent": "AgentName",
"task": "описание задачи",
"input": "Для этого шага необходимы входные данные"
    }}
  ]
}}
"""
    def _parse_plan(self, response: str) -> List[Dict[str, Any]]:
        """
Выходные данные плана анализа из LLM
        """
        try:
            data = json.loads(response)
            plan = data.get("plan", [])
            if not plan:
поднять ValueError("План пуст")
            return plan
        except Exception:
            return [
                {
                    "step": 1,
                    "agent": "FallbackAgent",
"task": "Разбор не удался, требуется ручное или вторичное планирование",
                    "input": response
                }
            ]