import asyncio
import time
from fastapi import APIRouter, Query
from app.ai.llm import llm

router = APIRouter(prefix="/llm")

@router.get("/test")
async def test_llm(
    prompt: str = Query(default="Explain a pharmacy inventory system in 2 short lines."),
    timeout_seconds: int = Query(default=60, ge=3, le=120),
):
    started = time.perf_counter()

    try:
        response = await asyncio.wait_for(llm.ainvoke(prompt), timeout=timeout_seconds)
        return {
            "response": getattr(response, "content", str(response)),
            "source": "ollama",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except asyncio.TimeoutError:
        return {
            "response": f"LLM timed out after {timeout_seconds}s.",
            "source": "fallback",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except Exception as exc:
        return {
            "response": f"LLM unavailable: {exc.__class__.__name__}",
            "source": "fallback",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }

@router.get("/test2")
async def test_llm2():
    response = await llm.ainvoke("Explain pharmacy inventory in 3 lines.")
    return {"response": response.content}
