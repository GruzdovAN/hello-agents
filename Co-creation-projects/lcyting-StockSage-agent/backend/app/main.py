"""
Интеллектуальный помощник по анализу акций — портал приложений FastAPI

Метод запуска (выполняется из корневого каталога проекта):
    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

Запустите exe сразу после упаковки:
    stock_analyzer.exe
Доступ через браузер http://127.0.0.1:5174/dashboard (порт зависит от BACKEND_PORT в .env рядом с exe)
"""

import sys
import io
from pathlib import Path

# Восстановление кодировки консоли Windows: принудительно используйте вывод UTF-8, чтобы избежать ошибок печати эмодзи/китайского языка.
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

# Добавьте ключевой каталог проекта в sys.path, чтобы гарантировать правильную работу всех типов импорта.
# main.py находится в backend/app/main.py и должен подняться на 3 уровня вверх до корневого каталога проекта.
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend" # Сделайте импорт из app.xxx эффективным
_AGENTS_DIR = _PROJECT_ROOT/"агенты" # Сделать импорт из агентов.xxx эффективным
_HELLO_DIR = _PROJECT_ROOT / «HelloAgents Optimized» # Сделайте импорт из hello_agents эффективным

for p in [_BACKEND_DIR, _PROJECT_ROOT, _AGENTS_DIR, _HELLO_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
from contextlib import asynccontextmanager

from app.config import settings
from app.utils.response import success_response, error_response
from app.models.database import init_db, close_db
from app.models.report import AnalysisReport  # noqa: F401 — 确保数据库初始化时创建表
из app.models.history_models import AnalysisHistory # noqa: F401 — Обеспечить создание таблицы истории


@asynccontextmanager
async def lifespan(app: FastAPI):
"""Управление жизненным циклом приложения"""
# Выполнить при запуске
print(f"[Backend] Запускается интеллектуальный помощник по анализу акций...")
    warnings = settings.validate()
    if warnings:
        print("[后端] ⚠️ 配置警告:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("[后端] ✅ 配置验证通过")
print(f"Адрес службы [Backend]: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")

    # 初始化数据库（创建表）
    await init_db()
    print("[后端] ✅ 数据库初始化完成")

# Замечательный кеш, необходимый для прогрева дашборда в фоновом режиме (не блокируя этому воркеру прием запросов)
    async def _warm_dashboard_cache_bg() -> None:
        try:
            from app.services.dashboard_warmup import warm_dashboard_cache

            await asyncio.to_thread(warm_dashboard_cache)
print("[Backend] ✅ Прогрев данных информационной панели завершен (кеш Wonder в процессе заполнен)")
        except Exception as exc:
            print(f"[后端] ⚠️ 仪表盘预热未完成（可忽略）: {exc}")

    asyncio.create_task(_warm_dashboard_cache_bg())

    yield
# Выполнить при закрытии
    await close_db()
print("Служба [Backend] отключена")


#Создаем экземпляр приложения FastAPI
app = FastAPI(
title="Интеллектуальный помощник по анализу акций",
description="API инструмента анализа инвестиций A-share на основе мультиагентной архитектуры",
    version="0.1.0",
    lifespan=lifespan,
)

# Следует ли размещать продукт сборки Vue (интеграция с exe или установка FRONTEND_DIR и dist существует)
_FRONTEND_DIR = settings.FRONTEND_DIR
_SERVE_FRONTEND = _FRONTEND_DIR.exists() and (_FRONTEND_DIR / "index.html").exists()
# SPA 入口禁用强缓存：避免升级 exe 后浏览器仍用旧 index 引用已过期的 hash chunk
_SPA_INDEX_HEADERS = {"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"}

# =========================================================================
# Междоменное промежуточное программное обеспечение CORS (обеспечивает доступ к интерфейсному серверу разработки Vue3)
# =========================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.FRONTEND_PORT}",
        "http://127.0.0.1:5173",
        f"http://127.0.0.1:{settings.BACKEND_PORT}",
"*", # Разрешить все источники на этапе разработки
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================================
# Системная маршрутизация
# =========================================================================
@app.get("/api/v1/system/health", tags=["system"])
async def health_check():
"""Интерфейс проверки работоспособности"""
    return success_response(
        data={
            "status": "ok",
            "version": "0.1.0",
            "agent_ready": settings.is_agent_ready(),
            "skills_ready": settings.is_skills_ready(),
        }
    )


@app.get("/api/v1/system/config", tags=["system"])
async def system_config():
    """获取系统配置（公开信息，不包含密钥）"""
    return success_response(
        data={
            "llm_model": settings.LLM_MODEL_ID,
            "agent_ready": settings.is_agent_ready(),
            "skills_ready": settings.is_skills_ready(),
            "frontend_port": settings.FRONTEND_PORT,
        }
    )


@app.get("/", tags=["система"])
async def root():
    """根路径：托管前端时返回 index.html（与 vite dev 一致）；否则返回 API 说明"""
    if _SERVE_FRONTEND:
        return FileResponse(str(_FRONTEND_DIR / "index.html"), headers=dict(_SPA_INDEX_HEADERS))
    return {"message": "智能股票分析助手 API", "docs": "/docs"}


# =========================================================================
# Регистрация подмаршрутов
# =========================================================================
from app.api.preferences import router as preferences_router
from app.api.market import router as market_router
from app.api.financial import router as financial_router
from app.api.news import router as news_router
from app.api.screener import router as screener_router
from app.api.analysis import router as analysis_router
from app.api.watchlist import router as watchlist_router
from app.api.buffett import router as buffett_router
from app.api.simulation import router as simulation_router
from app.api.chat import router as chat_router
from app.api.history import router as history_router
from app.api.agent_api import router as agent_router
from app.api.sentiment import router as sentiment_router
from app.api.data_analysis import router as data_analysis_router
from app.api.cache_api import router as cache_router
from app.api.system_browser import router as system_browser_router

app.include_router(preferences_router, prefix="/api/v1")
app.include_router(market_router, prefix="/api/v1")
app.include_router(financial_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(screener_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(watchlist_router, prefix="/api/v1")
app.include_router(buffett_router, prefix="/api/v1")
app.include_router(simulation_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(history_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(sentiment_router, prefix="/api/v1")
app.include_router(data_analysis_router, prefix="/api/v1")
app.include_router(cache_router, prefix="/api/v1")
app.include_router(system_browser_router, prefix="/api/v1")

# =========================================================================
# Служба статических файлов внешнего интерфейса (включена, если указан режим exe или FRONTEND_DIR)
# =========================================================================
if _SERVE_FRONTEND:
    # 挂载 assets 等静态资源（文件名带 content hash，可由浏览器长期缓存）
    _assets_dir = _FRONTEND_DIR / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="frontend_assets")

    # SPA 回退：非 /api 路径返回 index.html（含禁止缓存响应头，见 _SPA_INDEX_HEADERS）
@app.get("/{full_path:path}", tags=["интерфейс"])
    async def serve_spa(full_path: str = ""):
        fp = _FRONTEND_DIR / full_path
        if full_path and fp.exists() and fp.is_file():
            return FileResponse(str(fp))
        return FileResponse(str(_FRONTEND_DIR / "index.html"), headers=dict(_SPA_INDEX_HEADERS))


# =========================================================================
#exe отдельный вход
# =========================================================================
def start_server(host: str = None, port: int = None):
"""Запустить сервер uvicorn (вызывается записью exe)"""
    import uvicorn
    uvicorn.run(
        app,
        host=host or settings.BACKEND_HOST,
        port=port or settings.BACKEND_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.BACKEND_DEBUG,
    )
