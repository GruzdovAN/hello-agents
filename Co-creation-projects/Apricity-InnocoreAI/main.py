"""
Yanchuang Intelligent Core — вход в главное приложение
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from innocore_ai.core.config import settings
from innocore_ai.core.database import engine, Base
from innocore_ai.core.exceptions import InnoCoreException
from innocore_ai.api.routes import papers, users, tasks, analysis, writing
from innocore_ai.agents.controller import AgentController

#Журнал конфигурации
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальный контроллер агента
agent_controller = None

@asynccontextmanager
async def lifespan(app: FastAPI):
"""Управление жизненным циклом приложения"""
# Выполнить при запуске
    logger.info("Starting InnoCore AI application...")
    
#Создаем таблицу базы данных
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
#Инициализируем контроллер агента
    global agent_controller
    agent_controller = AgentController()
    await agent_controller.initialize()
    logger.info("Agent controller initialized")
    
    yield
    
# Выполнить при закрытии
    logger.info("Shutting down InnoCore AI application...")
    if agent_controller:
        await agent_controller.shutdown()
    logger.info("Application shutdown complete")

#Создаем приложение FastAPI
app = FastAPI(
title="Яньчуанский интеллектуальный базовый API",
description="Интеллектуальная платформа для научных исследований на основе мультиагентной архитектуры",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Добавляем промежуточное ПО
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

#монтируем статические файлы
try:
    app.mount("/static", StaticFiles(directory="innocore_ai/frontend/static"), name="static")
except Exception:
# Если путь не существует, попробуйте относительный путь
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Зарегистрировать маршрут
app.include_router(users.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(papers.router, prefix="/api/v1/papers", tags=["Управление бумагой"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Управление задачами"])
app.include_router(anaанализ.router, prefix="/api/v1/anaанализ", tags=["Отчет об анализе"])
app.include_router(writing.router, prefix="/api/v1/writing", tags=["Академическое письмо"])

# Фронтальная маршрутизация
@app.get("/")
async def read_root():
"""Главная страница интерфейса"""
    try:
        from fastapi.responses import FileResponse
        return FileResponse("innocore_ai/frontend/index.html")
    except Exception:
        return FileResponse("frontend/index.html")

@app.get("/dashboard")
async def dashboard():
"""Страница информационной панели"""
    try:
        from fastapi.responses import FileResponse
        return FileResponse("innocore_ai/frontend/templates/dashboard.html")
    except Exception:
        return FileResponse("frontend/templates/dashboard.html")

@app.get("/login")
async def login():
"""Страница входа"""
    try:
        from fastapi.responses import FileResponse
        return FileResponse("innocore_ai/frontend/templates/login.html")
    except Exception:
        return FileResponse("frontend/templates/login.html")

# Обработка подстановочных знаков для внешней маршрутизации (для SPA)
@app.get("/frontend/{path:path}")
async def frontend_files(path: str):
"""Статические файлы интерфейса"""
    try:
        from fastapi.responses import FileResponse
        file_path = f"innocore_ai/frontend/{path}"
        return FileResponse(file_path)
    except Exception:
        file_path = f"frontend/{path}"
        return FileResponse(file_path)

@app.get("/health")
async def health_check():
"""Проверка здоровья"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "InnoCore AI"
    }

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats(request: Request):
"""Получить статистику панели мониторинга"""
#Здесь мы должны получить реальные данные из базы данных
    return {
        "total_papers": 156,
        "total_tasks": 42,
        "total_analyses": 28,
        "total_writings": 15,
        "recent_activities": [
{"type": "paper_added", "title": "Применение глубокого обучения в анализе медицинских изображений", "time": "2 часа назад"},
{"type": "task_completed", "title": "Поиск в литературе: машинное обучение", "time": "4 часа назад"},
{"type": "anaанализ_generated", "title": "Комплексный анализ 10 статей", "time": "1 день назад"}
        ]
    }

# Глобальная обработка исключений
@app.exception_handler(InnoCoreException)
async def innocore_exception_handler(request: Request, exc: InnoCoreException):
"""Обработка пользовательских исключений"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
"""Обработка типичных исключений"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
"message": "Внутренняя ошибка сервера",
            "details": str(exc) if settings.DEBUG else None
        }
    )

# Запрос промежуточного программного обеспечения журнала
@app.middleware("http")
async def log_requests(request: Request, call_next):
"""Запись журнала запросов"""
    start_time = asyncio.get_event_loop().time()
    
# Запрос журнала
    logger.info(f"Request: {request.method} {request.url}")
    
# Обрабатываем запрос
    response = await call_next(request)
    
# Рассчитать время обработки
    process_time = asyncio.get_event_loop().time() - start_time
    
# Запись ответа
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
    
# Добавить время обработки в заголовок ответа
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

def create_app():
"""Создать экземпляр приложения"""
    return app

if __name__ == "__main__":
    uvicorn.run(
        "innocore_ai.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )