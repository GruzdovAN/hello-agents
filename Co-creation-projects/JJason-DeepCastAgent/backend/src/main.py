"""通过 HTTP 暴露 DeepResearchAgent 的 FastAPI 入口点。"""

from __future__ import annotations

import asyncio
import concurrent.futures
import glob
import json
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

# Ensure src directory is in sys.path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel, Field

from agent import DeepResearchAgent
from config import Configuration

# Добавляем обработчик журнала консоли
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <4}</level> | <cyan>using_function:{function}</cyan> | <cyan>{file}:{line}</cyan> | <level>{message}</level>",
    colorize=True,
)


class ResearchRequest(BaseModel):
"""Нагрузка, запускающая исследование."""

    topic: str = Field(..., description="用户提供的研究主题")

class PodcastScript(BaseModel):
"""Модель контента сценария подкаста."""
    script: str = Field(..., description="生成的播客脚本内容")


class ResearchResponse(BaseModel):
"""Содержит HTTP-ответы для создания отчетов и структурированных задач."""

    report_markdown: str = Field(
        ..., description="Markdown 格式的研究报告，包含各个部分"
    )
    todo_items: list[dict[str, Any]] = Field(
        default_factory=list,
описание="Структурированная задача с кратким описанием и источниками",
    )
    podcast_script: PodcastScript | None = Field(
        default=None,
описание="Сгенерированный контент сценария подкаста",
    )


def _mask_secret(value: str | None, visible: int = 4) -> str:
"""Маскируйте чувствительные токены, сохраняя начальные и конечные символы."""
    if not value:
        return "unset"

    if len(value) <= visible * 2:
        return "*" * len(value)

    return f"{value[:visible]}...{value[-visible:]}"


def _build_config(payload: ResearchRequest) -> Configuration:
    return Configuration.from_env()


def create_app() -> FastAPI:
"""Создайте и настройте экземпляр приложения FastAPI."""

# В настоящее время активная ссылка на исследовательский агент, используемая для поддержки операций отмены
    _active_agent: dict[str, DeepResearchAgent | None] = {"current": None}

# Убедитесь, что выходной каталог существует (используйте абсолютный путь, основанный на корневом каталоге серверной части)
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(backend_root, "output")
    os.makedirs(output_dir, exist_ok=True)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
"""Управление жизненным циклом приложений: запись конфигурации при запуске и очистка ресурсов при завершении работы."""
        config = Configuration.from_env()
        logger.info(
            "DeepResearch configuration loaded: provider=%s model=%s base_url=%s search_api=%s "
            "max_loops=%s fetch_full_page=%s tool_calling=%s strip_thinking=%s api_key=%s",
            config.llm_provider,
            config.resolved_model() or "unset",
            config.llm_base_url or "unset",
            config.search_api.value,
            config.max_web_research_loops,
            config.fetch_full_page,
            config.use_tool_calling,
            config.strip_thinking_tokens,
            _mask_secret(config.llm_api_key),
        )
доходность # Приложение запущено
# Очистка при выключении
        _active_agent["current"] = None

    app = FastAPI(title="DeepCast - 自动播客生成智能体", lifespan=lifespan)

# Прочитайте разрешенные источники CORS из конфигурации, чтобы избежать использования подстановочных знаков в производственных средах.
    _startup_config = Configuration.from_env()
    _allowed_origins = [
        origin.strip()
        for origin in _startup_config.cors_origins.split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

#Подключаем каталог статических файлов для доступа к сгенерированным аудиофайлам
    app.mount("/output", StaticFiles(directory=output_dir), name="output")

    @app.get("/healthz")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/audio/latest")
    def get_latest_audio() -> dict[str, Any]:
"""Получить последний созданный аудиофайл."""
        audio_dir = os.path.join(output_dir, "audio")
        if not os.path.exists(audio_dir):
            return {"file": None, "error": "音频目录不存在"}
        
# Найти все файлы podcast_*.mp3
        pattern = os.path.join(audio_dir, "podcast_*.mp3")
        files = glob.glob(pattern)
        
        if not files:
            return {"file": None, "error": "没有找到音频文件"}
        
# Сортируйте по времени модификации, чтобы получить самую свежую информацию
        latest_file = max(files, key=os.path.getmtime)
        filename = os.path.basename(latest_file)
        return {"file": filename, "url": f"/output/audio/{filename}"}

    @app.post("/research", response_model=ResearchResponse)
    def run_research(payload: ResearchRequest) -> ResearchResponse:
        """
Запускайте синхронные исследовательские задачи.
        
Выполните полный процесс исследования и верните все результаты сразу в ответе HTTP.
        """
        try:
            config = _build_config(payload)
            agent = DeepResearchAgent(config=config)
            result = agent.run(payload.topic)
        except ValueError as exc:  # Likely due to unsupported configuration
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive guardrail
            raise HTTPException(status_code=500, detail="Research failed") from exc

        todo_payload = [
            {
                "id": item.id,
                "title": item.title,
                "intent": item.intent,
                "query": item.query,
                "status": item.status,
                "summary": item.summary,
                "sources_summary": item.sources_summary,
                "note_id": item.note_id,
                "note_path": item.note_path,
            }
            for item in result.todo_items
        ]

        # 确保 podcast_script 类型正确，Pydantic 模型需要 PodcastScript 实例
        script_content = ""
        if result.podcast_script:
            if isinstance(result.podcast_script, (list, dict)):
                script_content = json.dumps(result.podcast_script, ensure_ascii=False)
            else:
                script_content = str(result.podcast_script)
        
        podcast_resp = PodcastScript(script=script_content)

        return ResearchResponse(
            report_markdown=(result.report_markdown or result.running_summary or ""),
            todo_items=todo_payload,
            podcast_script=podcast_resp,
        )

    @app.post("/research/cancel")
    async def cancel_research() -> dict[str, str]:
        """
Заблаговременно отмените текущие исследовательские задачи.
        
Внешний интерфейс может явно уведомить серверную часть о прекращении обработки через эту конечную точку.
        """
        agent = _active_agent.get("current")
        if agent and not agent.is_cancelled():
            logger.info("Cancel requested via /research/cancel endpoint")
            agent.cancel()
            return {"status": "cancelled", "message": "取消请求已发送"}
        return {"status": "no_task", "message": "当前没有正在运行的任务"}

    @app.post("/research/stream")
    async def stream_research(payload: ResearchRequest, request: Request) -> StreamingResponse:
        """
Запускайте потоковые исследовательские задачи.
        
        通过 Server-Sent Events (SSE) 实时返回研究进度、日志和部分结果。
        支持客户端断开连接时自动取消后端任务。
        """
        try:
            config = _build_config(payload)
            agent = DeepResearchAgent(config=config)
            _active_agent["current"] = agent  # 注册活跃 agent 以支持取消
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        async def event_iterator():
            loop = asyncio.get_event_loop()
# Используйте asyncio.Queue для соединения синхронных генераторов и асинхронных циклов
            # 生成器在单一后台线程中完整运行，避免并发调用 next() 破坏生成器状态
            event_queue: asyncio.Queue = asyncio.Queue()
_SENTINEL = object() # Значение дозорного в конце генератора

            def run_generator():
                """在后台线程中完整运行生成器，将事件逐一推入异步队列。"""
                try:
                    for event in agent.run_stream(payload.topic):
                        if agent.is_cancelled():
                            logger.info("Generator stopped: cancel detected")
                            break
                        loop.call_soon_threadsafe(event_queue.put_nowait, event)
                except Exception as exc:
                    logger.exception("Generator raised exception")
                    loop.call_soon_threadsafe(
                        event_queue.put_nowait,
                        {"type": "error", "detail": str(exc)},
                    )
                finally:
                    loop.call_soon_threadsafe(event_queue.put_nowait, _SENTINEL)

# Запускаем задачу мониторинга отключения
            async def monitor_disconnect():
                while True:
                    if await request.is_disconnected():
                        logger.info("Client disconnected detected by monitor")
                        agent.cancel()
                        return
                    await asyncio.sleep(0.5)

            monitor_task = asyncio.create_task(monitor_disconnect())
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            loop.run_in_executor(executor, run_generator)

            try:
                while True:
                    try:
# С ожиданием тайм-аута, чтобы на отмену можно было отреагировать вовремя
                        item = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        # 超时时检查是否已取消（用于客户端断开但生成器还未感知的情况）
                        if agent.is_cancelled():
                            logger.info("✅ 本次任务已取消（超时检测）")
выход 'data: {"type": "cancelled", "message": "Исследовательская задача была отменена пользователем"}\n\n'
                            break
                        continue

# Sentinel: Генератор закончился
                    if item is _SENTINEL:
                        break

                    event = item
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                    if event.get("type") in ("done", "cancelled", "error"):
                        break
            finally:
# Убедитесь, что сигнал отмены установлен — это ядро ​​механизма отмены:
                # 前端 abort SSE 后 monitor_task 可能还未检测到断连就被 cancel，
# Для _active_agent могло быть установлено значение None при поступлении API /research/cancel.
                # 因此必须在此处显式调用 cancel() 确保后台线程能感知取消。
                agent.cancel()
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
                executor.shutdown(wait=False)
                _active_agent["current"] = None

        return StreamingResponse(
            event_iterator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    _config = Configuration.from_env()
    uvicorn.run(
        "main:app",
        host=_config.host,
        port=_config.port,
        reload=True,
        log_level=_config.log_level.lower(),
    )
