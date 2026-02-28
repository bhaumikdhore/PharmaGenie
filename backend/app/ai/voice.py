import os

try:
    from elevenlabs import generate, set_api_key
except Exception:
    generate = None
    set_api_key = None

if set_api_key is not None:
    set_api_key(os.getenv("ELEVENLABS_API_KEY"))

def text_to_voice(text):
    if generate is None:
        return None

    audio = generate(
        text=text,
        voice="Rachel",
        model="eleven_multilingual_v2"
    )
    return audio
