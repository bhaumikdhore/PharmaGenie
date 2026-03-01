"""
Feedback router — lets the frontend submit user ratings / corrections for any LLM trace.
Scores are written back to Langfuse so they appear in the dashboard.
"""
from __future__ import annotations

from typing import Any, Literal

import httpx
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config import get_settings

router = APIRouter()
log = structlog.get_logger()
settings = get_settings()

_AUTH = (settings.langfuse_public_key, settings.langfuse_secret_key)
_BASE = settings.langfuse_host.rstrip("/")


class FeedbackRequest(BaseModel):
    trace_id: str = Field(..., description="Langfuse trace_id to attach score to")
    score: float = Field(..., ge=0, le=1, description="0.0 = very bad, 1.0 = perfect")
    name: str = Field("user-feedback", description="Score name shown in dashboard")
    comment: str | None = None
    data_type: Literal["NUMERIC", "BOOLEAN", "CATEGORICAL"] = "NUMERIC"


@router.post("", summary="Submit user feedback for a trace")
async def post_feedback(req: FeedbackRequest) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "traceId": req.trace_id,
        "name": req.name,
        "value": req.score,
        "dataType": req.data_type,
    }
    if req.comment:
        payload["comment"] = req.comment

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{_BASE}/api/public/scores",
                auth=_AUTH,
                json=payload,
            )
            if r.status_code >= 400:
                raise HTTPException(status_code=r.status_code, detail=r.text)
            log.info("feedback_submitted", trace_id=req.trace_id, score=req.score)
            return {"ok": True, "score_id": r.json().get("id")}
    except HTTPException:
        raise
    except Exception as exc:
        log.error("feedback_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
