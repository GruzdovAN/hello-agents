"""HelloClaw Backend — портал FastAPI"""
import os

# Отключите PYTHONSTARTUP, чтобы избежать проблем с вводом-выводом.

os.environ.pop("PYTHONSTARTUP", None)

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import chat, session, config, memory
from .workspace.manager import WorkspaceManager
from .agent.helloclaw_agent import HelloClawAgent

# Загрузить переменные среды

load_dotenv()

# Экземпляр глобального агента

_agent: HelloClawAgent = None


def get_agent() -> HelloClawAgent:
    """Получить глобальный экземпляр агента"""
    global _agent
    return _agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложений"""
    global _agent

    # Инициализировать при запуске

    print("HelloClaw Backend starting...")

    # Инициализировать рабочую область

    workspace_path = os.getenv("WORKSPACE_PATH", "~/.helloclaw/workspace")
    workspace = WorkspaceManager(workspace_path)
    workspace.ensure_workspace_exists()
    print(f"Workspace initialized at: {workspace.workspace_path}")

    # Настройка экземпляра глобальной рабочей области

    config.set_workspace(workspace)
    memory.set_workspace(workspace)

    # Инициализируйте экземпляр глобального агента

    _agent = HelloClawAgent(workspace_path=workspace_path)
    print("HelloClawAgent initialized")

    yield
    # Очистка при выключении

    print("HelloClaw Backend shutting down...")


app = FastAPI(
    title="HelloClaw API",
    description="AI Agent powered by HelloAgents",
    version="0.1.0",
    lifespan=lifespan,
)

# Конфигурация CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# проверка здоровья

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "helloclaw-backend"}


# Зарегистрировать маршрут API

app.include_router(chat.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(memory.router, prefix="/api")


@app.get("/api")
async def api_root():
    return {"message": "HelloClaw API v0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
