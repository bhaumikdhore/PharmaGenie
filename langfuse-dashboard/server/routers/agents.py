"""
Agent-run router — every endpoint runs a LangChain chain and auto-traces to Langfuse.
"""
from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from integrations.pharmagenie import (
    run_safety_check,
    run_prescription_analysis,
    run_drug_interaction_check,
    run_planner,
    run_custom_chain,
)

router = APIRouter()
log = structlog.get_logger()


# ── Request / Response models ─────────────────────────────────────────────────

class SafetyCheckRequest(BaseModel):
    medicine_name: str
    dosage: str = "standard"
    patient_notes: str = ""
    session_id: str | None = None
    user_id: str | None = None


class PrescriptionAnalysisRequest(BaseModel):
    prescription_text: str = Field(
        ..., description="Raw text or OCR output of a prescription"
    )
    session_id: str | None = None
    user_id: str | None = None


class DrugInteractionRequest(BaseModel):
    medicines: list[str] = Field(..., min_length=2, description="At least 2 medicine names")
    session_id: str | None = None
    user_id: str | None = None


class PlannerRequest(BaseModel):
    history: str = Field(..., description="Customer purchase history text")
    prescription: str = Field(..., description="Current prescription text")
    budget: str = "no preference"
    session_id: str | None = None
    user_id: str | None = None


class CustomChainRequest(BaseModel):
    system_prompt: str
    user_message: str
    temperature: float = 0.5
    trace_name: str = "custom-chain"
    tags: list[str] = []
    session_id: str | None = None
    user_id: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/safety-check", summary="Medicine safety check (traced)")
async def safety_check(req: SafetyCheckRequest) -> dict[str, Any]:
    try:
        result = await run_safety_check(
            medicine_name=req.medicine_name,
            dosage=req.dosage,
            patient_notes=req.patient_notes,
            session_id=req.session_id,
            user_id=req.user_id,
        )
        log.info("safety_check_done", medicine=req.medicine_name)
        return {"ok": True, "result": result}
    except Exception as exc:
        log.error("safety_check_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/prescription-analysis", summary="Analyse a prescription (traced)")
async def prescription_analysis(req: PrescriptionAnalysisRequest) -> dict[str, Any]:
    try:
        result = await run_prescription_analysis(
            prescription_text=req.prescription_text,
            session_id=req.session_id,
            user_id=req.user_id,
        )
        log.info("prescription_analysis_done")
        return {"ok": True, "result": result}
    except Exception as exc:
        log.error("prescription_analysis_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/drug-interaction", summary="Drug interaction check (traced)")
async def drug_interaction(req: DrugInteractionRequest) -> dict[str, Any]:
    try:
        result = await run_drug_interaction_check(
            medicines=req.medicines,
            session_id=req.session_id,
            user_id=req.user_id,
        )
        log.info("drug_interaction_done", medicines=req.medicines)
        return {"ok": True, "result": result}
    except Exception as exc:
        log.error("drug_interaction_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/planner", summary="Pharmacy refill planner (traced)")
async def planner(req: PlannerRequest) -> dict[str, Any]:
    try:
        result = await run_planner(
            history=req.history,
            prescription=req.prescription,
            budget=req.budget,
            session_id=req.session_id,
            user_id=req.user_id,
        )
        log.info("planner_done")
        return {"ok": True, "result": result}
    except Exception as exc:
        log.error("planner_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/custom", summary="Run a custom prompt chain (traced)")
async def custom(req: CustomChainRequest) -> dict[str, Any]:
    try:
        result = await run_custom_chain(
            system_prompt=req.system_prompt,
            user_message=req.user_message,
            temperature=req.temperature,
            session_id=req.session_id,
            user_id=req.user_id,
            trace_name=req.trace_name,
            tags=req.tags or ["custom", "pharmagenie"],
        )
        log.info("custom_chain_done")
        return {"ok": True, "result": result}
    except Exception as exc:
        log.error("custom_chain_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
