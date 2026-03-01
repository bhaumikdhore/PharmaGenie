"""
Metrics router — aggregates cost, latency, and error stats from Langfuse.
"""
from __future__ import annotations

from typing import Any

import httpx
import structlog
from fastapi import APIRouter, HTTPException, Query

from config import get_settings

router = APIRouter()
log = structlog.get_logger()
settings = get_settings()

_AUTH = (settings.langfuse_public_key, settings.langfuse_secret_key)
_BASE = settings.langfuse_host.rstrip("/")


async def _lf_get(path: str, params: dict | None = None) -> Any:
    url = f"{_BASE}{path}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, auth=_AUTH, params=params)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


@router.get("/summary", summary="Aggregated cost, latency, and error summary")
async def metrics_summary(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
) -> dict[str, Any]:
    """
    Pulls recent traces from Langfuse and computes basic aggregations:
    - total runs per agent type (by trace name)
    - average latency
    - total estimated USD cost
    - error rate
    """
    try:
        data = await _lf_get("/api/public/traces", params={"limit": 200, "page": 1})
        traces: list[dict] = data.get("data", [])

        total = len(traces)
        errors = sum(1 for t in traces if t.get("level") == "ERROR")
        latencies = [t["latency"] for t in traces if t.get("latency") is not None]
        costs = [t.get("totalCost", 0) or 0 for t in traces]

        by_name: dict[str, int] = {}
        for t in traces:
            name = t.get("name", "unknown")
            by_name[name] = by_name.get(name, 0) + 1

        return {
            "period_days": days,
            "total_runs": total,
            "error_count": errors,
            "error_rate_pct": round(errors / total * 100, 2) if total else 0,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "total_cost_usd": round(sum(costs), 6),
            "runs_by_agent": by_name,
        }
    except HTTPException:
        raise
    except Exception as exc:
        log.error("metrics_summary_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
