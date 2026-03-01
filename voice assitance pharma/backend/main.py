"""PharmaGenie Voice Agent - FastAPI backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from action_router import process_voice_text

app = FastAPI(title="PharmaGenie Voice Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VoiceInput(BaseModel):
    text: str


class VoiceResponse(BaseModel):
    success: bool
    message: str
    data: object | None = None


@app.get("/")
def root():
    return {"app": "PharmaGenie Voice Agent", "status": "ok", "docs": "/docs"}


@app.post("/voice/process", response_model=VoiceResponse)
def process_voice(input: VoiceInput):
    """Main endpoint: speech text → intent → action → response."""
    result = process_voice_text(input.text)
    return VoiceResponse(
        success=result["success"],
        message=result["message"],
        data=result.get("data"),
    )
