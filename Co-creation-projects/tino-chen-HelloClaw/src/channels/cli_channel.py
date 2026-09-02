"""CLI Channel — канал взаимодействия через командную строку

REPL-цикл с поддержкой:
- многораундового диалога
- потокового вывода
- команд выхода
- расширенного вывода в терминале
"""

import asyncio
import sys
from typing import Optional, TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text

if TYPE_CHECKING:
    from ..agent.helloclaw_agent import HelloClawAgent


class CLIChannel:
    """Канал CLI-взаимодействия

    REPL-цикл: ввод пользователя и вывод Agent.

    Attributes:
        agent: экземпляр HelloClaw Agent
        session_id: ID текущей сессии
        console: экземпляр Rich Console
    """

    EXIT_COMMANDS = {"exit", "quit", "q", "bye", "выход"}
    HELP_COMMANDS = {"help", "h", "помощь", "?"}
    CLEAR_COMMANDS = {"clear", "cls", "очистить"}

    def __init__(
        self,
        agent: "HelloClawAgent",
        session_id: Optional[str] = None,
    ):
        """Инициализация CLI Channel"""
        self.agent = agent
        self.session_id = session_id
        self.console = Console()
        self._running = False

    async def run(self):
        """Запустить REPL-цикл"""
        self._running = True
        self._print_welcome()

        while self._running:
            try:
                user_input = await self._get_input()
                if user_input is None:
                    break
                if not self._handle_command(user_input):
                    await self._chat(user_input)
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Прерывание — введите 'exit' для выхода[/yellow]")
            except EOFError:
                self.console.print("\n[yellow]До свидания![/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Ошибка: {e}[/red]")

        self._print_goodbye()

    async def _get_input(self) -> Optional[str]:
        """Получить ввод пользователя"""
        try:
            user_input = Prompt.ask("\n[bold cyan]Вы[/bold cyan]").strip()
            return user_input or None
        except (KeyboardInterrupt, EOFError):
            return None

    def _handle_command(self, input_text: str) -> bool:
        """Обработать специальные команды"""
        cmd = input_text.lower().strip()
        if cmd in self.EXIT_COMMANDS:
            self._running = False
            return True
        if cmd in self.HELP_COMMANDS:
            self._print_help()
            return True
        if cmd in self.CLEAR_COMMANDS:
            self.console.clear()
            self._print_welcome(compact=True)
            return True
        return False

    async def _chat(self, message: str):
        """Диалог с Agent"""
        with self.console.status("[bold green]Думаю...[/bold green]"):
            try:
                async for event in self.agent.achat(message, session_id=self.session_id):
                    event_type = event.type.value
                    if event_type == "llm_chunk":
                        self.console.print(event.chunk or "", end="")
                    elif event_type == "tool_call_start":
                        tool_name = getattr(event, "tool_name", "unknown")
                        self.console.print(f"\n[dim]🔧 Вызов инструмента: {tool_name}...[/dim]")
                    elif event_type == "agent_finish":
                        if hasattr(event, "result") and event.result:
                            self.console.print()
                if hasattr(self.agent, "_current_session_id"):
                    self.session_id = self.agent._current_session_id
            except Exception as e:
                self.console.print(f"\n[red]❌ Ошибка Agent: {e}[/red]")

    def _print_welcome(self, compact: bool = False):
        """Приветственное сообщение"""
        if compact:
            self.console.print(Panel(
                f"[bold]{self.agent.name}[/bold] — ваш персональный AI-ассистент",
                border_style="blue",
            ))
        else:
            self.console.print(Panel(
                f"[bold]{self.agent.name}[/bold] — ваш персональный AI-ассистент\n\n"
                "[dim]Введите сообщение для начала диалога[/dim]\n"
                "[dim]'help' — помощь, 'exit' — выход[/dim]",
                title="HelloClaw",
                border_style="blue",
            ))

    def _print_goodbye(self):
        """Прощальное сообщение"""
        self.console.print("\n[bold blue]До свидания! 👋[/bold blue]\n")

    def _print_help(self):
        """Сообщение помощи"""
        help_text = """[bold]Команды:[/bold]

[cyan]exit, quit, q[/cyan]  — выход
[cyan]help, h, ?[/cyan]     — помощь
[cyan]clear, cls[/cyan]     — очистить экран

[bold]Подсказки:[/bold]
- Введите сообщение для диалога с AI
- Контекст сохраняется между сообщениями
- Ctrl+C прерывает текущую операцию"""
        self.console.print(Panel(help_text, title="Помощь", border_style="green"))
