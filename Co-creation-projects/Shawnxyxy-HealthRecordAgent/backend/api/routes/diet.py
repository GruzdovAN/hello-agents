import asyncio
from typing import List, Literal, Optional

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field, field_validator

from memory.store import (
    get_diet_run,
    insert_diet_reflect,
    list_diet_runs_for_user,
    list_recent_diet_reflect,
)
from service.diet_recommend_service import DietRecommendService, replay_diet_run
from service.observability_views import build_diet_observability
from rag.indexers import index_reflect_event

router = APIRouter()


class DietContext(BaseModel):
    today_food_log_text: str = Field(
        ..., min_length=4, max_length=8000, description="今天吃了什么（自由文本）"
    )
    goal: Literal["muscle_gain", "fat_loss", "maintain"] = Field(
        default="muscle_gain", description="健康目标"
    )
    channels: List[str] = Field(
        default_factory=lambda: ["convenience_store", "delivery"],
описание="Покупные теги канала",
    )
Activity_context: str = Field(default="", max_length=2000,description="Упражнение/сон и другие контексты")
    free_notes: str = Field(
        default="", max_length=2000, description="额外说明（如只有便利店）"
    )


class DietRecommendRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=256)
    context: DietContext

    @field_validator("user_id")
    @classmethod
    def strip_uid(cls, v: str) -> str:
        v = v.strip()
        if not v:
поднять ValueError("user_id не может быть пустым")
        return v


class DietReplayRequest(BaseModel):
"""Необязательно: при передаче user_id он должен совпадать с run, чтобы предотвратить случайное воспроизведение."""

    user_id: Optional[str] = Field(default=None, max_length=256)


class DietReflectRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=256)
    diet_run_id: str = Field(..., min_length=8, max_length=64)
    followed: bool = Field(..., description="是否按上次推荐执行")
    reason_code: Optional[
        Literal["cant_buy", "too_late", "dont_want", "executed_ok", "other"]
    ] = Field(default=None, description="未执行或总结原因类型")
    reason_detail: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("user_id", "diet_run_id")
    @classmethod
    def strip_ids(cls, v: str) -> str:
        return v.strip()


@router.post("/diet/recommend")
async def diet_recommend(body: DietRecommendRequest):
    """
Рекомендации по диете: Этап 2 – **Детолог → Тренер → Привычка**, три агента, фиксированная схема JSON + проверка Pydantic;
На каждом этапе максимум 2 попытки. В случае неудачи он будет ухудшен и записан в `errors`/`degraded`.
Библиотека Diet_runs по-прежнему удаляется, и память Reflect считывается.
    """
    svc = DietRecommendService()
    ctx = body.context.model_dump()
    result = await svc.run(body.user_id, ctx)
    return result


@router.post("/diet/reflect")
async def diet_reflect(body: DietReflectRequest):
    """
    Reflect：用户反馈是否执行及原因，写入 diet_reflect；下次 recommend 自动读取。
    """
    row = get_diet_run(body.diet_run_id)
    if not row:
        raise HTTPException(status_code=404, detail="diet_run_id 不存在")
    if row.get("user_id") != body.user_id:
        raise HTTPException(status_code=403, detail="该 run 不属于此 user_id")

    rc = body.reason_code
    if body.followed and rc is None:
        rc = "executed_ok"

    rid = insert_diet_reflect(
        user_id=body.user_id,
        diet_run_id=body.diet_run_id,
        followed=body.followed,
        reason_code=rc,
        reason_detail=body.reason_detail,
    )
    asyncio.create_task(asyncio.to_thread(index_reflect_event, rid))
    return {
        "ok": True,
        "reflect_id": rid,
        "user_id": body.user_id,
        "diet_run_id": body.diet_run_id,
    }


@router.get("/diet/users/{user_id}/runs")
async def diet_runs(user_id: str, limit: int = 20):
    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id 无效")
    return {"user_id": uid, "items": list_diet_runs_for_user(uid, limit=limit)}


@router.get("/diet/users/{user_id}/reflect_history")
async def diet_reflect_history(user_id: str, limit: int = 20):
    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id 无效")
    return {"user_id": uid, "items": list_recent_diet_reflect(uid, limit=limit)}


@router.get("/diet/runs/{run_id}")
async def diet_run_detail(run_id: str):
    row = get_diet_run(run_id.strip())
    if not row:
        raise HTTPException(status_code=404, detail="未找到该饮食推荐 run")
    return row


@router.get("/diet/runs/{run_id}/observability")
async def diet_run_observability(run_id: str):
    """
Этап 3: Просмотр наблюдаемости — временная шкала/ошибки/описание повтора (след сохраняется в Diet_runs).
    """
    row = get_diet_run(run_id.strip())
    if not row:
        raise HTTPException(status_code=404, detail="未找到该饮食推荐 run")
    return build_diet_observability(row)


@router.post("/diet/runs/{run_id}/replay")
async def diet_run_replay(
    run_id: str,
    body: DietReplayRequest | None = Body(default=None),
):
    """
Этап 3. Используйте входные данные прогона для повторного запуска конвейера (новый run_id; столбцы replayed_from_run_id и output.replayed_from для отслеживания).
Макетные инструменты более детерминированы, результаты LLM все равно могут различаться.
    """
    rid = run_id.strip()
    row = get_diet_run(rid)
    if not row:
        raise HTTPException(status_code=404, detail="run 不存在")
    if body and body.user_id and body.user_id.strip() != row["user_id"]:
поднять HTTPException (status_code=403, Detail="user_id не соответствует запуску")
    try:
        return await replay_diet_run(rid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
