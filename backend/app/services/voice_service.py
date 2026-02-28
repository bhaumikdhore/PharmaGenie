import base64
from app.core.config import settings

try:
    from elevenlabs import ElevenLabs
except ImportError:
    ElevenLabs = None

client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY) if ElevenLabs else None

def generate_voice(text: str) -> str:
    """
    Converts text to speech using ElevenLabs.
    Returns base64 encoded audio string.
    """
    if client is None:
        return None

    try:
        audio = client.text_to_speech.convert(
            voice_id="EXAVITQu4vr4xnSDxMaL",  # Default ElevenLabs voice (Rachel)
            model_id="eleven_multilingual_v2",
            text=text,
        )

        audio_bytes = b"".join(audio)

        return base64.b64encode(audio_bytes).decode("utf-8")

    except Exception as e:
        print("Voice generation error:", e)
        return None
