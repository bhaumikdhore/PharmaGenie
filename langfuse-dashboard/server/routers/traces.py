"""
Traces router — thin proxy into the Langfuse REST API.
Lets you query traces from your own backend without
exposing Langfuse secret keys to the frontend.
"""
from __future__ import annotations

from typing import Any

import httpx
import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from config import get_settings

router = APIRouter()
log = structlog.get_logger()
settings = get_settings()

# Basic-auth for Langfuse public API
_AUTH = (settings.langfuse_public_key, settings.langfuse_secret_key)
_BASE = settings.langfuse_host.rstrip("/")


async def _lf_get(path: str, params: dict | None = None) -> Any:
    url = f"{_BASE}{path}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, auth=_AUTH, params=params)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


@router.get("", summary="List recent traces")
async def list_traces(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str | None = None,
    session_id: str | None = None,
    tags: str | None = Query(None, description="Comma-separated tag filter"),
) -> Any:
    params: dict[str, Any] = {"page": page, "limit": limit}
    if user_id:
        params["userId"] = user_id
    if session_id:
        params["sessionId"] = session_id
    if tags:
        params["tags"] = tags
    return await _lf_get("/api/public/traces", params=params)


@router.get("/{trace_id}", summary="Get a single trace by ID")
async def get_trace(trace_id: str) -> Any:
    return await _lf_get(f"/api/public/traces/{trace_id}")


@router.get("/{trace_id}/observations", summary="Get all observations (spans) for a trace")
async def get_observations(trace_id: str) -> Any:
    return await _lf_get("/api/public/observations", params={"traceId": trace_id})
