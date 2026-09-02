from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class PatchApplyError(RuntimeError):
    """
    Исключение при применении патча.
    Содержит причину сбоя и цели для повторной проверки.
    
    Параметры:
        message: описание ошибки
        recheck_targets: список целей для отладки патча
    """
    def __init__(self, message: str, recheck_targets: Optional[List[str]] = None):
        super().__init__(message)
        self.recheck_targets = recheck_targets or []


@dataclass
class ApplyResult:
    """
    Результат применения патча.
    Изменённые файлы и бэкапы.
    
    Поля:
        files_changed: относительные пути изменённых файлов
        backups: абсолютные пути бэкапов
    """
    files_changed: List[str]
    backups: List[str]


class ApplyPatchExecutor:
    """
    Применяет патчи формата *** Begin Patch (Codex).

    Безопасность (MVP):
    - ограничение repo_root (защита от path traversal)
    - атомарная запись через tempfile + os.replace
    - бэкап в <repo_root>/.helloagents/backups/<timestamp>/
    - лимиты: число файлов и строк изменений
    - точное сопоставление контекста в Update File
    """

    def __init__(
        self,
        repo_root: Path,
        max_files: int = 10,
        max_total_changed_lines: int = 800,
        allowed_write_suffixes: Optional[List[str]] = None,
    ):
        """
        Инициализация исполнителя патчей.
        
        Параметры:
            repo_root: корень репозитория, все операции только внутри
            max_files: макс. файлов в одном патче (10)
            max_total_changed_lines: макс. изменённых строк (800)
            allowed_write_suffixes: разрешённые суффиксы файлов
        """
        self.repo_root = repo_root
        self.max_files = max_files
        self.max_total_changed_lines = max_total_changed_lines
        
        # Суффиксы текстовых файлов, защита от бинарников
        self.allowed_write_suffixes = allowed_write_suffixes or [
            ".py",
            ".md",
            ".toml",
            ".json",
            ".yml",
            ".yaml",
            ".txt",
            ".html",
            ".htm",
            ".css",
            ".js",
        ]

        # Рабочий и backup-каталоги
        self.root_dir = repo_root / ".helloagents"
        self.backups_dir = self.root_dir / "backups"
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def apply(self, patch_text: str) -> ApplyResult:
        """
        Разбирает и применяет патч.
        
        Порядок:
        1. Разбор операций Add/Update/Delete
        2. Проверка лимитов
        3. Каталог бэкапа
        4. Операции (сначала бэкап)
        
        Параметры:
            patch_text: Текст патча от *** Begin Patch до *** End Patch
            
        Returns:
            ApplyResult: ApplyResult с файлами и бэкапами
            
        Raises:
            PatchApplyError: если формат неверен, лимиты превышены или сбой
        """
        # Разбор патча
        ops = self._parse_patch(patch_text)
        
        # Лимит файлов
        touched_files = [op[1] for op in ops if op[0] in {"add", "update", "delete"}]
        if len(set(touched_files)) > self.max_files:
            raise PatchApplyError(f"Too many files in patch: {len(set(touched_files))} > {self.max_files}")

        # Лимит строк
        total_changed = self._estimate_changed_lines(ops)
        if total_changed > self.max_total_changed_lines:
            raise PatchApplyError(f"Patch too large: {total_changed} changed lines > {self.max_total_changed_lines}")

        # Каталог бэкапа с меткой времени
        backup_run_dir = self.backups_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_run_dir.mkdir(parents=True, exist_ok=True)

        # Сбор результатов
        files_changed: List[str] = []  # Изменённые файлы
        backups: List[str] = []  # Пути бэкапов

        # Выполнение операций
        for kind, rel_path, payload in ops:
            # Проверка пути в repo_root
            target = self._safe_path(rel_path)
            
            # Проверка суффикса
            self._enforce_suffix(target)

            if kind == "add":
                # Add File
                if target.exists():
                    raise PatchApplyError(f"Add File target already exists: {rel_path}")
                # mkdir parents
                target.parent.mkdir(parents=True, exist_ok=True)
                # Атомарная запись
                self._atomic_write(target, payload)
                # Учёт изменений
                files_changed.append(rel_path)
                
            elif kind == "delete":
                # Delete File
                if not target.exists():
                    raise PatchApplyError(f"Delete File target missing: {rel_path}")
                # Бэкап перед удалением
                b = self._backup_file(target, backup_run_dir)
                backups.append(str(b))
                # Удаление файла
                target.unlink()
                # Учёт изменений
                files_changed.append(rel_path)
                
            elif kind == "update":
                # Update File
                if not target.exists():
                    raise PatchApplyError(f"Update File target missing: {rel_path}")
                # Чтение с keepends
                original = target.read_text(encoding="utf-8").splitlines(keepends=True)
                # Бэкап перед update
                b = self._backup_file(target, backup_run_dir)
                backups.append(str(b))
                # Применение hunk
                updated = self._apply_update_payload(original, payload, rel_path)
                # Атомарная запись
                self._atomic_write(target, "".join(updated))
                # Учёт изменений
                files_changed.append(rel_path)
                
            else:
                # Неизвестная операция
                raise PatchApplyError(f"Unknown op kind: {kind}")

        # Итог
        return ApplyResult(files_changed=files_changed, backups=backups)

    def _safe_path(self, rel_path: str) -> Path:
        """
        Проверка пути (Path Traversal).
        Путь должен оставаться в repo_root.
        
        Параметры:
            rel_path: относительный путь
            
        Returns:
            Path: безопасный Path
            
        Raises:
            PatchApplyError: если абсолютный путь или выход за repo_root
        """
        if rel_path.startswith("/") or rel_path.startswith("~"):
            raise PatchApplyError(f"Absolute paths are not allowed: {rel_path}")
        target = (self.repo_root / rel_path).resolve()
        # resolve().startswith(repo_root)
        if not str(target).startswith(str(self.repo_root.resolve()) + os.sep) and target != self.repo_root.resolve():
            raise PatchApplyError(f"Path escapes repo_root: {rel_path}")
        if target.exists() and target.is_symlink():
            raise PatchApplyError(f"Refusing to modify symlink: {rel_path}")
        return target

    def _enforce_suffix(self, target: Path) -> None:
        """
        Проверка суффикса файла.
        Защита от бинарников и чувствительных файлов.
        
        Параметры:
            target: Path цели
            
        Raises:
            PatchApplyError: если суффикс не в whitelist
        """
        if target.suffix and target.suffix not in self.allowed_write_suffixes:
            raise PatchApplyError(f"Disallowed file suffix for write: {target.suffix}")

    def _backup_file(self, target: Path, backup_run_dir: Path) -> Path:
        """
        Бэкап файла.
        Та же относительная структура + .bak
        
        Параметры:
            target: файл для бэкапа
            backup_run_dir: каталог бэкапа
            
        Returns:
            Path: путь к .bak
        """
        # relative_to(repo_root)
        rel = target.relative_to(self.repo_root)
        # путь бэкапа
        backup_path = backup_run_dir / (str(rel) + ".bak")
        # mkdir parents
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        # копирование
        backup_path.write_bytes(target.read_bytes())
        return backup_path

    def _atomic_write(self, target: Path, content: str) -> None:
        """
        Атомарная запись.
        tempfile + os.replace против повреждения при сбое.
        
        Параметры:
            target: Path
            content: содержимое
        """
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=str(target.parent), encoding="utf-8") as tf:
            tf.write(content)
            tf.flush()
            os.fsync(tf.fileno())
            tmp_name = tf.name
        os.replace(tmp_name, target)

    def _parse_patch(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Парсер патча.
        Операции:
        - *** Add File: <path>
        - *** Delete File: <path>
        - *** Update File: <path>
        
        Параметры:
            text: текст патча
            
        Returns:
            List[Tuple[str, str, str]]: список (kind, path, payload)
            
        Raises:
            PatchApplyError: неверный формат
        """
        lines = text.splitlines()
        # Пропуск пустых строк и ```
        while lines and lines[0].strip() in {"", "```", "```patch", "```diff", "```text"}:
            lines = lines[1:]
        # Поиск *** Begin Patch
        if lines and lines[0].strip() != "*** Begin Patch":
            for idx, l in enumerate(lines):
                if l.strip() == "*** Begin Patch":
                    lines = lines[idx:]
                    break
        if not lines or lines[0].strip() != "*** Begin Patch":
            raise PatchApplyError("Patch must start with '*** Begin Patch'")
        # Пропуск хвоста
        while lines and lines[-1].strip() in {"", "```"}:
            lines = lines[:-1]
        if not lines or lines[-1].strip() != "*** End Patch":
            # Поиск *** End Patch
            for idx in range(len(lines) - 1, -1, -1):
                if lines[idx].strip() == "*** End Patch":
                    lines = lines[: idx + 1]
                    break
        if not lines or lines[-1].strip() != "*** End Patch":
            raise PatchApplyError("Patch must end with '*** End Patch'")

        ops: List[Tuple[str, str, str]] = []
        i = 1
        while i < len(lines) - 1:
            line = lines[i]
            if line.startswith("*** Add File: "):
                path = line[len("*** Add File: ") :].strip()
                i += 1
                buf: List[str] = []
                while i < len(lines) - 1 and not lines[i].startswith("*** "):
                    # Форматы:
                    # 1) строки с +
                    # 2) без '+' (модель)
                    if lines[i].startswith("+"):
                        buf.append(lines[i][1:] + "\n")
                    else:
                        buf.append(lines[i] + "\n")
                    i += 1
                ops.append(("add", path, "".join(buf)))
                continue
            if line.startswith("*** Delete File: "):
                path = line[len("*** Delete File: ") :].strip()
                ops.append(("delete", path, ""))
                i += 1
                continue
            if line.startswith("*** Update File: "):
                path = line[len("*** Update File: ") :].strip()
                i += 1
                buf: List[str] = []
                while i < len(lines) - 1 and not lines[i].startswith("*** "):
                    buf.append(lines[i])
                    i += 1
                ops.append(("update", path, "\n".join(buf)))
                continue
            if line.strip() == "":
                i += 1
                continue
            raise PatchApplyError(f"Unexpected patch line: {line}")

        return ops

    def _estimate_changed_lines(self, ops: List[Tuple[str, str, str]]) -> int:
        """
        Оценка числа изменённых строк.
        Проверка лимита размера.
        
        Параметры:
            ops: список ops
            
        Returns:
            int: число строк
        """
        changed = 0
        for kind, _, payload in ops:
            if kind == "add":
                # add: по \n
                changed += payload.count("\n")
            elif kind == "delete":
                # delete: 1 строка
                changed += 1
            elif kind == "update":
                # update: +/- строки
                for l in payload.splitlines():
                    if l.startswith("+") or l.startswith("-"):
                        changed += 1
        return changed

    def _apply_update_payload(self, original: List[str], payload: str, rel_path: str) -> List[str]:
        """
        Применяет payload Update File.
        Разбивает на hunks и применяет.
        """
        # Без +/- — полная замена файла
        raw_lines = payload.splitlines(keepends=True)
        if raw_lines and all(not l.startswith(("+", "-", " ")) for l in raw_lines):
            return raw_lines

        hunks = self._split_hunks(payload)
        current = original
        try:
            for hunk in hunks:
                current = self._apply_hunk(current, hunk, rel_path)
            return current
        except PatchApplyError as e:
            # fallback: полная замена файла при сбое контекста
            if "context not found" not in str(e).lower():
                raise
            fallback = self._hunks_to_after(hunks)
            if fallback:
                return fallback
            raise

    def _split_hunks(self, payload: str) -> List[List[str]]:
        """
        Разбивает payload на hunks.
        Разделители @@ или пустые строки.
        Один фрагмент изменения.
        
        Параметры:
            payload: payload update
            
        Returns:
            List[List[str]]: список hunks
        """
        lines = payload.splitlines()
        hunks: List[List[str]] = []
        buf: List[str] = []
        for l in lines:
            if l.startswith("@@"):
                if buf:
                    hunks.append(buf)
                    buf = []
                continue
            if l.strip() == "" and buf:
                hunks.append(buf)
                buf = []
                continue
            buf.append(l)
        if buf:
            hunks.append(buf)
        return [h for h in hunks if any(x.startswith((" ", "+", "-")) for x in h)]

    def _apply_hunk(self, current: List[str], hunk_lines: List[str], rel_path: str) -> List[str]:
        """
        Применяет один hunk.
        
        Алгоритм:
        1. before/after из +/- и контекста
        2. Поиск before в файле
        3. Замена before на after
        4. Иначе ошибка
        
        Параметры:
            current: строки файла
            hunk_lines: строки hunk
            rel_path: rel_path для ошибок
            
        Returns:
            List[str]: обновлённые строки
            
        Raises:
            PatchApplyError: неверный hunk или нет контекста
        """
        before: List[str] = []
        after: List[str] = []
        for l in hunk_lines:
            if not l:
                continue
            tag = l[0]
            text = l[1:] + "\n"
            if tag == " ":
                before.append(text)
                after.append(text)
            elif tag == "-":
                before.append(text)
            elif tag == "+":
                after.append(text)

        if not before:
            raise PatchApplyError("Update hunk has no context/removals; refusing to apply")

        idx = self._find_subsequence(current, before)
        if idx is None:
            context_line = next((b.strip() for b in before if b.strip()), "")
            hint = f"{rel_path}:search:'{context_line[:80]}'"
            raise PatchApplyError("Patch hunk context not found; file changed?", recheck_targets=[hint])

        return current[:idx] + after + current[idx + len(before) :]

    def _find_subsequence(self, haystack: List[str], needle: List[str]) -> Optional[int]:
        """
        Поиск подпоследовательности.
        O(N*M) точное совпадение.
        
        Параметры:
            haystack: haystack
            needle: needle
            
        Returns:
            Optional[int]: индекс или None
        """
        if len(needle) > len(haystack):
            return None
        for i in range(0, len(haystack) - len(needle) + 1):
            if haystack[i : i + len(needle)] == needle:
                return i
        # Повтор без хвостовых пробелов
        norm_hay = [h.rstrip() + "\n" for h in haystack]
        norm_need = [n.rstrip() + "\n" for n in needle]
        for i in range(0, len(norm_hay) - len(norm_need) + 1):
            if norm_hay[i : i + len(norm_need)] == norm_need:
                return i
        return None

    def _hunks_to_after(self, hunks: List[List[str]]) -> List[str]:
        """
        Собирает after из hunks.
        Fallback: + и пробел, без -.
        """
        out: List[str] = []
        for hunk in hunks:
            for l in hunk:
                if not l:
                    continue
                tag = l[0]
                text = l[1:] + "\n" if len(l) > 1 else "\n"
                if tag == "-" or tag == "@":
                    continue
                if tag in (" ", "+"):
                    out.append(text)
        return out
