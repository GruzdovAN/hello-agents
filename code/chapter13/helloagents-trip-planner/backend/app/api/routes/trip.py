"""Маршрутизация API планирования поездки"""

from fastapi import APIRouter, HTTPException
from ...models.schemas import (
    TripRequest,
    TripPlanResponse,
    ErrorResponse
)
from ...agents.trip_planner_agent import get_trip_planner_agent

router = APIRouter(prefix="/trip", tags=["планирование поездки"])


@router.post(
    "/plan",
    response_model=TripPlanResponse,
    summary="Создать план поездки",
    description="Создавайте подробные планы поездок на основе потребностей в поездках, введенных пользователем."
)
async def plan_trip(request: TripRequest):
    """
    Создать план поездки

    Аргументы:
        запрос: параметры запроса на поездку

    Возврат:
        ответ по планированию поездки
    """
    try:
        print(f"\n{'='*60}")
        print(f"📥 Получен запрос на планирование поездки:")
        print(f"   Город: {request.city}")
        print(f"   Дата: {request.start_date} – {request.end_date}")
        print(f"   Дни: {request.travel_days}")
        print(f"{'='*60}\n")

        # Получить экземпляр агента
        print("🔄 Получите примеры мультиагентных систем...")
        agent = get_trip_planner_agent()

        # Создать план поездки
        print("🚀 Начните составлять планы путешествий...")
        trip_plan = agent.plan_trip(request)

        print("✅ План поездки успешно создан, готов к ответу\n")

        return TripPlanResponse(
            success=True,
            message="План поездки успешно создан",
            data=trip_plan
        )

    except Exception as e:
        print(f"❌ Не удалось создать план поездки: {str(e)}.")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось создать план поездки: {str(e)}."
        )


@router.get(
    "/health",
    summary="проверка здоровья",
    description="Проверьте, правильно ли работает сервис планирования путешествий"
)
async def health_check():
    """проверка здоровья"""
    try:
        # Проверьте, доступен ли агент
        agent = get_trip_planner_agent()
        
        return {
            "status": "healthy",
            "service": "trip-planner",
            "agent_name": agent.agent.name,
            "tools_count": len(agent.agent.list_tools())
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Сервис недоступен: {str(e)}"
        )

