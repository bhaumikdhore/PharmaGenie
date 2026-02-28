import asyncio
from app.services.voice_service import generate_voice


async def generate_audio(text: str):
    if not text:
        return None
    return await asyncio.to_thread(generate_voice, text)
