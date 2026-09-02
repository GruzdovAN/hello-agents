"""API потокового анализа данных AI — согласованный путь решения"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.agent_api import AnalysisRequest, iter_data_analysis_ndjson

router = APIRouter(prefix="/data-analysis", tags=["AI数据分析"])


@router.post("/analyze/stream")
async def data_analysis_analyze_stream(body: AnalysisRequest):
    """POST /api/v1/data-analysis/analyze/stream"""
    return StreamingResponse(
        iter_data_analysis_ndjson(body.stock_code, body.stock_name),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
