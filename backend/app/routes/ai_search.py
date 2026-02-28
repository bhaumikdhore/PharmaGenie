from fastapi import APIRouter
from pydantic import BaseModel
from app.services.agent_service import run_agent
from app.services.voice_service import generate_voice

router = APIRouter(prefix="/ai")

class QueryRequest(BaseModel):
    query: str

@router.post("/search")
async def ai_search(request: QueryRequest):
    response = await run_agent(request.query)
    audio_base64 = generate_voice(response)
    return {
        "response": response,
        "audio": audio_base64,
    }
