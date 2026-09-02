"""
Сценарий Desktop/exe: серверная часть вызывает системный браузер по умолчанию для открытия внешних ссылок.

部分环境下前端 window.open 会被拦截；与 run_exe.py 中 webbrowser.open 打开仪表盘一致。
"""

from __future__ import annotations

import asyncio
import webbrowser
from urllib.parse import urlparse

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.utils.response import error_response, success_response

router = APIRouter(prefix="/system", tags=["system"])


class OpenExternalUrlBody(BaseModel):
    url: str = Field(..., min_length=8, max_length=4096)


def _normalize_http_url(url: str) -> str | None:
    s = url.strip()
    if len(s) > 4096:
        return None
    parsed = urlparse(s)
    if parsed.scheme not in ("http", "https"):
        return None
    if not parsed.netloc:
        return None
    return s


@router.post("/open-external-url")
async def open_external_url(body: OpenExternalUrlBody):
"""Откройте ссылку http(s) в локальном браузере по умолчанию."""
    ok_url = _normalize_http_url(body.url)
    if not ok_url:
        return error_response(400, "仅允许有效的 http(s) 外链")

    opened = await asyncio.to_thread(webbrowser.open, ok_url)
    return success_response(data={"opened": bool(opened)})
