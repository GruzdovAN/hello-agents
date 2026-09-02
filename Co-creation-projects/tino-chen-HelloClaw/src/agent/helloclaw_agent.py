"""HelloClaw Agent - Персонализированный AI на HelloAgents SimpleAgent"""

import os
from typing import List

from hello_agents import Config
from .enhanced_simple_agent import EnhancedSimpleAgent
from .enhanced_llm import EnhancedHelloAgentsLLM  # Специальный LLM HelloClaw (поддерживает вызов инструментов потоковой передачи)

from ..memory.memory_flush import MemoryFlushManager
from ..memory.capture import MemoryCaptureManager
from hello_agents.tools import (
    ToolRegistry,
    ReadTool,
    WriteTool,
    EditTool,
    CalculatorTool,
)

from ..workspace.manager import WorkspaceManager
from ..tools import MemoryTool, ExecuteCommandTool, WebSearchTool, WebFetchTool


class HelloClawAgent:
    """HelloClaw Agent - Персонализированный AI-ассистент

    На основе HelloAgents SimpleAgent добавлено:
    - Управление рабочим пространством (файлы конфигурации, файлы памяти)
    - Читать системные подсказки с AGENTS.md
    - Эксклюзивный набор инструментов HelloClaw"""

    def __init__(
        self,
        workspace_path: str = None,
        name: str = None,
        model_id: str = None,
        api_key: str = None,
        base_url: str = None,
        max_tool_iterations: int = 10,
    ):
        """Инициализация агента HelloClaw

        Аргументы:
            workspace_path: путь к рабочей области, по умолчанию ~/.helloclaw/workspace
            name: Имя агента (читается из IDENTITY.md, вручную указывать не нужно)
            model_id: идентификатор модели LLM
            api_key: Ключ API
            base_url: Базовый URL-адрес API
            max_tool_iterations: Максимальное количество итераций вызова инструмента."""
        # Убедитесь, что путь к рабочей области_рабочей области правильно расширен ~/

        self.workspace_path = os.path.expanduser(workspace_path or "~/.helloclaw/workspace")

        # Инициализация менеджера рабочего пространства
        self.workspace = WorkspaceManager(self.workspace_path)

        # Создать рабочее пространство при необходимости
        self.workspace.ensure_workspace_exists()

        # Прочитайте имя из IDENTITY.md, используйте значение по умолчанию, если его нет.

        self.name = name or self._read_identity_name() or "HelloClaw"

        # Сохраните входящие параметры (используются для определения приоритета во время горячей загрузки)

        self._override_model_id = model_id
        self._override_api_key = api_key
        self._override_base_url = base_url

        # Создайте слова-подсказки для системы (читать из AGENTS.md)

        system_prompt = self._build_system_prompt()

        # Инициализировать LLM (прочитать конфигурацию из config.json)

        self._init_llm()

        # Начальная конфигурация

        self.config = Config(
            session_enabled=True,
            session_dir=os.path.join(self.workspace_path, "sessions"),
            compression_threshold=0.8,
            min_retain_rounds=10,
            enable_smart_compression=False,
            context_window=128000,
            trace_enabled=False,
            skills_enabled=False,
            todowrite_enabled=False,
            devlog_enabled=False,
            subagent_enabled=True,  # Включить поддержку дочернего агента

        )

        # Реестр инструмента инициализации

        self.tool_registry = self._setup_tools()

        # Инициализируйте базовый EnhancedSimpleAgent.

        self._agent = EnhancedSimpleAgent(
            name=self.name,  # Использовать прочитанное имя

            llm=self._llm,
            tool_registry=self.tool_registry,
            system_prompt=system_prompt,
            config=self.config,
            enable_tool_calling=True,
            max_tool_iterations=max_tool_iterations,
        )

        # Инициализируйте диспетчер очистки памяти

        self._memory_flush_manager = MemoryFlushManager(
            context_window=self.config.context_window,
            compression_threshold=self.config.compression_threshold,
            soft_threshold_tokens=4000,
            enabled=True,
        )

        # Инициализируйте диспетчер захвата памяти

        self._memory_capture_manager = MemoryCaptureManager(self.workspace)

    def _read_identity_name(self) -> str:
        """Прочитать имя помощника из IDENTITY.md

        Возврат:
            Имя помощника или «Нет», если не установлено."""
        import re
        identity = self.workspace.load_config("IDENTITY")
        if not identity:
            return None

        # Попробуйте сопоставить поле имени

        # Формат: - **Имя:** xxx или - **Имя:** xxx

match = re.search(r'\*\*Name[::]\*\*\s*(.+?)(?:\n|$)', тождество)
        if match:
            name = match.group(1).strip()
            # Проверьте, является ли это текстом-заполнителем (содержит подчеркивание или «выберите один» и т. д.)

if name, а не name.startswith('_') и '选一个' не по имени и '（' не по имени:
                return name
        return None

    def _init_llm(self):
        """Инициализировать LLM (прочитать конфигурацию из config.json)

        Приоритет конфигурации: параметры конструктора > config.json > переменные среды > значение по умолчанию."""
        llm_config = self.workspace.get_llm_config()

        self._model_id = self._override_model_id or llm_config.get("model_id") or "glm-4"
        self._api_key = self._override_api_key or llm_config.get("api_key")
        self._base_url = self._override_base_url or llm_config.get("base_url")

        self._llm = EnhancedHelloAgentsLLM(
            model=self._model_id,
            api_key=self._api_key,
            base_url=self._base_url,
        )

    def _reload_llm_if_changed(self) -> bool:
        """Проверьте изменения конфигурации и перезагрузите LLM.

        Если конфигурация в config.json изменится, создайте заново экземпляр LLM.

        Возврат:
            произошла ли перезагрузка"""
        llm_config = self.workspace.get_llm_config()

        new_model_id = self._override_model_id or llm_config.get("model_id") or "glm-4"
        new_api_key = self._override_api_key or llm_config.get("api_key")
        new_base_url = self._override_base_url or llm_config.get("base_url")

        if (new_model_id != self._model_id or
            new_api_key != self._api_key or
            new_base_url != self._base_url):

            print(f"🔄 Обнаружено изменение конфигурации, перезагрузка LLM: {self._model_id} -> {new_model_id}")

            self._model_id = new_model_id
            self._api_key = new_api_key
            self._base_url = new_base_url

            self._llm = EnhancedHelloAgentsLLM(
                model=self._model_id,
                api_key=self._api_key,
                base_url=self._base_url,
            )

            # Обновите ссылку LLM агента

            if hasattr(self, '_agent'):
                self._agent.llm = self._llm

            return True
        return False

    def _build_system_prompt(self) -> str:
        """Создание подсказок для системы

        Прочтите основной контент из AGENTS.md, добавив другие файлы конфигурации в качестве контекста.
        Если подключение не завершено, внедрите загрузочное содержимое BOOTSTRAP.md.

        Поднимает:
            RuntimeError: если AGENTS.md не существует"""
        # Читать с AGENTS.md (должен существовать)

        agents_content = self.workspace.load_config("AGENTS")
        if not agents_content:
            raise RuntimeError("Файл конфигурации AGENTS.md не найден, проверьте инициализацию workspace")

        base_prompt = agents_content

        # Загрузите другие файлы конфигурации в качестве контекста.

        context_parts = []

        # Проверка завершения онбординга
        if not self.workspace.is_onboarding_completed():
            bootstrap = self.workspace.load_config("BOOTSTRAP")
            if bootstrap:
                context_parts.append(f"\n## Онбординг\n\n{bootstrap}")

        # Идентификационная информация

        identity = self.workspace.load_config("IDENTITY")
        if identity:
            context_parts.append(f"\n## Ваша личность\n{identity}")

        # Информация о пользователе

        user_info = self.workspace.load_config("USER")
        if user_info:
            context_parts.append(f"\n## Информация о пользователе\n{user_info}")

        # шаблон личности

        soul = self.workspace.load_config("SOUL")
        if soul:
            context_parts.append(f"\n## Шаблон личности\n{soul}")

        # Долгосрочная память
        memory = self.workspace.load_config("MEMORY")
        if memory:
            context_parts.append(f"\n## Долгосрочная память\n{memory}")

        if context_parts:
            return base_prompt + "\n" + "\n".join(context_parts)

        return base_prompt

    def _setup_tools(self) -> ToolRegistry:
        """Набор инструментов настройки"""
        registry = ToolRegistry()

        # Встроенные инструменты HelloAgents

        registry.register_tool(ReadTool(project_root=self.workspace_path))
        registry.register_tool(WriteTool(project_root=self.workspace_path))
        registry.register_tool(EditTool(project_root=self.workspace_path))
        registry.register_tool(CalculatorTool())

        # Пользовательские инструменты HelloClaw

        registry.register_tool(MemoryTool(self.workspace))
        registry.register_tool(ExecuteCommandTool(
            allowed_directories=[self.workspace_path]  # Ограничено каталогом рабочей области

        ))
        registry.register_tool(WebSearchTool())  # Инструмент веб-поиска (требуется настройка BRAVE_API_KEY)

        registry.register_tool(WebFetchTool())   # Инструменты парсинга веб-страниц


        return registry

    def chat(self, message: str, session_id: str = None) -> str:
        """синхронный чат"""
        # Конфигурация горячей перезагрузки (обнаружение изменений config.json)

        self._reload_llm_if_changed()

        # Динамическое обновление слов системных подсказок (проверьте состояние BOOTSTRAP, прочитайте последнюю конфигурацию)

        self._agent.system_prompt = self._build_system_prompt()

        # Если есть session_id, проверьте, нужно ли загружать или очищать историю.

        if session_id:
            session_file = os.path.join(self.workspace_path, "sessions", f"{session_id}.json")
            if os.path.exists(session_file):
                self._agent.load_session(session_file)
            else:
                self._agent.clear_history()
        else:
            self._agent.clear_history()

        # Параметры вызова LLM (для предотвращения повторных циклов)

        llm_kwargs = {
            "frequency_penalty": 0.5,  # Уменьшите вероятность повторения одного и того же контента.

            "presence_penalty": 0.3,   # Поощряйте разговор на новые темы

        }

        # Запустить агент

        response = self._agent.run(message, **llm_kwargs)

        # сохранить сеанс

        save_id = session_id or self.create_session()
        try:
            self._agent.save_session(save_id)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения сессии: {e}")

        return response

    async def achat(self, message: str, session_id: str = None):
        """Асинхронный чат (поддерживает потоковую передачу)

        Аргументы:
            сообщение: сообщение пользователя
            session_id: идентификатор сеанса, если None создает новый сеанс.

        Выход:
            StreamEvent: событие потоковой передачи"""
        import uuid
        import time

        t0 = time.time()
        print(f"[⏱️ {t0:.3f}] achat начат")

        # Конфигурация горячей перезагрузки (обнаружение изменений config.json)

        self._reload_llm_if_changed()

        # Динамическое обновление слов системных подсказок (проверьте состояние BOOTSTRAP, прочитайте последнюю конфигурацию)

        self._agent.system_prompt = self._build_system_prompt()
        print(f"[⏱️ {time.time():.3f}] Системный промпт собран (+{time.time()-t0:.3f}s)")

        # Если session_id нет, создайте новый

        if not session_id:
            session_id = str(uuid.uuid4())[:8]
            self._agent.clear_history()
            # Сбросить состояние очистки памяти (новый сеанс)

            self._memory_flush_manager.reset()
        else:
            session_file = os.path.join(self.workspace_path, "sessions", f"{session_id}.json")
            if os.path.exists(session_file):
                self._agent.load_session(session_file)
            else:
                self._agent.clear_history()
                self._memory_flush_manager.reset()
        print(f"[⏱️ {time.time():.3f}] Сессия загружена (+{time.time()-t0:.3f}s)")

        # Сохраните session_id для последующего сохранения.

        self._current_session_id = session_id

        # Параметры вызова LLM (для предотвращения повторных циклов)

        llm_kwargs = {
            "frequency_penalty": 0.5,  # Уменьшите вероятность повторения одного и того же контента.

            "presence_penalty": 0.3,   # Поощряйте разговор на новые темы

        }

        t_llm = time.time()
        print(f"[⏱️ {t_llm:.3f}] начало调用 LLM ({self._model_id})...")
        first_chunk = True

        async for event in self._agent.arun_stream_with_tools(message, **llm_kwargs):
            if first_chunk and event.type.value == "llm_chunk":
                print(f"[⏱️ {time.time():.3f}] Первый token (задержка LLM: {time.time()-t_llm:.3f}s)")
                first_chunk = False
            yield event

        print(f"[⏱️ {time.time():.3f}] LLM завершён (всего: {time.time()-t0:.3f}s)")

        # Автоматически захватывать память после завершения разговора (выполняется асинхронно, без блокировки пользователя)

        await self._capture_memories(message)

        # После окончания разговора проверьте, нужно ли запускать Memory Flush (асинхронное выполнение, без блокировки пользователя)

        await self._check_and_run_memory_flush()

    async def _capture_memories(self, user_message: str):
        """Автоматически сохранять воспоминания из разговоров

        Аргументы:
            user_message: сообщение пользователя"""
        try:
            # Анализируйте и сохраняйте воспоминания с помощью MemoryCaptureManager.

            memories = await self._memory_capture_manager.acapture_and_store(user_message)

            if memories:
                print(f"📝 Автозахват {len(memories)} записей памяти")
                for m in memories:
                    print(f"   - [{m['category']}] {m['content'][:50]}...")
        except Exception as e:
            print(f"⚠️ Ошибка захвата памяти: {e}")

    async def _check_and_run_memory_flush(self):
        """Проверьте и выполните очистку памяти.

        Если текущее количество токенов близко к порогу сжатия, запускается тихий раунд, напоминающий агенту о необходимости сохранить свою память."""
        # Оцените текущее количество токенов (простая оценка: количество символов / 4)

        estimated_tokens = self._estimate_tokens()

        if self._memory_flush_manager.should_trigger_flush(estimated_tokens):
            print(f"\n🔄 Запуск Memory Flush (оценка token: {estimated_tokens})")

            # Получить слово подсказки для сброса

            flush_prompt = self._memory_flush_manager.get_flush_prompt()

            # Выполнить тихий раунд

            try:
                # Выполнить с использованием синхронного метода (не возвращается пользователю)

                response = self._agent.run(flush_prompt)

                # Проверьте, не является ли это молчаливым ответом

                if self._memory_flush_manager.is_silent_response(response):
                    print("📝 Агент решил не сохранять память")
                else:
                    print(f"📝 Агент сохранил память")

            except Exception as e:
                print(f"⚠️ Ошибка Memory Flush: {e}")

    def _estimate_tokens(self) -> int:
        """Оцените количество токенов в текущем контексте

        Используйте простые методы оценки характера.
        Для китайского языка около 1,5 символов/токен; для английского языка — около 4 символов на токен.
        Здесь используется консервативная оценка: символов/3.

        Возврат:
            Предполагаемое количество токенов"""
        total_chars = 0

        # Слово системной подсказки

        if self._agent.system_prompt:
            total_chars += len(self._agent.system_prompt)

        # исторические новости

        for msg in self._agent._history:
            if msg.content:
                total_chars += len(msg.content)

        # Консервативная оценка: количество символов / 3.

        return total_chars // 3

    def save_current_session(self):
        """Сохранить текущий сеанс"""
        if hasattr(self, '_current_session_id') and self._current_session_id:
            try:
                self._agent.save_session(self._current_session_id)
                return self._current_session_id
            except Exception as e:
                print(f"⚠️ Ошибка сохранения сессии: {e}")
        return None

    def create_session(self) -> str:
        """Создать новый сеанс"""
        import uuid
        session_id = str(uuid.uuid4())[:8]
        return session_id

    def list_sessions(self) -> List[dict]:
        """Список всех сессий"""
        sessions_dir = os.path.join(self.workspace_path, "sessions")
        if not os.path.exists(sessions_dir):
            return []

        sessions = []
        for filename in os.listdir(sessions_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(sessions_dir, filename)
                stat = os.stat(filepath)
                sessions.append({
                    "id": filename[:-5],
                    "created_at": stat.st_ctime,
                    "updated_at": stat.st_mtime,
                })

        return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)

    def delete_session(self, session_id: str) -> bool:
        """Удалить сеанс"""
        filepath = os.path.join(self.workspace_path, "sessions", f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def get_session_history(self, session_id: str) -> List[dict]:
        """Получить сообщения истории сеансов"""
        import json
        filepath = os.path.join(self.workspace_path, "sessions", f"{session_id}.json")
        if not os.path.exists(filepath):
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            messages = []
            raw_history = data.get("history", [])
            for msg in raw_history:
                role = msg.get("role", "")
                # Поддерживает три роли: пользователь, помощник, инструмент.

                if role in ("user", "assistant", "tool"):
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        text_parts = []
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text_parts.append(part.get("text", ""))
                            elif isinstance(part, str):
                                text_parts.append(part)
                        content = "\n".join(text_parts)

                    # Создайте объект сообщения, включая метаданные.

                    message_obj: dict = {"role": role, "content": content}
                    # Сохранять метаданные (содержитtool_calls илиtool_call_id)

                    if "metadata" in msg:
                        message_obj["metadata"] = msg["metadata"]

                    messages.append(message_obj)

            return messages
        except Exception as e:
            print(f"Error loading session history: {e}")
            return []

    def clear_all_history(self):
        """Очистить всю историю в памяти агента

        Используется для сброса состояния агента во время инициализации."""
        self._agent.clear_history()
        self._current_session_id = None

        # Сбросить состояние MemoryFlushManager

        if hasattr(self, '_memory_flush_manager'):
            self._memory_flush_manager.reset()

        # Перечитать имя (потому что IDENTITY.md мог быть сброшен)

        self.name = self._read_identity_name() or "HelloClaw"
