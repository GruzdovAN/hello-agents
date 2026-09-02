"""Интеллектуальный рекомендательный API: мультиагентный конвейер (портрет → извлечение → рекомендация).

Синхронный агент/LLM выполняется через asyncio.to_thread, чтобы избежать блокировки цикла событий.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter

from ...agents.movie_recommender_agent import get_movie_recommender
from ...exceptions import AppError
from ...models.schemas import RecommendRequest, RecommendResponse
from ...utils.logger import get_logger

router = APIRouter(prefix="/recommend", tags=["Recommend"])
logger = get_logger("app.recommend")


@router.post(
    "",
    response_model=RecommendResponse,
summary="Интеллектуальная рекомендация фильмов",
    description=(
        "串行多智能体：画像（无工具）→ 检索（TMDB Tool）→ 推荐（候选内决策）。"
«Это может занять много времени (в зависимости от LLM), рекомендуется, чтобы время ожидания клиента составляло ≥ 120 с».
    ),
)
async def recommend_movies(request: RecommendRequest) -> RecommendResponse:
    logger.info(
"рекомендовать запрос настроение=%s вечеринка=%s жанры=%s",
        request.mood,
        request.party_type,
        request.genres,
    )
    agent = get_movie_recommender()
#рекомендовать() содержит несколько синхронизаций LLM/HTTP и помещает их в пул потоков
    result, message = await asyncio.to_thread(agent.recommend, request)
    return RecommendResponse(success=True, message=message, data=result)


@router.get(
    "/health",
summary="Рекомендуемая проверка работоспособности службы",
    description="返回各 Agent 名称与工具数量；初始化失败时 503。",
)
async def recommend_health():
    try:
        agent = get_movie_recommender()
        snap = agent.health_snapshot()
        return {
            "status": "healthy",
            "service": "recommend",
            **snap,
        }
    except Exception as e:
logger.Exception («рекомендовать работоспособность не удалась»)
        raise AppError(
f"Рекомендуемая услуга недоступна: {e}",
            code="RECOMMEND_UNAVAILABLE",
            status_code=503,
        ) from e
