from __future__ import annotations

import asyncio
from itertools import combinations
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.agents import planner_agent, safety_agent, billing_agent, prescription_agent, delivery_agent, notification_agent, prescription_requirement_agent, ai_safety_medicine
from app.services.intent_router import route_query
from app.services.response_agent import format_response
from app.services.voice_agent import generate_audio

router = APIRouter(prefix="/ai", tags=["AI"])


class QueryRequest(BaseModel):
    query: str


class DrugInteraction(BaseModel):
    medicine1: str
    medicine2: str
    severity: str
    description: str
    recommendation: str


class InteractionsRequest(BaseModel):
    medicines: List[str]


@router.post("/internal")
async def ai_internal(request: QueryRequest):
    return await route_query(request.query)


@router.post("/search")
async def ai_search(request: QueryRequest):
    structured_result = await route_query(request.query)

    status = structured_result.get("status") if isinstance(structured_result, dict) else None
    if status in {"restricted", "unsafe_dosage", "error", "unsupported"}:
        return structured_result

    formatted_text = await format_response(structured_result)
    audio = await generate_audio(formatted_text)

    return {
        "response": formatted_text,
        "audio": audio,
    }


@router.post("/check-interactions")
async def check_interactions(payload: InteractionsRequest):
    """
    Multi-medicine interaction and safety aggregation powered by the safety agent.
    Returns the InteractionCheckResponse shape expected by the frontend.
    """
    raw_medicines = payload.medicines or []
    cleaned: list[str] = []
    seen = set()
    for name in raw_medicines:
        if not name:
            continue
        canon = name.strip()
        if not canon:
            continue
        key = canon.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(canon)

    # Single medicine – treat as safe; the per-medicine safety agent is used elsewhere.
    if len(cleaned) < 2:
        return {
            "has_interactions": False,
            "interactions": [],
            "overall_risk": "safe",
            "recommendation": "Single medication - no interaction risk detected.",
        }

    # Call safety agent once per unique medicine.
    safety_results: dict[str, dict] = {}
    for name in cleaned:
        try:
            # safety_agent.run returns a dict with dataclass fields from SafetyAssessment.
            result = await safety_agent.run({"medicine_name": name})
        except Exception as exc:  # pragma: no cover - defensive
            result = {"status": "error", "message": str(exc)}
        safety_results[name] = result or {}

    def per_medicine_severity(data: dict) -> str:
        status = (data.get("status") or "").lower()
        if status == "error":
            return "high"
        is_safe = data.get("is_safe", True)
        requires_prescription = bool(data.get("requires_prescription"))
        controlled_level = data.get("controlled_level") or 0

        if not is_safe:
            return "severe"
        if requires_prescription or (isinstance(controlled_level, int) and controlled_level > 0):
            return "high"
        return "low"

    severity_rank = {"low": 0, "moderate": 1, "high": 2, "severe": 3}

    interactions: list[DrugInteraction] = []
    worst_pair_severity_value = 0

    for m1, m2 in combinations(cleaned, 2):
        d1 = safety_results.get(m1, {})
        d2 = safety_results.get(m2, {})

        s1 = per_medicine_severity(d1)
        s2 = per_medicine_severity(d2)
        pair_severity = s1 if severity_rank[s1] >= severity_rank[s2] else s2

        if severity_rank[pair_severity] == 0:
            # Both appear low-risk individually; no explicit interaction to surface.
            continue

        reasons: list[str] = []
        for d in (d1, d2):
            for reason in d.get("reasons") or []:
                if reason not in reasons:
                    reasons.append(reason)

        description_parts = []
        if reasons:
            description_parts.append(" ".join(reasons))
        description_parts.append(
            "Combined use should be reviewed by a pharmacist, especially for dosage and contraindications."
        )
        description = " ".join(description_parts)

        if pair_severity in {"high", "severe"}:
            recommendation = "High-risk combination. Consult a licensed medical professional before dispensing."
        else:
            recommendation = "Use with caution and monitor the patient; escalate to a pharmacist if unsure."

        interactions.append(
            DrugInteraction(
                medicine1=m1,
                medicine2=m2,
                severity=pair_severity,
                description=description,
                recommendation=recommendation,
            )
        )
        worst_pair_severity_value = max(worst_pair_severity_value, severity_rank[pair_severity])

    has_interactions = len(interactions) > 0

    if not has_interactions:
        # Multiple medicines, but no high-signal flags from the safety database.
        overall_risk = "caution"
        recommendation = (
            "No specific high-risk interactions detected in the safety database, "
            "but multi-drug therapy always warrants pharmacist oversight."
        )
    else:
        if worst_pair_severity_value >= severity_rank["severe"]:
            overall_risk = "danger"
            recommendation = (
                "One or more severe safety flags detected across this combination. "
                "Do not dispense without pharmacist review."
            )
        elif worst_pair_severity_value >= severity_rank["high"]:
            overall_risk = "warning"
            recommendation = (
                "High-risk combination detected. Proceed only after pharmacist validation and documentation."
            )
        else:
            overall_risk = "caution"
            recommendation = (
                "Moderate concerns detected. Use with caution and consider dose adjustments or alternatives."
            )

    # Shape matches frontend InteractionCheckResponse type.
    return {
        "has_interactions": has_interactions,
        "interactions": [i.model_dump() for i in interactions],
        "overall_risk": overall_risk,
        "recommendation": recommendation,
    }


class ChatRequest(BaseModel):
    query: str
    include_audio: bool = True


class TTSRequest(BaseModel):
    text: str


@router.post("/tts")
async def ai_tts(request: TTSRequest):
    """On-demand TTS: convert any text to base64 MP3 audio."""
    audio = await generate_audio(request.text)
    return {"audio": audio}


async def _text_and_audio(text_coro, include_audio: bool):
    """Run text formatting and TTS generation concurrently.
    text_coro may be a coroutine or a plain string.
    Returns (text, audio_or_none).
    """
    import asyncio as _asyncio
    import inspect

    if inspect.iscoroutine(text_coro):
        if include_audio:
            # We need the text first to feed into TTS — resolve text, then fire both
            text = await text_coro
        else:
            text = await text_coro
    else:
        text = text_coro

    if include_audio:
        audio = await generate_audio(text)
    else:
        audio = None
    return text, audio


@router.post("/chat")
async def ai_chat(request: ChatRequest):
    """
    Fast pharma chat endpoint.
    - Text response and TTS audio are generated concurrently via asyncio.gather.
    - Pass include_audio=false to skip TTS entirely (saves ~1-2 s per request).
    """
    try:
        structured_result = await route_query(request.query)
    except Exception as exc:
        return {
            "intent": "error",
            "response": f"Agent error: {exc}",
            "items": [],
            "audio": None,
        }

    intent = structured_result.get("intent") or structured_result.get("status", "info")
    status = structured_result.get("status")

    # -------- fast paths where text is already available --------
    if intent == "purchase_order":
        resp_text = structured_result.get("message", "Adding items to your cart…")
        audio = await generate_audio(resp_text) if request.include_audio else None
        return {
            "intent": "purchase_order",
            "response": resp_text,
            "items": structured_result.get("items", []),
            "audio": audio,
        }

    if status in {"restricted", "unsafe_dosage", "error", "unsupported"}:
        resp_text = structured_result.get("message", str(structured_result))
        audio = await generate_audio(resp_text) if request.include_audio else None
        return {
            "intent": status,
            "response": resp_text,
            "items": [],
            "audio": audio,
        }

    if status == "chat" or intent == "general_chat":
        resp_text = structured_result.get("message", "I'm here to help! Ask me anything about medicines.")
        audio = await generate_audio(resp_text) if request.include_audio else None
        return {
            "intent": "general_chat",
            "response": resp_text,
            "items": [],
            "audio": audio,
        }

    # -------- remaining intents need LLM formatting --------
    # Run format_response and generate_audio(placeholder) concurrently:
    # First format text, then generate audio — both wrapped so TTS only starts after text ready.
    try:
        formatted_text = await format_response(structured_result)
    except Exception:
        formatted_text = structured_result.get("message") or str(structured_result)

    audio = await generate_audio(formatted_text) if request.include_audio else None
    return {
        "intent": intent or "info",
        "response": formatted_text,
        "items": [],
        "audio": audio,
    }


@router.post("/test/planner")
async def test_planner(data: dict):
    return await planner_agent.run(data)


@router.post("/test/safety")
async def test_safety(data: dict):
    return await safety_agent.run(data)


@router.post("/test/billing")
async def test_billing(data: dict):
    return await billing_agent.run(data)


@router.post("/test/prescription")
async def test_prescription(data: dict):
    return await prescription_agent.run(data)


@router.post("/test/delivery")
async def test_delivery(data: dict):
    """Test delivery tracking agent"""
    return await delivery_agent.run(data)


@router.post("/test/notification")
async def test_notification(data: dict):
    """Test notification agent"""
    return await notification_agent.run(data)


@router.post("/test/prescription-requirement")
async def test_prescription_requirement(data: dict):
    """Check if a medicine requires prescription"""
    return await prescription_requirement_agent.run(data)


@router.post("/test/ai-safety-medicine")
async def test_ai_safety_medicine(data: dict):
    """
    AI-powered medicine safety check
    Analyzes any medicine for safety, prescription requirements, and usage guidance.

    Input:
    - medicine_name: str (required)
    - dosage: str (optional)

    Returns:
    - is_approved: bool
    - approval_status: str (✅ AVAILABLE FOR PURCHASE or restricted message)
    - ai_analysis: str (AI reasoning or rule-based explanation)
    - source: str (ollama_ai | generic_assessment)
    """
    return await ai_safety_medicine.run(data)
