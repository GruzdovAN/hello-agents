"""Основная программа бэкэнда Cyber ​​Town FastAPI"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from models import (
    ChatRequest, ChatResponse, 
    NPCStatusResponse, NPCListResponse, NPCInfo
)
from agents import get_npc_manager
from state_manager import get_state_manager

# управление жизненным циклом
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложений"""
    # При запуске
    print("\n" + "="*60)
    print("🎮 Запускается серверная служба Cyber ​​Town...")
    print("="*60)
    
    # Проверьте конфигурацию
    settings.validate()
    
    # Инициализировать менеджера NPC
    npc_manager = get_npc_manager()
    
    # Инициализируйте и запустите менеджер состояний
    state_manager = get_state_manager(settings.NPC_UPDATE_INTERVAL)
    await state_manager.start()
    
    print("\n✔Все услуги активированы!")
    print(f"📡 Адрес API: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 Документация по API: http://{settings.API_HOST}:{settings.API_PORT}/docs.")
    print("="*60 + "\n")
    
    yield
    
    # когда закрыто
    print("\n🛑 Закрытие службы...")
    await state_manager.stop()
    print("✅ Сервис закрыт\n")

# Создать приложение FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Cyber ​​Town - диалоговая система AI NPC на основе HelloAgents",
    lifespan=lifespan
)

# Конфигурация CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Получить глобальный экземпляр
npc_manager = None
state_manager = None

def get_managers():
    """Получить экземпляр менеджера"""
    global npc_manager, state_manager
    if npc_manager is None:
        npc_manager = get_npc_manager()
    if state_manager is None:
        state_manager = get_state_manager()
    return npc_manager, state_manager

# =================== API-маршрутизация ====================

@app.get("/")
async def root():
    """Корневой путь — информация API"""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "features": ["разговор с ИИ", "Система памяти NPC", "Система льгот", "Пакетные обновления статуса"],
        "endpoints": {
            "docs": "/docs",
            "chat": "/chat",
            "npcs": "/npcs",
            "npcs_status": "/npcs/status",
            "npc_memories": "/npcs/{npc_name}/memories",
            "npc_affinity": "/npcs/{npc_name}/affinity",
            "all_affinities": "/affinities"
        }
    }

@app.get("/health")
async def health_check():
    """проверка здоровья"""
    return {"status": "healthy", "timestamp": "now"}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_npc(request: ChatRequest):
    """Диалоговый интерфейс с NPC
    
    Игроки общаются в режиме реального времени с назначенными NPC, используя независимую обработку агентов.
    """
    npc_mgr, _ = get_managers()
    
    # Убедитесь, что NPC существует
    npc_info = npc_mgr.get_npc_info(request.npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{request.npc_name}' не существует"
        )
    
    try:
        # Вызовите NPC-агента для ведения диалога.
        response_text = npc_mgr.chat(request.npc_name, request.message)
        
        return ChatResponse(
            npc_name=request.npc_name,
            npc_title=npc_info["title"],
            message=response_text,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось обработать разговор: {str(e)}"
        )

@app.get("/npcs", response_model=NPCListResponse)
async def list_npcs():
    """Получить список всех NPC"""
    npc_mgr, _ = get_managers()
    
    npcs_data = npc_mgr.get_all_npcs()
    npcs = [NPCInfo(**npc) for npc in npcs_data]
    
    return NPCListResponse(
        npcs=npcs,
        total=len(npcs)
    )

@app.get("/npcs/status", response_model=NPCStatusResponse)
async def get_npcs_status():
    """Получить текущий статус всех NPC
    
    Возвращает пакетно сгенерированное содержимое диалога NPC, используемое для отображения автономного поведения NPC.
    """
    _, state_mgr = get_managers()
    
    state = state_mgr.get_current_state()
    
    return NPCStatusResponse(
        dialogues=state["dialogues"],
        last_update=state["last_update"],
        next_update_in=state["next_update_in"]
    )

@app.post("/npcs/status/refresh")
async def refresh_npcs_status():
    """Принудительно обновить статус NPC
    
    Немедленно запустить пакетную генерацию диалога
    """
    _, state_mgr = get_managers()
    
    await state_mgr.force_update()
    state = state_mgr.get_current_state()
    
    return {
        "message": "Статус NPC обновлен.",
        "dialogues": state["dialogues"]
    }

@app.get("/npcs/{npc_name}")
async def get_npc_info(npc_name: str):
    """Получить подробную информацию об указанном NPC"""
    npc_mgr, state_mgr = get_managers()

    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' не существует"
        )

    # Добавить текущий разговор
    current_dialogue = state_mgr.get_npc_dialogue(npc_name)
    npc_info["current_dialogue"] = current_dialogue

    return npc_info

@app.get("/npcs/{npc_name}/memories")
async def get_npc_memories(npc_name: str, limit: int = 10):
    """Получите список воспоминаний NPC.

    Аргументы:
        npc_name: имяNPC
        предел: Ограничение на количество возвращаемых воспоминаний (по умолчанию 10).

    Возврат:
        Список воспоминаний NPC
    """
    npc_mgr, _ = get_managers()

    # Убедитесь, что NPC существует
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' не существует"
        )

    try:
        memories = npc_mgr.get_npc_memories(npc_name, limit=limit)

        return {
            "npc_name": npc_name,
            "memories": memories,
            "total": len(memories)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось получить память: {str(e)}"
        )

@app.delete("/npcs/{npc_name}/memories")
async def clear_npc_memories(npc_name: str, memory_type: str = None):
    """Очистить память NPC (для тестирования)

    Аргументы:
        npc_name: имя NPC
        Memory_type: тип памяти (рабочая/эпизодическая), если не указан, все будет очищено

    Возврат:
        Результат операции
    """
    npc_mgr, _ = get_managers()

    # Убедитесь, что NPC существует
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' не существует"
        )

    try:
        npc_mgr.clear_npc_memory(npc_name, memory_type)

        return {
            "message": f"Память {npc_name} очищена.",
            "npc_name": npc_name,
            "memory_type": memory_type or "all"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось очистить память: {str(e)}"
        )

@app.get("/npcs/{npc_name}/affinity")
async def get_npc_affinity(npc_name: str, player_id: str = "player"):
    """Получите благосклонность NPC к игроку.

    Аргументы:
        npc_name: имя NPC
        player_id: идентификатор игрока (по умолчанию «игрок»)

    Возврат:
        Информация о благоприятности
    """
    npc_mgr, _ = get_managers()

    # Убедитесь, что NPC существует
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' не существует"
        )

    try:
        affinity_info = npc_mgr.get_npc_affinity(npc_name, player_id)

        return {
            "npc_name": npc_name,
            "player_id": player_id,
            **affinity_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось получить благосклонность: {str(e)}"
        )

@app.get("/affinities")
async def get_all_affinities(player_id: str = "player"):
    """Получите благосклонность всех NPC к игроку.

    Аргументы:
        player_id: идентификатор игрока (по умолчанию «игрок»)

    Возврат:
        Информация о благосклонности всех NPC
    """
    npc_mgr, _ = get_managers()

    try:
        affinities = npc_mgr.get_all_affinities(player_id)

        return {
            "player_id": player_id,
            "affinities": affinities
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось получить благосклонность: {str(e)}"
        )

@app.put("/npcs/{npc_name}/affinity")
async def set_npc_affinity(npc_name: str, affinity: float, player_id: str = "player"):
    """Установите благосклонность NPC к игроку (для тестирования)

    Аргументы:
        npc_name: имя NPC
        близость: значение благосклонности (0-100)
        player_id: идентификатор игрока (по умолчанию «игрок»)

    Возврат:
        Результат операции
    """
    npc_mgr, _ = get_managers()

    # Убедитесь, что NPC существует
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' не существует"
        )

    # Проверьте диапазон предпочтительности
    if affinity < 0 or affinity > 100:
        raise HTTPException(
            status_code=400,
            detail="Предпочтительность должна находиться в диапазоне 0–100."
        )

    try:
        npc_mgr.set_npc_affinity(npc_name, affinity, player_id)
        affinity_info = npc_mgr.get_npc_affinity(npc_name, player_id)

        return {
            "message": f"Установлено благосклонность {npc_name} к игроку.",
            "npc_name": npc_name,
            "player_id": player_id,
            **affinity_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось установить предпочтение: {str(e)}"
        )

# =================== Вход в основную программу ===================

if __name__ == "__main__":
    print("\n🚀 Запустите серверную службу Cyber ​​Town...")
    print(f"📍 Адрес прослушивания: {settings.API_HOST}:{settings.API_PORT}")
    print(f"📖Доступ к документации: http://localhost:{settings.API_PORT}/docs\n.")
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,  # Автоперезагрузка режима разработки
        log_level="info"
    )

