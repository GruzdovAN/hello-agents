"""
Интеллектуальный помощник по анализу запасов — модуль подключения к базе данных

Используйте SQLAlchemy + aiosqlite для реализации асинхронного доступа к базе данных.
Файл базы данных автоматически создается в каталоге данных проекта.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from pathlib import Path
import sys

# 确保能导入配置模块
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "backend"))

from app.config import settings


# Преобразование URL-адреса SQLite в асинхронную версию (aiosqlite)
def _build_async_url(url: str) -> str:
"""Преобразовать формат sqlite:/// в формат sqlite+aiosqlite:///"""
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    return url


# Убедитесь, что каталог данных существует
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

# Создаём асинхронный движок
engine = create_async_engine(
    _build_async_url(settings.DATABASE_URL),
echo=False, # Можно установить значение True для просмотра журналов SQL во время разработки.
)

# Создаём фабрику асинхронных сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Декларативный базовый класс SQLAlchemy
class Base(DeclarativeBase):
    pass


async def init_db():
    """初始化数据库，创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncSession:
"""Получить сеанс базы данных (для внедрения зависимостей FastAPI)"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db():
"""Закрыть соединение с базой данных"""
    await engine.dispose()
