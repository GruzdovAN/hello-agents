"""Портал командной строки HelloClaw

Используйте щелчок, чтобы реализовать интерфейс командной строки."""

import os
import asyncio
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

# Отключите PYTHONSTARTUP, чтобы избежать проблем с вводом-выводом.

os.environ.pop("PYTHONSTARTUP", None)

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="helloclaw")
def cli():
    """HelloClaw - Ваш Персонализированный AI-ассистент"""
    pass


@cli.command()
@click.option("--session", "-s", "session_id", default=None, help="ID сессии")
@click.option("--workspace", "-w", default=None, help="Путь к workspace")
def chat(session_id: Optional[str], workspace: Optional[str]):
    """Начать интерактивный разговор (режим REPL)"""
    from ..channels.cli_channel import CLIChannel
    from ..agent.helloclaw_agent import HelloClawAgent
    from ..workspace.manager import WorkspaceManager

    # Определить путь к рабочей области

    workspace_path = workspace or os.getenv("WORKSPACE_PATH", "~/.helloclaw/workspace")

    # Инициализировать рабочую область

    ws = WorkspaceManager(workspace_path)
    ws.ensure_workspace_exists()

    # Инициализировать агент

    try:
        agent = HelloClawAgent(workspace_path=workspace_path)
    except Exception as e:
        console.print(f"[red]❌ Ошибка инициализации Agent: {e}[/red]")
        raise SystemExit(1)

    # Запустить канал CLI

    channel = CLIChannel(agent, session_id=session_id)
    asyncio.run(channel.run())


@cli.command()
@click.argument("question")
@click.option("--session", "-s", "session_id", default=None, help="ID сессии")
@click.option("--workspace", "-w", default=None, help="Путь к workspace")
@click.option("--no-stream", is_flag=True, help="отключитьпотоковыйвывод")
def ask(question: str, session_id: Optional[str], workspace: Optional[str], no_stream: bool):
    """Задайте один вопрос и выйдите после вывода результатов."""
    from ..agent.helloclaw_agent import HelloClawAgent
    from ..workspace.manager import WorkspaceManager

    # Определить путь к рабочей области

    workspace_path = workspace or os.getenv("WORKSPACE_PATH", "~/.helloclaw/workspace")

    # Инициализировать рабочую область

    ws = WorkspaceManager(workspace_path)
    ws.ensure_workspace_exists()

    # Инициализировать агент

    try:
        agent = HelloClawAgent(workspace_path=workspace_path)
    except Exception as e:
        console.print(f"[red]❌ Ошибка инициализации Agent: {e}[/red]")
        raise SystemExit(1)

    if no_stream:
        # синхронный режим

        response = agent.chat(question, session_id=session_id)
        console.print(Markdown(response))
    else:
        # потоковый режим

        async def run_stream():
            async for event in agent.achat(question, session_id=session_id):
                if event.type.value == "llm_chunk":
                    console.print(event.chunk, end="")

        asyncio.run(run_stream())
        console.print()  # новая строка



@cli.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--workspace", "-w", default=None, help="Путь к workspace")
@click.option("--list", "-l", "list_all", is_flag=True, help="Перечислить все элементы")
@click.option("--edit", "-e", is_flag=True, help="Открыть в редакторе конфигурации файла")
def config(key: Optional[str], value: Optional[str], workspace: Optional[str], list_all: bool, edit: bool):
    """Управление конфигурацией

    Использование:
      helloclaw config # Показать все конфигурации
      helloclaw config model_id # Отобразить указанный элемент конфигурации
      helloclaw config model_id glm-4 # Установить элементы конфигурации
      helloclaw config --edit # Открыть файл конфигурации в редакторе"""
    from ..workspace.manager import WorkspaceManager

    workspace_path = workspace or os.getenv("WORKSPACE_PATH", "~/.helloclaw/workspace")
    ws = WorkspaceManager(workspace_path)
    ws.ensure_workspace_exists()

    config_path = os.path.join(ws.workspace_path, "config.json")

    if edit:
        # Откройте файл конфигурации в редакторе.

        editor = os.getenv("EDITOR", "nano")
        os.system(f"{editor} {config_path}")
        return

    # Чтение конфигурации

    llm_config = ws.get_llm_config()

    if list_all or (key is None and value is None):
        # Показать все конфигурации

        console.print(Panel(
            "\n".join([f"[cyan]{k}:[/cyan] {v}" for k, v in llm_config.items()]) or "[dim]пока нетконфигурация[/dim]",
            title="HelloClaw конфигурация",
            border_style="blue"
        ))
    elif key and value is None:
        # Показать один элемент конфигурации

        if key in llm_config:
            console.print(f"[cyan]{key}:[/cyan] {llm_config[key]}")
        else:
console.print(f"[yellow]конфигурация项 '{key}' не существует[/yellow]")
    elif key and value:
        # Установить элементы конфигурации

        import json
        llm_config[key] = value
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(llm_config, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✓[/green] уже设置 {key} = {value}")


@cli.command()
@click.option("--workspace", "-w", default=None, help="Путь к workspace")
@click.option("--list", "-l", "list_all", is_flag=True, help="Перечислить все сессии")
@click.option("--delete", "-d", "delete_id", default=None, help="удалениеУказать сессию")
@click.option("--clear", is_flag=True, help="清除所有сессия")
def sessions(workspace: Optional[str], list_all: bool, delete_id: Optional[str], clear: bool):
    """Управление сеансами

    Использование:
      helloclaw session # Вывести список всех сессий
      helloclaw session --list # Вывести список всех сессий
      helloclaw session --delete <id> # Удалить указанный сеанс
      helloclaw session --clear # Очистить все сеансы"""
    from ..workspace.manager import WorkspaceManager
    from datetime import datetime
    import glob

    workspace_path = workspace or os.getenv("WORKSPACE_PATH", "~/.helloclaw/workspace")
    ws = WorkspaceManager(workspace_path)
    ws.ensure_workspace_exists()

    sessions_dir = os.path.join(ws.workspace_path, "sessions")
    os.makedirs(sessions_dir, exist_ok=True)

    if delete_id:
        # Удалить указанный сеанс

        filepath = os.path.join(sessions_dir, f"{delete_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            console.print(f"[green]✓[/green] ужеудалениесессия: {delete_id}")
        else:
            console.print(f"[red]✗[/red] сессияне существует: {delete_id}")
    elif clear:
        # Очистить все разговоры

        session_files = glob.glob(os.path.join(sessions_dir, "*.json"))
        if session_files:
            for f in session_files:
                os.remove(f)
console.print(f"[green]✓[/green] ужеclear {len(session_files)} сессия")
        else:
            console.print("[yellow]没有сессия需要清除[/yellow]")
    else:
        # Список всех сессий

        session_files = glob.glob(os.path.join(sessions_dir, "*.json"))
        if not session_files:
            console.print("[dim]пока нетсессия[/dim]")
            return

        # Сортировать по времени модификации

        session_list = []
        for filepath in session_files:
            stat = os.stat(filepath)
            session_id = os.path.basename(filepath)[:-5]  # Удалить .json

            session_list.append({
                "id": session_id,
                "updated_at": stat.st_mtime,
            })

        session_list.sort(key=lambda x: x["updated_at"], reverse=True)

        for s in session_list:
            updated = datetime.fromtimestamp(s["updated_at"]).strftime("%Y-%m-%d %H:%M")
            console.print(f"[cyan]{s['id']}[/cyan] - {updated}")


def main():
    """Главный вход CLI"""
    cli()


if __name__ == "__main__":
    main()
