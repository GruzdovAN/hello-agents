"""Оркестровщик, координирующий глубокие исследовательские процессы."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Lock, Thread
from typing import Any

from hello_agents import HelloAgentsLLM, ToolAwareSimpleAgent
from hello_agents.tools import ToolRegistry
from hello_agents.tools.builtin.note_tool import NoteTool

from config import Configuration
from models import SummaryState, SummaryStateOutput, TodoItem
from prompts import (
    report_writer_instructions,
    task_summarizer_system_prompt,
    todo_planner_system_prompt,
)
from services.audio_generator import AudioGenerationService
from services.audio_synthesizer import PodcastSynthesisService
from services.planner import PlanningService
from services.reporter import ReportingService
from services.script_generator import ScriptGenerationService
from services.search import dispatch_search, prepare_research_context
from services.summarizer import SummarizationService
from services.tool_events import ToolCallTracker

logger = logging.getLogger(__name__)


class DeepResearchAgent:
"""Координатор по координации рабочих процессов исследований на основе TODO с использованием HelloAgents."""

    def __init__(self, config: Configuration | None = None) -> None:
"""Инициализируйте координатор, используя инструменты настройки и общего доступа."""
        self.config = config or Configuration.from_env()
        self.default_llm = self._init_llm(self.config.llm_model_id)
        self.smart_llm = self._init_llm(self.config.smart_llm_model)
        self.fast_llm = self._init_llm(self.config.fast_llm_model)

        self.note_tool = (
            NoteTool(workspace=self.config.notes_workspace)
            if self.config.enable_notes
            else None
        )
        self.tools_registry: ToolRegistry | None = None
        if self.note_tool:
            registry = ToolRegistry()
            registry.register_tool(self.note_tool)
            self.tools_registry = registry

        self._tool_tracker = ToolCallTracker(
            self.config.notes_workspace if self.config.enable_notes else None
        )
        self._tool_event_sink_enabled = False
        self._state_lock = Lock()
self._cancel_event = Event() # Отменить сигнал

        self.todo_agent = self._create_tool_aware_agent(
name="Эксперт по планированию исследований",
            system_prompt=todo_planner_system_prompt.strip(),
            llm=self.smart_llm,
        )
        self.report_agent = self._create_tool_aware_agent(
name="Эксперт по написанию отчетов",
            system_prompt=report_writer_instructions.strip(),
            llm=self.smart_llm,
        )

        self._summarizer_factory: Callable[[], ToolAwareSimpleAgent] = lambda: self._create_tool_aware_agent(  # noqa: E501
name="Эксперт сводки задач",
            system_prompt=task_summarizer_system_prompt.strip(),
            llm=self.fast_llm,
        )

        self.planner = PlanningService(self.todo_agent, self.config)
        self.summarizer = SummarizationService(self._summarizer_factory, self.config)
        self.reporting = ReportingService(self.report_agent, self.config)
        self.script_generator = ScriptGenerationService(self.config)
        self.audio_generator = AudioGenerationService(self.config)

        self.podcast_synthesizer = PodcastSynthesisService(self.config)

    def cancel(self) -> None:
"""Запрос на отмену выполняемой в данный момент исследовательской задачи."""
        logger.info("Cancel requested for research agent")
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
"""Проверьте, не была ли отменена текущая задача."""
        return self._cancel_event.is_set()

    # ------------------------------------------------------------------
# Публичный API
    # ------------------------------------------------------------------
    def _init_llm(self, model_id_override: str | None = None) -> HelloAgentsLLM:
"""Создать экземпляр HelloAgentsLLM в соответствии с настройками конфигурации."""
        llm_kwargs: dict[str, Any] = {"temperature": 0.0}

        model_id = model_id_override or self.config.llm_model_id
        if model_id:
            llm_kwargs["model"] = model_id

        provider = (self.config.llm_provider or "").strip()
        if provider:
            llm_kwargs["provider"] = provider

        if self.config.llm_base_url:
            llm_kwargs["base_url"] = self.config.llm_base_url
        if self.config.llm_api_key:
            llm_kwargs["api_key"] = self.config.llm_api_key

        return HelloAgentsLLM(**llm_kwargs)

    def _create_tool_aware_agent(self, *, name: str, system_prompt: str, llm: HelloAgentsLLM) -> ToolAwareSimpleAgent:
"""ToolAwareSimpleAgent, который создает экземпляры общих реестров инструментов и средств отслеживания."""
        return ToolAwareSimpleAgent(
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            enable_tool_calling=self.tools_registry is not None,
            tool_registry=self.tools_registry,
            tool_call_listener=self._tool_tracker.record,
        )

    def _set_tool_event_sink(self, sink: Callable[[dict[str, Any]], None] | None) -> None:
"""Включить или отключить немедленные обратные вызовы событий инструмента."""
        self._tool_event_sink_enabled = sink is not None
        self._tool_tracker.set_event_sink(sink)

    def run(self, topic: str) -> SummaryStateOutput:
        """
Выполните рабочий процесс исследования и верните окончательный отчет (синхронный режим).
        
Этот метод последовательно выполняет следующие шаги:
        1. 初始化状态和规划任务。
2. Выполнять каждую задачу последовательно (поиск + суммирование).
3. Создайте окончательный отчет.
4. Создайте сценарий подкаста.
5. Создавайте аудиофайлы и синтезируйте подкасты.
        """
        state = SummaryState(research_topic=topic)
        state.todo_items = self.planner.plan_todo_list(state)
        self._drain_tool_events(state)

        if not state.todo_items:
            logger.info("No TODO items generated; falling back to single task")
            state.todo_items = [self.planner.create_fallback_task(state)]

        for task in state.todo_items:
            for _ in self._execute_task(state, task, emit_stream=False):
                pass

        report = self.reporting.generate_report(state)
        self._drain_tool_events(state)
        state.structured_report = report
        state.running_summary = report
        self._persist_final_report(state, report)

        script = self.script_generator.generate_script(state)
        self._drain_tool_events(state)
        state.podcast_script = script

# Генерируем звук для скрипта
        task_id = f"task_{state.report_note_id}" if state.report_note_id else "task_default"
        audio_files = self.audio_generator.generate_audio(script, task_id)

#синтезподкаст
        self.podcast_synthesizer.synthesize_podcast(audio_files, task_id)
        
        return SummaryStateOutput(
            running_summary=report,
            report_markdown=report,
            todo_items=state.todo_items,
            podcast_script=script,
        )

    def run_stream(self, topic: str) -> Iterator[dict[str, Any]]:
        """
Выполняйте рабочие процессы исследований и генерируйте дополнительные события прогресса (режим потоковой передачи).

Этот метод использует несколько потоков для параллельного выполнения исследовательских задач и возвращает прогресс в реальном времени через генератор.
Основные шаги:
1. Инициализируйте и планируйте задачи.
2. Запустите рабочий поток для каждой задачи для параллельной обработки.
3. Потоковая передача в режиме реального времени статуса задачи, результатов поиска и сводок разделов.
4. После выполнения всех задач формируется и передается итоговый отчет.
5. Создавайте и транслируйте сценарии подкастов и прогресс синтеза звука.

Поддерживает отмену выполнения с помощью метода cancel().
        """
#Сбросить статус отмены
        self._cancel_event.clear()

        state = SummaryState(research_topic=topic)
        logger.debug("Starting streaming research: topic=%s", topic)
        yield {"type": "status", "message": "初始化研究流程"}

        if self.is_cancelled():
            yield {"type": "cancelled", "message": "研究任务已取消"}
            return

# Этап 1: Планирование + параллельные исследования
        yield from self._stream_research_phase(state)
        if self.is_cancelled():
            yield {"type": "cancelled", "message": "研究任务已取消"}
            return

# Этап 2: Создание отчета
        yield from self._stream_report_phase(state)
        if self.is_cancelled():
            yield {"type": "cancelled", "message": "研究任务已取消"}
            return

# Этап 3: Сценарий подкаста
        script_turns = yield from self._stream_script_phase(state)
        if self.is_cancelled():
            yield {"type": "cancelled", "message": "研究任务已取消"}
            return
        if script_turns == 0:
            yield {"type": "done"}
            return

# Фаза 4: Генерация звука + синтез
        yield from self._stream_audio_phase(state, script_turns)

        yield {"type": "done"}

    # ------------------------------------------------------------------
# Метод этапа потоковой передачи
    # ------------------------------------------------------------------

    def _stream_research_phase(self, state: SummaryState) -> Iterator[dict[str, Any]]:
"""Этап 1: Планирование задач для параллельного выполнения поиска и сводки."""
        if self.is_cancelled():
            return
        state.todo_items = self.planner.plan_todo_list(state)
        if self.is_cancelled():
            return
        for event in self._drain_tool_events(state, step=0):
            yield event
        if not state.todo_items:
            state.todo_items = [self.planner.create_fallback_task(state)]

        channel_map: dict[int, dict[str, Any]] = {}
        for index, task in enumerate(state.todo_items, start=1):
            token = f"task_{task.id}"
            task.stream_token = token
            channel_map[task.id] = {"step": index, "token": token}

        serialized_tasks = [self._serialize_task(t) for t in state.todo_items]
        logger.info(f"Emitting todo_list event with {len(serialized_tasks)} tasks")
        yield {
            "type": "todo_list",
            "tasks": serialized_tasks,
            "step": 0,
        }

        event_queue: Queue[dict[str, Any]] = Queue()

        def enqueue(
            event: dict[str, Any],
            *,
            task: TodoItem | None = None,
            step_override: int | None = None,
        ) -> None:
            payload = dict(event)
            target_task_id = payload.get("task_id")
            if task is not None:
                target_task_id = task.id
                payload["task_id"] = task.id
            channel = channel_map.get(target_task_id) if target_task_id is not None else None
            if channel:
                payload.setdefault("step", channel["step"])
                payload["stream_token"] = channel["token"]
            if step_override is not None:
                payload["step"] = step_override
            event_queue.put(payload)

        self._set_tool_event_sink(lambda ev: enqueue(ev))

        threads: list[Thread] = []

        def worker(task: TodoItem, step: int) -> None:
            try:
                if self.is_cancelled():
                    enqueue({"type": "__task_done__", "task_id": task.id})
                    return
                enqueue(
                    {
                        "type": "task_status",
                        "task_id": task.id,
                        "status": "in_progress",
                        "title": task.title,
                        "intent": task.intent,
                        "query": task.query,
                        "note_id": task.note_id,
                        "note_path": task.note_path,
                    },
                    task=task,
                )
                for event in self._execute_task(state, task, emit_stream=True, step=step):
                    if self.is_cancelled():
                        break
                    enqueue(event, task=task)
            except Exception as exc:
                if self.is_cancelled():
                    logger.info("Task %s cancelled", task.id)
                else:
                    logger.exception("Task execution failed", exc_info=exc)
                enqueue(
                    {
                        "type": "task_status",
                        "task_id": task.id,
                        "status": "failed",
                        "detail": str(exc),
                        "title": task.title,
                        "intent": task.intent,
                        "query": task.query,
                        "note_id": task.note_id,
                        "note_path": task.note_path,
                    },
                    task=task,
                )
            finally:
                enqueue({"type": "__task_done__", "task_id": task.id})

        for task in state.todo_items:
            step = channel_map.get(task.id, {}).get("step", 0)
            thread = Thread(target=worker, args=(task, step), daemon=True)
            threads.append(thread)
            thread.start()

        active_workers = len(state.todo_items)
        finished_workers = 0

        try:
            while finished_workers < active_workers:
                try:
                    event = event_queue.get(timeout=0.5)
                except Empty:
                    if self.is_cancelled():
                        logger.info("Research cancelled during task execution")
выход {"type": "отменено", "message": "Исследовательская задача была отменена"}
                        return
                    continue
                if event.get("type") == "__task_done__":
                    finished_workers += 1
                    continue
                yield event

            while True:
                try:
                    event = event_queue.get_nowait()
                except Empty:
                    break
                if event.get("type") != "__task_done__":
                    yield event
        finally:
            self._set_tool_event_sink(None)
            for thread in threads:
                thread.join(timeout=1.0)

    def _stream_report_phase(self, state: SummaryState) -> Iterator[dict[str, Any]]:
"""Этап 2: Создание отчета об углубленном исследовании."""
        yield {
            "type": "stage_change",
            "stage": "report",
            "message": "所有研究任务已完成，正在撰写深度研究报告...",
        }
выход {"type": "log", "message": f"🧠 Вызов модели {self.config.smart_llm_model} для написания подробного отчета..."}

        if self.is_cancelled():
            return
        report = self.reporting.generate_report(state)
        if self.is_cancelled():
            return
        final_step = len(state.todo_items) + 1
        for event in self._drain_tool_events(state, step=final_step):
            yield event
        state.structured_report = report
        state.running_summary = report
доходность {"type": "log", "message": f"✓ Написание отчета завершено, всего {len(report)} символов"}

        if self.is_cancelled():
            return

        note_event = self._persist_final_report(state, report)
        if note_event:
            yield note_event

        yield {
            "type": "final_report",
            "report": report,
            "note_id": state.report_note_id,
            "note_path": state.report_note_path,
        }

    def _stream_script_phase(self, state: SummaryState) -> Iterator[dict[str, Any] | int]:
        """
Этап 3: Преобразуйте отчет в сценарий подкаста.

Выдает потоковые события и в конечном итоге возвращает количество раундов сценария (int).
Вызывающая сторона получает его через ``script_turns = выход из self._stream_script_phase(state)``.
        """
        yield {
            "type": "stage_change",
            "stage": "script",
"message": "Преобразование исследовательского отчета в сценарий подкаста для бесед...",
        }
выход {"type": "log", "message": f"🧠 Вызов {self.config.fast_llm_model} скрипта подкаста генерации модели..."}
урожай {"type": "log", "message": "Эксперты по планированию сценариев создают диалог между хостом (Сяюй) и гостем (Лива)..."}

        if self.is_cancelled():
            return
        script = self.script_generator.generate_script(state)
        if self.is_cancelled():
            return
        for event in self._drain_tool_events(state):
            yield event
        state.podcast_script = script

        script_turns = len(script) if script else 0
доходность {"type": "log", "message": f"✓ Генерация сценария завершена, всего раундов диалога: {script_turns}"}
        yield {
            "type": "podcast_script",
            "script": script,
            "turns": script_turns,
        }

        if script_turns == 0:
            yield {"type": "log", "message": "⚠️ 警告：脚本为空，跳过音频生成"}

        return script_turns  # type: ignore[return-value]

    def _stream_audio_phase(self, state: SummaryState, script_turns: int) -> Iterator[dict[str, Any]]:
"""Этап 4: генерация звука TTS + синтез FFmpeg."""
        script = state.podcast_script

        yield {
            "type": "stage_change",
            "stage": "audio",
"message": "Вызов речевого движка TTS для генерации звука...",
        }

        task_id = f"task_{state.report_note_id}" if state.report_note_id else "task_default"

# Используйте очереди для реализации потокового аудио в реальном времени.
        audio_event_queue: Queue[dict[str, Any]] = Queue()
        audio_result: list = []
        audio_error: list = []
        cancel_audio = Event()

        def audio_progress_callback(current: int, total: int, role: str, preview: str) -> bool:
"""Помещать события прогресса в очередь для обновлений в реальном времени."""
            if self.is_cancelled() or cancel_audio.is_set():
                return False
            audio_event_queue.put({
                "type": "audio_progress",
                "current": current,
                "total": total,
                "role": role,
                "preview": preview,
                "message": f"[TTS {current}/{total}] ✓ {role} 语音生成成功",
            })
            return True

        def run_audio_generation() -> None:
"""Запустить генерацию звука в отдельном потоке."""
            try:
                files = self.audio_generator.generate_audio(
                    script, task_id, audio_progress_callback,
                    cancel_event=self._cancel_event,
                )
                audio_result.append(files)
            except Exception as e:
                if not self.is_cancelled():
                    audio_error.append(str(e))
            finally:
                audio_event_queue.put({"type": "_audio_done"})

выход {"type": "log", "message": f"Приготовьтесь генерировать речь для диалога {script_turns}..."}
        yield {
            "type": "audio_start",
            "total": script_turns,
            "message": f"开始生成 {script_turns} 段语音",
        }

        audio_thread = Thread(target=run_audio_generation, daemon=True)
        audio_thread.start()

# События прямой трансляции
        while True:
            if self.is_cancelled():
                cancel_audio.set()
                yield {"type": "cancelled", "message": "研究任务已取消"}
                audio_thread.join(timeout=2.0)
                return
            try:
                event = audio_event_queue.get(timeout=0.1)
                if event.get("type") == "_audio_done":
                    break
                yield event
                if event.get("type") == "audio_progress":
                    yield {
                        "type": "log",
"message": f"[TTS {event['current']}/{event['total']}] ✓ {event['role']} Голос завершен",
                    }
            except Empty:
                continue

        audio_thread.join(timeout=5.0)

        if self.is_cancelled():
            yield {"type": "cancelled", "message": "研究任务已取消"}
            return

        audio_files = audio_result[0] if audio_result else []
        audio_count = len(audio_files) if audio_files else 0

        if audio_error:
выход {"тип": "журнал", "сообщение": f"⚠️ Ошибка создания аудио: {audio_error[0]}"}

выход {"type": "log", "message": f"Генерация голоса завершена, сегменты {audio_count}/{script_turns} успешны"}
        yield {
            "type": "audio_generated",
            "files": audio_files,
            "count": audio_count,
        }

#синтезподкаст
        yield {
            "type": "stage_change",
            "stage": "synthesis",
"message": "Составление полного аудиофайла подкаста...",
        }

        if self.is_cancelled():
            yield {"type": "cancelled", "message": "研究任务已取消"}
            return

        yield {"type": "log", "message": "使用 FFmpeg 拼接所有语音片段..."}
        podcast_file = self.podcast_synthesizer.synthesize_podcast(
            audio_files, task_id, cancel_check=self.is_cancelled,
        )
        if podcast_file:
            yield {"type": "podcast_ready", "file": podcast_file}
выход {"тип": "журнал", "сообщение": f"🎉 Файл подкаста успешно сгенерирован: {podcast_file}"}
        else:
выход {"type": "log", "message": "⚠️ Не удалось синтезировать подкаст, проверьте конфигурацию FFmpeg"}

    # ------------------------------------------------------------------
#Помощник по исполнению
    # ------------------------------------------------------------------
    def _execute_task(
        self,
        state: SummaryState,
        task: TodoItem,
        *,
        emit_stream: bool,
        step: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """
Запускайте логику поиска и сводки для одной задачи.
        
        Args:
состояние: статус глобального исследования.
задача: элемент задачи, который должен быть выполнен в данный момент.
            emit_stream: 是否产生流式事件（True 用于 run_stream，False 用于 run）。
шаг: номер текущего шага (только для потоковой передачи событий).
            
        Returns:
            事件字典的迭代器（即使 emit_stream=False，也可能产生少量内部事件，通常被忽略）。
        """
        task.status = "in_progress"

        search_result, notices, answer_text, backend = dispatch_search(
            task.query,
            self.config,
            state.research_loop_count,
        )
        task.notices = notices

        if emit_stream:
            for event in self._drain_tool_events(state, step=step):
                yield event
        else:
            self._drain_tool_events(state)

        if notices and emit_stream:
            for notice in notices:
                if notice:
                    yield {
                        "type": "status",
                        "message": notice,
                        "task_id": task.id,
                        "step": step,
                    }

        if not search_result or not search_result.get("results"):
            task.status = "skipped"
            if emit_stream:
                for event in self._drain_tool_events(state, step=step):
                    yield event
                yield {
                    "type": "task_status",
                    "task_id": task.id,
                    "status": "skipped",
                    "title": task.title,
                    "intent": task.intent,
                    "note_id": task.note_id,
                    "note_path": task.note_path,
                    "step": step,
                }
            else:
                self._drain_tool_events(state)
            return
        else:
            if not emit_stream:
                self._drain_tool_events(state)

        sources_summary, context = prepare_research_context(
            search_result,
            answer_text,
            self.config,
        )

        task.sources_summary = sources_summary

        with self._state_lock:
            state.web_research_results.append(context)
            state.sources_gathered.append(sources_summary)
            state.research_loop_count += 1

        summary_text: str | None = None

        if emit_stream:
            for event in self._drain_tool_events(state, step=step):
                yield event
            yield {
                "type": "sources",
                "task_id": task.id,
                "latest_sources": sources_summary,
                "raw_context": context,
                "step": step,
                "backend": backend,
                "note_id": task.note_id,
                "note_path": task.note_path,
            }

            summary_stream, summary_getter = self.summarizer.stream_task_summary(state, task, context)
            try:
                for event in self._drain_tool_events(state, step=step):
                    yield event
                for chunk in summary_stream:
                    if chunk:
                        yield {
                            "type": "task_summary_chunk",
                            "task_id": task.id,
                            "content": chunk,
                            "note_id": task.note_id,
                            "step": step,
                        }
                    for event in self._drain_tool_events(state, step=step):
                        yield event
            finally:
                summary_text = summary_getter()
        else:
            summary_text = self.summarizer.summarize_task(state, task, context)
            self._drain_tool_events(state)

Task.summary = summary_text.strip() if summary_text else «Информация пока отсутствует»
        task.status = "completed"

        if emit_stream:
            for event in self._drain_tool_events(state, step=step):
                yield event
            yield {
                "type": "task_status",
                "task_id": task.id,
                "status": "completed",
                "title": task.title,
                "intent": task.intent,
                "summary": task.summary,
                "sources_summary": task.sources_summary,
                "note_id": task.note_id,
                "note_path": task.note_path,
                "step": step,
            }
        else:
            self._drain_tool_events(state)

    def _drain_tool_events(
        self,
        state: SummaryState,
        *,
        step: int | None = None,
    ) -> list[dict[str, Any]]:
"""Инструмент обмена вызывает прокси-сервер трекера."""
        events = self._tool_tracker.drain(state, step=step)
        if self._tool_event_sink_enabled:
            return []
        return events

    def _serialize_task(self, task: TodoItem) -> dict[str, Any]:
"""Преобразуйте класс данных задачи во интерфейсный сериализуемый словарь."""
        return {
            "id": task.id,
            "title": task.title,
            "intent": task.intent,
            "query": task.query,
            "status": task.status,
            "summary": task.summary,
            "sources_summary": task.sources_summary,
            "note_id": task.note_id,
            "note_path": task.note_path,
            "stream_token": task.stream_token,
        }

    def _persist_final_report(self, state: SummaryState, report: str) -> dict[str, Any] | None:
        if not self.note_tool or not report or not report.strip():
            return None

        note_title = f"研究报告：{state.research_topic}".strip() or "研究报告"
        tags = ["deep_research", "report"]
        content = report.strip()

        note_id = self._find_existing_report_note_id(state)
        response = ""

        if note_id:
            response = self.note_tool.run(
                {
                    "action": "update",
                    "note_id": note_id,
                    "title": note_title,
                    "note_type": "conclusion",
                    "tags": tags,
                    "content": content,
                }
            )
            if response.startswith("❌"):
                note_id = None

        if not note_id:
            response = self.note_tool.run(
                {
                    "action": "create",
                    "title": note_title,
                    "note_type": "conclusion",
                    "tags": tags,
                    "content": content,
                }
            )
            note_id = self._tool_tracker._extract_note_id(response)

        if not note_id:
            return None

        state.report_note_id = note_id
        if self.config.notes_workspace:
            note_path = Path(self.config.notes_workspace) / f"{note_id}.md"
            state.report_note_path = str(note_path)
        else:
            note_path = None

        payload = {
            "type": "report_note",
            "note_id": note_id,
            "title": note_title,
            "content": content,
        }
        if note_path:
            payload["note_path"] = str(note_path)

        return payload

    def _find_existing_report_note_id(self, state: SummaryState) -> str | None:
        """
Найдите существующие идентификаторы заметок к отчету, связанные с темой исследования.
        
Этот метод проверяет, имеет ли текущее состояние связанный с ним идентификатор заметки отчета. В противном случае он циклически перебирает зарегистрированные события инструмента,
Найдите недавно созданные или обновленные заметки типа заключения с отчетом, в заголовке которого указана тема исследования.
        
        Args:
состояние: Текущий статус исследования, включая темы исследований и записанные события инструмента.
            
        Returns:
Идентификатор существующей заметки к отчету, связанной с темой исследования, если таковая существует, в противном случае — «Нет».
        """
        if state.report_note_id:
            return state.report_note_id

        for event in reversed(self._tool_tracker.as_dicts()):
            if event.get("tool") != "note":
                continue

            parameters = event.get("parsed_parameters") or {}
            if not isinstance(parameters, dict):
                continue

            action = parameters.get("action")
            if action not in {"create", "update"}:
                continue

            note_type = parameters.get("note_type")
            if note_type != "conclusion":
                title = parameters.get("title")
если нет (isinstance(title, str) и title.startswith("Отчет об исследовании")):
                    continue

            note_id = parameters.get("note_id")
            if not note_id:
                note_id = self._tool_tracker._extract_note_id(event.get("result", ""))  # type: ignore[attr-defined]

            if note_id:
                return note_id

        return None


