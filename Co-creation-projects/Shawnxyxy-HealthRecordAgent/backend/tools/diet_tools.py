"""
Инструмент макета сцены диеты: запрос о питании, сводка упражнений/сна (можно заменить реальным API).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

# Распространенные варианты с высоким содержанием белка в магазинах и на вынос (для демонстрации)
_NUTRITION_MOCK: Dict[str, Dict[str, Any]] = {
«Яйцо»: {»protein_g_per_unit»: 6,0, «unit»: «1 штука (около 50 г)», «kcal_per_unit»: 70},
"вареные яйца": {"белок_г_на_единицу": 6,0, "единица": "1 штука", "ккал_на_единицу": 70},
"Греческий йогурт": {"protein_g_per_unit": 12,0, "unit": "100g", "kcal_per_unit": 95},
"Йогурт": {"protein_g_per_unit": 4,0, "unit": "100g", "kcal_per_unit": 85},
«Молоко»: {»белок_г_на_единицу»: 3,3, «единица»: «100мл», «ккал_на_единицу»: 60},
«Соевое молоко»: {»protein_g_per_unit»: 3,6, «unit»: «100ml», «kcal_per_unit»: 40},
"Готовая куриная грудка": {"protein_g_per_unit": 24,0, "unit": "100g", "kcal_per_unit": 120},
«Куриное бедро»: {»protein_g_per_unit»: 20,0, «unit»: «100g», «kcal_per_unit»: 180},
«Консервированный тунец»: {»protein_g_per_unit»: 22,0, «unit»: «100g», «kcal_per_unit»: 110},
"протеиновый батончик": {"protein_g_per_unit": 15,0, "unit": "1 палочка (около 40 г)", "kcal_per_unit": 180},
«Тофу»: {»protein_g_per_unit»: 8,0, «unit»: «100 г», «kcal_per_unit»: 80},
"сушеный творог": {"protein_g_per_unit": 16,0, "unit": "100g", "kcal_per_unit": 140},
}


def nutrition_lookup(query: str) -> Dict[str, Any]:
    """
Сопоставьте макеты таблиц питания по ключевым словам; поддержка нескольких ключевых слов, разделенных запятыми.
    """
    q = (query or "").strip()
    if not q:
        return {"matches": [], "hint": "请提供食物名称关键词"}

    keys = [k.strip() for k in q.replace("，", ",").split(",") if k.strip()]
    if not keys:
        keys = [q]

    matches: List[Dict[str, Any]] = []
    for kw in keys:
        for name, meta in _NUTRITION_MOCK.items():
            if kw in name or name in kw:
                matches.append({"name": name, **meta})
# прямое попадание
        if kw in _NUTRITION_MOCK and not any(m["name"] == kw for m in matches):
            matches.append({"name": kw, **_NUTRITION_MOCK[kw]})

#Удалить имя
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for m in matches:
        if m["name"] not in seen:
            seen.add(m["name"])
            uniq.append(m)

    return {
        "query": q,
        "matches": uniq[:20],
        "source": "mock_nutrition_db",
    }


def activity_sleep_summary(user_id: str) -> Dict[str, Any]:
    """
Макет: носимые/заполненные вручную резюме. Позже вы можете вместо этого прочитать user_profiles или внешний API.
    """
    _ = user_id
    return {
        "user_id": user_id,
"дата": "Сегодня",
        "steps": 8200,
        "sleep_hours": 6.5,
"sleep_quality": "Общее",
        "evening_workout": True,
"workout_type": "силовая тренировка",
"notes": "mock: цикл непрерывного приема данных зондирования/OpenAPI",
        "source": "mock_wearable",
    }


def tools_spec() -> str:
    return json.dumps(
        [
            {
                "name": "nutrition_lookup",
                "description": "查询常见便利店/外卖食物蛋白质含量与份量单位",
                "parameters": {"query": "关键词，多个用英文逗号分隔"},
            },
            {
                "name": "activity_sleep_summary",
                "description": "获取用户今日步数、睡眠与晚间是否安排训练等摘要",
"параметры": {"user_id": "идентификатор пользователя"},
            },
        ],
        ensure_ascii=False,
        indent=2,
    )


def dispatch_tool(name: str, action_input: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    if name == "nutrition_lookup":
        return nutrition_lookup(str(action_input.get("query", "")))
    if name == "activity_sleep_summary":
        uid = str(action_input.get("user_id") or user_id)
        return activity_sleep_summary(uid)
return {"ошибка": f"Неизвестный инструмент: {имя}"}
