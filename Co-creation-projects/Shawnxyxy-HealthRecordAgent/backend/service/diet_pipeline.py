"""
阶段 2：Nutritionist → Coach → Habit 三 Agent 串行流水线；
Выходные данные LLM каждого этапа проверяются Pydantic, и неудачные попытки автоматически повторяются; коды ошибок и понижения версии унифицированы.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel, ValidationError

from core.llm_adapter import get_llm_adapter
from memory.store import format_reflect_memory_for_prompt, save_diet_run
from rag.indexers import index_diet_run
from rag.retriever import retrieve
from service.diet_errors import DietErrorCode, diet_error_record
from service.diet_schemas import (
    SCHEMA_VERSION,
    CoachOutput,
    FoodParseOutput,
    HabitOutput,
    MealPlan,
    MealPlanItem,
    NutritionistOutput,
    NutritionSummary,
)
from tools.diet_tools import dispatch_tool

logger = logging.getLogger(__name__)

DIET_STAGE_TIMEOUT_SEC = 95.0
MAX_STAGE_ATTEMPTS = 2


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    t = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t)
    if m:
        t = m.group(1).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        i = t.find("{")
        j = t.rfind("}")
        if i >= 0 and j > i:
            try:
                return json.loads(t[i : j + 1])
            except json.JSONDecodeError:
                return None
    return None


def _goal_target_protein(context: Dict[str, Any]) -> float:
    goal = str(context.get("goal") or "maintain")
    if goal == "muscle_gain":
        return 130.0
    if goal == "fat_loss":
        return 95.0
    return 105.0


def _fallback_food_parse(context: Dict[str, Any]) -> FoodParseOutput:
    raw = str(context.get("today_food_log_text") or "")
    pieces = [p.strip(" ，。;；\n\t") for p in re.split(r"[，,;；。]\s*", raw) if p.strip()]
    items = []
    for p in pieces[:10]:
        items.append(
            {
                "meal_time": "",
                "food_name": p[:40],
"portion_text": "Непонятно",
                "confidence": 0.45,
            }
        )
    return FoodParseOutput(
        items=items,
        nutrition_summary=NutritionSummary(),
        parse_notes="（降级）食物解析阶段失败，已按日志片段做粗略拆分；营养值未估算。",
    )


def _fallback_nutritionist(context: Dict[str, Any], nutrition_summary: NutritionSummary) -> NutritionistOutput:
    tgt = _goal_target_protein(context)
    cur = float(nutrition_summary.protein_g or 0)
    gap = max(0.0, tgt - cur)
    return NutritionistOutput(
        protein_gap_g=gap,
        rationale="（降级）根据目标与日志解析结果估算蛋白缺口；LLM 阶段未通过校验或超时。",
        suggested_lookup_queries=["鸡蛋,希腊酸奶,牛奶,豆浆,即食鸡胸肉"],
кандидат_фокус = ["Магазин с высоким содержанием белка", "Посттренировочная добавка"],
    )


def _fallback_coach(context: Dict[str, Any]) -> CoachOutput:
    activity_text = str(context.get("activity_context") or "")
train = Any(k в Activity_text для k в ["тренировка", "сила", "фитнес", "тренировка", "тренировка"])
    return CoachOutput(
        training_recovery_note="（降级）晚间安排力量训练时需优先补充蛋白与适量碳水；具体强度以当日体感为准。"
        if train
else "(Понижение) В дни без тренировок по-прежнему сосредотачивайтесь на сбалансированном белке и избегайте переедания перед сном.",
        timing_constraints="训练后 1～2 小时内尽量安排一餐；便利店即食优先选成分表蛋白较高的品类。"
        if train
else "Старайтесь ужинать регулярно и не ешьте слишком много слишком поздно.",
        energy_note="",
        coach_constraints_for_menu=["少油炸", "避免单次过量乳糖不耐受品类"],
    )


def _fallback_habit(
    context: Dict[str, Any], reflect_mem: str, nutrition_summary: NutritionSummary
) -> HabitOutput:
    tgt = _goal_target_protein(context)
    cur = float(nutrition_summary.protein_g or 0)
    gap = max(25.0, min(80.0, max(0.0, tgt - cur)))
    return HabitOutput(
        reflect_alignment="（降级）未能生成完整习惯层输出；已忽略部分 Reflect 细节，仅做安全兜底推荐。"
+ («Недавно появились записи отзывов пользователей. Рекомендуется сократить цепочку принятия решений или проверить формат вывода модели в следующий раз». если «Нет», то нет в Reflection_mem else «»),
        execution_hints=["优先买得到、可立即食用的组合", "若仍失败请改选外卖蛋白套餐"],
        meal_plan=MealPlan(
            items=[
                MealPlanItem(
name="Греческий йогурт",
порция="около 150 г×1 чашка",
                    est_protein_g=min(18.0, gap * 0.35),
Why="распространено в магазинах повседневного спроса, с более высокой плотностью белка",
                ),
                MealPlanItem(
name="вареное яйцо",
порция="2 шт.",
                    est_protein_g=12.0,
Why="Легко купить, стабильный белок",
                ),
                MealPlanItem(
name="Соевое молоко",
                    portion="300ml",
                    est_protein_g=min(12.0, gap * 0.2),
Why="Добавка жидкого белка и влаги",
                ),
            ],
            total_est_protein_g=round(min(gap, 45.0), 1),
            tips=["此为 schema/LLM 失败时的安全兜底菜单，建议重试或检查 API。"],
        ),
    )


async def _run_validated_stage(
    llm: Any,
    stage: str,
    prompt: str,
    model_cls: Type[BaseModel],
    errors: List[Dict[str, Any]],
    timeout_sec: float = DIET_STAGE_TIMEOUT_SEC,
) -> Tuple[Optional[BaseModel], List[Dict[str, Any]]]:
    attempts: List[Dict[str, Any]] = []
    repair_hint = ""
    for attempt in range(MAX_STAGE_ATTEMPTS):
        full_prompt = prompt
        if repair_hint:
            full_prompt += (
                "\n\n【修正要求】上一输出未通过 schema 校验或无法解析：\n"
f"{repair_hint}\nПожалуйста, выведите только **один** объект JSON с полными полями и правильными типами. Markdown не требуется."
            )
        try:
            raw = await asyncio.wait_for(llm.ainvoke(full_prompt), timeout=timeout_sec)
        except asyncio.TimeoutError:
            errors.append(
                diet_error_record(
                    stage,
                    DietErrorCode.LLM_TIMEOUT,
«Тайм-аут вызова LLM»,
                    attempt=attempt,
                )
            )
            attempts.append(
                {"attempt": attempt, "ok": False, "error_code": DietErrorCode.LLM_TIMEOUT.value}
            )
            repair_hint = "上次超时；请输出更紧凑的 JSON，保留所有必填字段。"
            continue
        except Exception as e:
            # 上游模型网关 5xx / SDK 异常都归一为阶段中止错误，避免接口直接 500。
            errors.append(
                diet_error_record(
                    stage,
                    DietErrorCode.STAGE_ABORTED,
                    f"LLM 调用异常: {type(e).__name__}",
                    attempt=attempt,
                    detail=str(e)[:1200],
                )
            )
            attempts.append(
                {
                    "attempt": attempt,
                    "ok": False,
                    "error_code": DietErrorCode.STAGE_ABORTED.value,
                    "exception": type(e).__name__,
                }
            )
Repair_hint = "Последний вызов не удался, выводите только действительный JSON."
            continue

        obj = _extract_json_object(raw)
        if obj is None:
            errors.append(
                diet_error_record(
                    stage,
                    DietErrorCode.LLM_PARSE_ERROR,
«Невозможно проанализировать JSON из выходных данных модели»,
                    attempt=attempt,
                    detail=(raw[:1200] if raw else ""),
                )
            )
            attempts.append(
                {
                    "attempt": attempt,
                    "ok": False,
                    "error_code": DietErrorCode.LLM_PARSE_ERROR.value,
                    "llm_preview": (raw[:1500] if raw else ""),
                }
            )
            repair_hint = "模型输出不是合法 JSON；请严格输出 JSON only。"
            continue

        try:
            validated = model_cls.model_validate(obj)
            attempts.append(
                {
                    "attempt": attempt,
                    "ok": True,
                    "error_code": None,
                    "llm_preview": raw[:2500] if raw else "",
                }
            )
            return validated, attempts
        except ValidationError as ve:
            err_text = ve.json()[:2000]
            errors.append(
                diet_error_record(
                    stage,
                    DietErrorCode.VALIDATION_FAILED,
«Пидантическая проверка не удалась»,
                    attempt=attempt,
                    detail=err_text,
                )
            )
            attempts.append(
                {
                    "attempt": attempt,
                    "ok": False,
                    "error_code": DietErrorCode.VALIDATION_FAILED.value,
                    "validation_detail": err_text,
                    "parsed_shape": {k: type(v).__name__ for k, v in obj.items()}
                    if isinstance(obj, dict)
                    else None,
                }
            )
            repair_hint = err_text

    return None, attempts


def _prefetch_tools(user_id: str, context: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    trace_tools: List[Dict[str, Any]] = []
    activity: Dict[str, Any] = {}
    nutrition: Dict[str, Any] = {}
    try:
        activity = dispatch_tool(
            "activity_sleep_summary", {"user_id": user_id}, user_id
        )
    except Exception as e:
        trace_tools.append(
            {
                "tool": "activity_sleep_summary",
                "ok": False,
                "error": str(e),
            }
        )
    else:
        trace_tools.append({"tool": "activity_sleep_summary", "ok": True, "result": activity})

default_q = "Яйца, греческий йогурт, молоко, соевое молоко, готовая куриная грудка"
    try:
        nutrition = dispatch_tool(
            "nutrition_lookup",
            {"query": context.get("nutrition_prefetch_query") or default_q},
            user_id,
        )
    except Exception as e:
        trace_tools.append({"tool": "nutrition_lookup", "ok": False, "error": str(e)})
    else:
        trace_tools.append({"tool": "nutrition_lookup", "ok": True, "result": nutrition})

    return {"activity": activity, "nutrition": nutrition}, trace_tools


class DietMultiAgentPipeline:
    def __init__(self) -> None:
        self.llm = get_llm_adapter()

    async def run(
        self,
        user_id: str,
        context: Dict[str, Any],
        *,
        replayed_from_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        reflect_mem = format_reflect_memory_for_prompt(user_id, limit=8)
        errors: List[Dict[str, Any]] = []
        pipeline_trace: List[Dict[str, Any]] = []
        rag_result = await asyncio.to_thread(
            retrieve,
            user_id,
            {
                "scenario": "diet_recommendation",
                "goal": context.get("goal"),
                "free_notes": context.get("free_notes", ""),
                "today_food_log_text": str(context.get("today_food_log_text") or "")[:600],
"query": "Комплементация белка после тренировки и избежание препятствий при выполнении",
            },
        )
        rag_summary = rag_result.get("summary", "（暂无召回记忆）")
        pipeline_trace.append({"phase": "rag_retrieve", "debug": rag_result.get("debug", {})})

        tool_bundle, tool_trace = _prefetch_tools(user_id, context)
        pipeline_trace.append({"phase": "tool_prefetch", "tools": tool_trace})

        degraded = False

        # ----- Food Parse (LLM) -----
fp_prompt = f"""Вы являетесь агентом анализа журнала питания. Проанализируйте записи о диете пользователя на естественном языке в JSON. Выводите только объект JSON, без Markdown.

структура:
{{
  "items": [
    {{
"meal_time": строка, // завтрак/обед/ужин/перекус или пустая строка
      "food_name": string,
      "portion_text": string,
      "confidence": number      // 0~1
    }}
  ],
  "nutrition_summary": {{
    "protein_g": number,
    "carb_g": number,
    "fat_g": number,
    "fiber_g": number,
    "sodium_mg": number,
    "calories_kcal": number
  }},
  "parse_notes": string
}}

Требовать:
- 从 today_food_log_text 中尽可能提取食物与份量；没有明确份量可写“未明确”。
- Nutrition_summary дает приблизительную оценку; введите 0, если не можете определить.
- Поля заполнены и имеют правильный тип.

Пользовательский сценарий:
{json.dumps(context, ensure_ascii=False, indent=2)}
"""
        fp, fp_attempts = await _run_validated_stage(
            self.llm, "food_parse", fp_prompt, FoodParseOutput, errors
        )
        fp_fb = False
        if fp is None:
            fp = _fallback_food_parse(context)
            fp_fb = True
            degraded = True
            errors.append(
                diet_error_record(
                    "food_parse",
                    DietErrorCode.DEGRADED_FALLBACK,
«Фаза анализа еды не удалась, результат был понижен с помощью правил»,
                )
            )
        pipeline_trace.append(
            {
                "phase": "food_parse",
                "fallback_used": fp_fb,
                "attempts": fp_attempts,
                "output": fp.model_dump(),
            }
        )

        # ----- Nutritionist -----
n_prompt = f"""Вы **Агент диетолога**. Выводите только **JSON**, никакой другой текст.

Поля и типы должны быть абсолютно одинаковыми:
{{
  "protein_gap_g": number,
  "rationale": string,
  "suggested_lookup_queries": string[],
  "candidate_focus": string[]
}}

Пользовательский сценарий:
{json.dumps(context, ensure_ascii=False, indent=2)}

Результаты анализа пищевых продуктов (LLM):
{json.dumps(fp.model_dump(), ensure_ascii=False, indent=2)}

Отразить память (скорректировать рекомендуемую стратегию):
{reflect_mem}

Восстановление исторической памяти (RAG):
{rag_summary}

Результаты поиска ложной таблицы питания (для справки):
{json.dumps(tool_bundle.get("nutrition", {}), ensure_ascii=False, indent=2)}
"""
        nu, nu_attempts = await _run_validated_stage(
            self.llm, "nutritionist", n_prompt, NutritionistOutput, errors
        )
        nu_fb = False
        if nu is None:
            nu = _fallback_nutritionist(context, fp.nutrition_summary)
            nu_fb = True
            degraded = True
            errors.append(
                diet_error_record(
                    "nutritionist",
                    DietErrorCode.DEGRADED_FALLBACK,
«Этап диетолога провалился, и результат был снижен с помощью правил»,
                )
            )
        pipeline_trace.append(
            {
                "phase": "nutritionist",
                "fallback_used": nu_fb,
                "attempts": nu_attempts,
                "output": nu.model_dump(),
            }
        )

#Добавьте запрос о питании, рекомендованный диетологом (необязательно).
        extra_nutrition: Dict[str, Any] = {}
        if nu.suggested_lookup_queries:
            q = ",".join(nu.suggested_lookup_queries[:3])
            try:
                extra_nutrition = dispatch_tool(
                    "nutrition_lookup", {"query": q[:200]}, user_id
                )
            except Exception as e:
                errors.append(
                    diet_error_record(
                        "tool",
                        DietErrorCode.TOOL_ERROR,
                        f"nutrition_lookup 追加查询失败: {e}",
                    )
                )
                extra_nutrition = {"error": str(e)}
        tool_bundle["nutrition_extra"] = extra_nutrition

        # ----- Coach -----
        c_prompt = f"""你是 **Coach（运动恢复）Agent**。只输出 **一个 JSON**。

структура:
{{
  "training_recovery_note": string,
  "timing_constraints": string,
  "energy_note": string,
  "coach_constraints_for_menu": string[]
}}

Пользовательский сценарий:
{json.dumps(context, ensure_ascii=False, indent=2)}

Анализ продуктов питания (краткая информация о пищевой ценности):
{json.dumps(fp.nutrition_summary.model_dump(), ensure_ascii=False, indent=2)}

Заключение диетолога:
{json.dumps(nu.model_dump(), ensure_ascii=False, indent=2)}

Сводка активности/сна:
{json.dumps(tool_bundle.get("activity", {}), ensure_ascii=False, indent=2)}

Восстановление исторической памяти (RAG):
{rag_summary}
"""
        co, co_attempts = await _run_validated_stage(
            self.llm, "coach", c_prompt, CoachOutput, errors
        )
        co_fb = False
        if co is None:
            co = _fallback_coach(context)
            co_fb = True
            degraded = True
            errors.append(
                diet_error_record(
                    "coach",
                    DietErrorCode.DEGRADED_FALLBACK,
«Этап тренера не удался, выходные данные шаблона понижены»,
                )
            )
        pipeline_trace.append(
            {
                "phase": "coach",
                "fallback_used": co_fb,
                "attempts": co_attempts,
                "output": co.model_dump(),
            }
        )

        # ----- Habit -----
        h_prompt = f"""你是 **Habit（习惯养成）Agent**。只输出 **一个 JSON**。

структура:
{{
  "reflect_alignment": string,
  "execution_hints": string[],
  "meal_plan": {{
    "items": [{{ "name": string, "portion": string, "est_protein_g": number, "why": string }}],
    "total_est_protein_g": number,
    "tips": string[]
  }}
}}

Требовать:
- food_plan.items Минимум 1 товар; размер порции конкретен и выполним; подходит для магазинов шаговой доступности/на вынос.
- В сочетании с «Отражением памяти» объясните, как на этот раз избежать причин последней неудачи.
- est_protein_g — приблизительная оценка.

Пользовательский сценарий:
{json.dumps(context, ensure_ascii=False, indent=2)}

Результаты анализа продуктов питания:
{json.dumps(fp.model_dump(), ensure_ascii=False, indent=2)}

Отразить память:
{reflect_mem}

Восстановление исторической памяти (RAG):
{rag_summary}

Диетолог:
{json.dumps(nu.model_dump(), ensure_ascii=False, indent=2)}

Coach：
{json.dumps(co.model_dump(), ensure_ascii=False, indent=2)}

Данные о пищевой ценности (включая дополнительные запросы):
{json.dumps(tool_bundle, ensure_ascii=False, indent=2)[:12000]}
"""
        ha, ha_attempts = await _run_validated_stage(
            self.llm, "habit", h_prompt, HabitOutput, errors
        )
        ha_fb = False
        if ha is None:
            ha = _fallback_habit(context, reflect_mem, fp.nutrition_summary)
            ha_fb = True
            degraded = True
            errors.append(
                diet_error_record(
                    "habit",
                    DietErrorCode.DEGRADED_FALLBACK,
«Фаза привычки не удалась, использовано меню безопасности»,
                )
            )
        pipeline_trace.append(
            {
                "phase": "habit",
                "fallback_used": ha_fb,
                "attempts": ha_attempts,
                "output": ha.model_dump(),
            }
        )

        meal_plan = ha.meal_plan.model_dump()

        planning = {
            "reasoning": nu.rationale,
            "plan_steps": [
«FoodParse: извлечение продуктов и их порций из журналов еды и оценка питания»,
                f"Nutritionist：缺口约 {nu.protein_gap_g:.1f}g 蛋白",
«Тренер: обучение/принятие окон и ограничения восстановления»,
«Привычка: выравнивать исполняемое меню Reflect»,
            ],
            "agent_pipeline": [
                "FoodParseAgent",
                "NutritionistAgent",
                "CoachAgent",
                "HabitAgent",
            ],
        }

        output: Dict[str, Any] = {
            "run_id": run_id,
            "user_id": user_id,
            "schema_version": SCHEMA_VERSION,
            "pipeline_mode": "multi_agent",
            "replayed_from": replayed_from_run_id,
            "degraded": degraded,
            "errors": errors,
            "planning": planning,
            "stages": {
                "nutritionist": {
                    "ok": not nu_fb,
                    "fallback_used": nu_fb,
                    "output": nu.model_dump(),
                },
                "coach": {
                    "ok": not co_fb,
                    "fallback_used": co_fb,
                    "output": co.model_dump(),
                },
                "habit": {
                    "ok": not ha_fb,
                    "fallback_used": ha_fb,
                    "output": ha.model_dump(),
                },
            },
            "meal_plan": meal_plan,
            "food_parse": fp.model_dump(),
            "nutrition_summary": fp.nutrition_summary.model_dump(),
            "habit_extras": {
                "reflect_alignment": ha.reflect_alignment,
                "execution_hints": ha.execution_hints,
            },
            "react_trace": pipeline_trace,
            "reflect_memory_used": reflect_mem,
            "retrieved_memory": rag_summary,
            "rag_debug": rag_result.get("debug", {}),
        }

        try:
            save_diet_run(
                user_id=user_id,
                run_id=run_id,
                input_payload=context,
                steps_trace=pipeline_trace,
                output_payload=output,
                replayed_from_run_id=replayed_from_run_id,
            )
        except Exception as e:
            logger.exception("diet_runs 落库失败: %s", e)
        try:
# Индекс наилучших усилий, не влияет на основной процесс
            await asyncio.to_thread(index_diet_run, run_id)
        except Exception as e:
            logger.warning("diet run 向量索引失败（不影响返回）: %s", e)

        return output
        
