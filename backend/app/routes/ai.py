from fastapi import APIRouter
from pydantic import BaseModel
from app.agents import planner_agent, safety_agent, billing_agent, prescription_agent
from app.services.intent_router import route_query
from app.services.response_agent import format_response
from app.services.voice_agent import generate_audio

router = APIRouter()  # Removed the '/ai' prefix to ensure endpoints are not nested


class QueryRequest(BaseModel):
    query: str


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

