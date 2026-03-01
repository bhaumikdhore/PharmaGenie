"""
Health router — checks connectivity to Langfuse and Redis.
"""
from __future__ import annotations

import httpx
import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from config import get_settings

router = APIRouter()
log = structlog.get_logger()
settings = get_settings()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    langfuse: str
    redis: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    # ── Langfuse reachability ──────────────────────────────────────────────
    langfuse_status = "unreachable"
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            r = await client.get(f"{settings.langfuse_host}/api/public/health")
            langfuse_status = "ok" if r.status_code < 400 else f"http_{r.status_code}"
    except Exception as exc:
        log.warning("langfuse_health_failed", error=str(exc))

    # ── Redis reachability (optional) ────────────────────────────────────────
    redis_status = "disabled"
    if settings.redis_url:
        try:
            r_client = aioredis.from_url(settings.redis_url, socket_connect_timeout=3)
            await r_client.ping()
            await r_client.aclose()
            redis_status = "ok"
        except Exception as exc:
            log.warning("redis_health_failed", error=str(exc))
            redis_status = "unreachable"

    redis_ok = redis_status in ("ok", "disabled")
    overall = "ok" if langfuse_status == "ok" and redis_ok else "degraded"
    return HealthResponse(
        status=overall,
        service=settings.app_name,
        version=settings.app_version,
        langfuse=langfuse_status,
        redis=redis_status,
    )
