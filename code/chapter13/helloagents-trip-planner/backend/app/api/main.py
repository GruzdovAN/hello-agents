"""Основное приложение FastAPI"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..config import get_settings, validate_config, print_config
from .routes import trip, poi, map as map_routes

# Получить конфигурацию
settings = get_settings()

# Создать приложение FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API-интерфейс интеллектуального помощника по планированию поездок на основе платформы HelloAgents.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настроить КОРС
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зарегистрировать маршрут
app.include_router(trip.router, prefix="/api")
app.include_router(poi.router, prefix="/api")
app.include_router(map_routes.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """событие запуска приложения"""
    print("\n" + "="*60)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("="*60)
    
    # Распечатать информацию о конфигурации
    print_config()
    
    # Проверьте конфигурацию
    try:
        validate_config()
        print("\n✅ Проверка конфигурации пройдена")
    except ValueError as e:
        print(f"\n❌ Проверка конфигурации не удалась:\n{e}")
        print("\nПроверьте файл .env и убедитесь, что установлены все необходимые элементы конфигурации.")
        raise
    
    print("\n" + "="*60)
    print("📚 Документация по API: http://localhost:8000/docs.")
    print("📖 Документ ReDoc: http://localhost:8000/redoc.")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Событие закрытия приложения"""
    print("\n" + "="*60)
    print("👋Приложение закрывается...")
    print("="*60 + "\n")


@app.get("/")
async def root():
    """корневой путь"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health():
    """проверка здоровья"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )

