"""Настройка маршрутизации API"""
import json
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from ..workspace.manager import WorkspaceManager, get_default_global_config

router = APIRouter(prefix="/config", tags=["config"])


class ConfigUpdateRequest(BaseModel):
    """Запрос на обновление конфигурации"""
    content: str


class AgentInfo(BaseModel):
    """Информация о помощнике"""
    name: str


# Экземпляр глобальной рабочей области (устанавливается при запуске main.py)

_workspace: Optional[WorkspaceManager] = None


def set_workspace(ws: WorkspaceManager):
    """Настройка экземпляра глобальной рабочей области"""
    global _workspace
    _workspace = ws


def get_workspace() -> WorkspaceManager:
    """Получить экземпляр рабочей области"""
    if _workspace is None:
        ws = WorkspaceManager(os.getenv("WORKSPACE_PATH", "~/.helloclaw/workspace"))
        ws.ensure_workspace_exists()
        set_workspace(ws)
    return _workspace


def get_config_json_path() -> str:
    """Получите глобальный путь config.json"""
    return os.path.expanduser("~/.helloclaw/config.json")


def ensure_config_json_exists():
    """Убедитесь, что config.json существует."""
    config_path = get_config_json_path()
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(get_default_global_config(), f, indent=2, ensure_ascii=False)


@router.get("/list")
async def list_configs(ws: WorkspaceManager = Depends(get_workspace)):
    """Получить Список конфигурационных файлов"""
    configs = ws.list_configs()

    # Добавьте config.json в начало списка.

    configs.insert(0, "CONFIG")
    return {"configs": configs}


@router.get("/{name}")
async def get_config(name: str, ws: WorkspaceManager = Depends(get_workspace)):
    """Получить содержимое указанного файла конфигурации"""
    # Специальная обработка CONFIG (config.json)

    if name == "CONFIG":
        ensure_config_json_exists()
        config_path = get_config_json_path()
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"name": name, "content": content}

    # Обработка файлов конфигурации .md

    content = ws.load_config(name)
    if content is None:
        raise HTTPException(status_code=404, detail=f"файл конфигурации {name} не существует")
    return {"name": name, "content": content}


@router.put("/{name}")
async def update_config(name: str, request: ConfigUpdateRequest, ws: WorkspaceManager = Depends(get_workspace)):
    """Обновить файл конфигурации"""
    # Специальная обработка CONFIG (config.json)

    if name == "CONFIG":
        ensure_config_json_exists()
        # Строго проверяйте формат JSON.

        try:
            config_data = json.loads(request.content)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Неверный формат JSON: {str(e)}")

        # Проверьте обязательные поля

        if not isinstance(config_data, dict):
            raise HTTPException(status_code=400, detail="Конфигурация должна быть JSON-объектом")

        if "llm" not in config_data:
            raise HTTPException(status_code=400, detail="Отсутствует обязательное поле: llm")

        llm_config = config_data.get("llm", {})
        required_fields = ["model_id", "api_key", "base_url"]
        missing_fields = [f for f in required_fields if f not in llm_config]
        if missing_fields:
            raise HTTPException(status_code=400, detail=f"llm В конфигурации нет обязательных полей: {', '.join(missing_fields)}")

        config_path = get_config_json_path()
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(request.content)
        return {"name": name, "status": "updated"}

    # Обработка файлов конфигурации .md

    if name not in ws.list_configs():
        raise HTTPException(status_code=404, detail=f"файл конфигурации {name} не существует")

    ws.save_config(name, request.content)
    return {"name": name, "status": "updated"}


def get_agent():
    """Получить глобальный экземпляр агента"""
    from ..main import get_agent as _get_agent
    return _get_agent()


@router.post("/reset")
async def reset_workspace(
    reset_sessions: bool = False,
    reset_memory: bool = False,
    reset_global_config: bool = False,
    ws: WorkspaceManager = Depends(get_workspace)
):
    """Сброс к начальным шаблонам

    Args:
        reset_sessions: Очистить сессии
        reset_memory: Очистить ежедневную память
        reset_global_config: Сбросить глобальный конфиг

    Внимание: перезапись всех конфигов!
    """
    try:
        ws.reset_to_templates(
            reset_sessions=reset_sessions,
            reset_memory=reset_memory,
            reset_global_config=reset_global_config
        )

        # Если вы очистите сеанс, также очистите историю в памяти агента.

        if reset_sessions:
            agent = get_agent()
            if agent:
                agent.clear_all_history()

        messages = ["Файл конфигурации сброшен"]
        if reset_sessions:
            messages.append("Сессия очищена")
        if reset_memory:
            messages.append("дневнаяпамятьуже清除")
        if reset_global_config:
            messages.append("глобальныйконфигурацияужесброс")

        return {"status": "success", "message": "，".join(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"сбросошибка: {str(e)}")


@router.get("/agent/info", response_model=AgentInfo)
async def get_agent_info(ws: WorkspaceManager = Depends(get_workspace)):
    """Получить информацию об помощнике (включая имя)

    Перечитывайте IDENTITY.md каждый раз, чтобы узнать последнее имя."""
    # Прочитайте последнее имя на IDENTITY.md

    identity = ws.load_config("IDENTITY")
    name = "HelloClaw"  # имя по умолчанию


    if identity:
        import re
        # Формат соответствия: - **имя:** xxx или - **имя:** xxx

match = re.search(r'\*\*Name[::]\*\*\s*(.+?)(?:\n|$)', тождество)
        if match:
            name = match.group(1).strip()
            # Проверьте, является ли это заполнителем

            if name.startswith('_') or '选一个' in name or '（' in name:
                name = "HelloClaw"

    return AgentInfo(name=name)
