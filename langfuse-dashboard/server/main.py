"""
PharmaGenie Observability API Server
=====================================
Separate FastAPI service running on port 8001.
Wraps LangChain agent execution and streams every trace to Langfuse.

Endpoints
---------
GET  /                          Health ping
GET  /health                    Detailed health (langfuse + redis)
POST /run/safety-check          Safety-check agent (traced)
POST /run/prescription-analysis Prescription analysis agent (traced)
POST /run/drug-interaction      Drug-interaction check agent (traced)
POST /run/planner               Pharmacy planner agent (traced)
POST /run/custom                Run a custom prompt chain (traced)
GET  /traces                    List recent traces from Langfuse
GET  /traces/{trace_id}         Get a single trace
GET  /metrics/summary           Aggregated cost / latency / error stats
POST /feedback                  Submit user feedback on a trace
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import get_settings
from middleware.tracing import TracingMiddleware
from routers import health, traces, agents, metrics, feedback

# ── Logging setup ─────────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger()

settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(
        "PharmaGenie Observability Server starting",
        langfuse_host=settings.langfuse_host,
        version=settings.app_version,
    )
    yield
    log.info("Observability server shutting down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "LangChain + Langfuse observability layer for PharmaGenie AI Agents. "
        "Every agent run is traced and visible in the Langfuse dashboard at "
        "http://localhost:3100"
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Tracing middleware ────────────────────────────────────────────────────────
app.add_middleware(TracingMiddleware)

# ── Static files (dashboard UI) ──────────────────────────────────────────────
_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router,    tags=["Health"])
app.include_router(agents.router,    prefix="/run",     tags=["Agent Runs"])
app.include_router(traces.router,    prefix="/traces",  tags=["Traces"])
app.include_router(metrics.router,   prefix="/metrics", tags=["Metrics"])
app.include_router(feedback.router,  prefix="/feedback", tags=["Feedback"])


@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    """Serve the local observability dashboard UI."""
    return FileResponse(str(_static_dir / "index.html"), media_type="text/html")


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to the dashboard."""
    return RedirectResponse(url="/dashboard")
