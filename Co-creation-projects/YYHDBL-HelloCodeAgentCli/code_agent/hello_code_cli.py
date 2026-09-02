from __future__ import annotations

import argparse
import os
import re
import logging
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False

from core.llm import HelloAgentsLLM
from core.exceptions import HelloAgentsException
from core.config import Config
from code_agent.agentic import CodeAgent
from code_agent.executors.apply_patch_executor import ApplyPatchExecutor, PatchApplyError
from utils.cli_ui import c, hr, PRIMARY, ACCENT, INFO, WARN, ERROR


# Сопоставление блоков патча в стиле Codex (многострочно, допускает ведущие пробелы и ограждения кода)
PATCH_RE = re.compile(r"\s*\*\*\* Begin Patch[\s\S]*?\*\*\* End Patch", re.MULTILINE)
PATCH_FENCE_RE = re.compile(
    r"```(?:patch|diff|text)?\s*(\*\*\* Begin Patch[\s\S]*?\*\*\* End Patch)\s*```",
    re.MULTILINE,
)


def _extract_patch(text: str) -> str | None:
    """
    Извлекает блок патча из ответа LLM.
    Блок обычно ограничен *** Begin Patch и *** End Patch.
    """
    m = PATCH_FENCE_RE.search(text)
    if m:
        return m.group(1)
    m = PATCH_RE.search(text)
    return m.group(0).strip() if m else None


def _normalize_patch(patch_text: str) -> str:
    """
    Нормализует текст патча, допуская типичные ошибки формата модели.
    - Принимает 'Delete File:' / 'Update File:' / 'Add File:' (даже без ведущего '*** ')
    - Сохраняет стандартный формат Codex, требуемый исполнителем.
    """
    lines = patch_text.splitlines()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("Add File:", "Update File:", "Delete File:")) and not stripped.startswith("*** "):
            out.append("*** " + stripped)
            continue
        out.append(line)
    return "\n".join(out)


def _patch_requires_confirmation(patch_text: str) -> bool:
    """
    Определяет, нужно ли подтверждение пользователя.
    Стратегия:
    - есть удаление файлов
    - слишком много файлов (>= 6)
    - слишком много изменённых строк (>= 400)
    """
    if "*** Delete File:" in patch_text:
        return True
    file_ops = patch_text.count("*** Add File:") + patch_text.count("*** Update File:") + patch_text.count("*** Delete File:")
    if file_ops >= 6:
        return True
    changed_lines = 0
    for line in patch_text.splitlines():
        if line.startswith("+") or line.startswith("-"):
            changed_lines += 1
    return changed_lines >= 400


def main(argv: list[str] | None = None) -> int:
    """
    Точка входа CLI.
    Инициализирует LLM, CodeAgent и PatchExecutor и запускает интерактивный цикл.
    """
    parser = argparse.ArgumentParser(description="HelloAgents-style Code Agent CLI (Codex/Claude-like)")
    parser.add_argument("--repo", type=str, default=".", help="Корень репозитория (workspace). По умолчанию: .")
    parser.add_argument("--project", type=str, default=None, help="Имя проекта (по умолчанию: имя папки репозитория)")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo).resolve()
    load_dotenv(dotenv_path=repo_root / ".env", override=False)

    project = args.project or repo_root.name
    config = Config.from_env()
    llm = HelloAgentsLLM()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("openai._base_client").setLevel(logging.WARNING)
    logging.getLogger("memory").setLevel(logging.WARNING)

    print(c(hr("=", 80), INFO))
    print(c("HelloAgents Code Agent CLI", PRIMARY))
    print(c(f"workspace: {repo_root}", INFO))
    print(c(f"LLM: provider={llm.provider} model={llm.model} base_url={llm.base_url}", INFO))
    print(c(f"state: {Path(config.helloagents_dir).as_posix()}", INFO))
    print(c(hr("=", 80), INFO))

    try:
        _ = llm.invoke([{"role": "user", "content": "ping"}], max_tokens=1)
    except HelloAgentsException as e:
        print(c("Предварительная проверка LLM не прошла (обычно проблема API key/base_url/model).", ERROR))
        print(c(f"error: {e}", ERROR))
        print(c("Проверьте DEEPSEEK_API_KEY / LLM_* в .env.", WARN))
        return 2

    agent = CodeAgent(repo_root=repo_root, llm=llm, config=config)
    patch_executor = ApplyPatchExecutor(repo_root=repo_root)

    print(c("Введите запрос на естественном языке. Команды:", INFO))
    print(c("  :quit", ACCENT) + c(" выход", INFO))
    print(c("  :plan <цель>", ACCENT) + c(" принудительно сгенерировать план", INFO))
    while True:
        try:
            user_in = input(c("👤 > ", PRIMARY))
        except (EOFError, KeyboardInterrupt):
            print("\n" + c("bye", INFO))
            return 0

        if user_in is None:
            continue
        user_in = user_in.strip()
        if not user_in:
            print(c("Укажите конкретную инструкцию или вопрос.", WARN))
            continue
        if user_in in {":q", ":quit", "quit", "exit"}:
            print(c("bye", INFO))
            return 0
        if user_in.startswith(":plan"):
            goal = user_in[len(":plan") :].strip() or "Сгенерируй исполнимый план для текущей задачи"
            response = agent.registry.execute_tool("plan", goal)
            print("\n" + c("🤖 plan", PRIMARY))
            print(response + "\n")
            continue

        try:
            response = agent.run_turn(user_in)
        except HelloAgentsException as e:
            print(c(f"Вызов LLM не удался: {e}", ERROR))
            continue

        if getattr(agent, "last_direct_reply", False):
            print(c("🤖 assistant", PRIMARY))
            print(response)
        
        patch_text = _extract_patch(response)
        if not patch_text:
            continue
        patch_text = _normalize_patch(patch_text)
        if patch_text.strip() == "*** Begin Patch\n*** End Patch":
            continue

        needs_confirm = _patch_requires_confirmation(patch_text)
        if needs_confirm:
            if user_in.strip().lower() in {"n", "no"}:
                print("Применение патча отменено.")
                continue
            if user_in.strip().lower() not in {"y", "yes"}:
                print("\n⚠️ Обнаружен рискованный патч (удаление/массовые изменения). Применить? (y/n)")
                ans = input("confirm> ").strip().lower()
                if ans not in {"y", "yes"}:
                    print("Применение патча отменено.")
                    continue

        try:
            res = patch_executor.apply(patch_text)
            print("\n" + c("✅ Patch applied", PRIMARY))
            print(c(f"files: {', '.join(res.files_changed) if res.files_changed else '(none)'}", INFO))
            if res.backups:
                print(c(f"backups: {len(res.backups)} (in .helloagents/backups/...)", INFO))

            agent.note_tool.run({
                "action": "create",
                "title": "Patch applied",
                "content": f"User input:\n{user_in}\n\nPatch:\n\n```text\n{patch_text}\n```\n\nFiles:\n"
                + "\n".join([f"- {p}" for p in res.files_changed]),
                "note_type": "action",
                "tags": [project, "patch_applied"],
            })
        except PatchApplyError as e:
            print("\n" + c(f"❌ Patch failed: {e}", ERROR))
            agent.note_tool.run({
                "action": "create",
                "title": "Patch failed",
                "content": f"Error: {e}\n\nUser input:\n{user_in}\n\nPatch:\n\n```text\n{patch_text}\n```\n",
                "note_type": "blocker",
                "tags": [project, "patch_failed"],
            })
            continue

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
