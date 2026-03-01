from langfuse import Langfuse
from app.core.config import settings

_langfuse_host = (
    settings.LANGFUSE_HOST
    or settings.LANGFUSE_BASE_URL
    or "https://cloud.langfuse.com"
)

langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=_langfuse_host,
)