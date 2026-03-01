"""
Langfuse v3 CallbackHandler — wires every LangChain run into Langfuse traces.

Langfuse v3 uses environment variables for auth and OpenTelemetry under the
hood. The CallbackHandler reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY,
and LANGFUSE_HOST automatically from the environment.

Usage
-----
from callbacks.langfuse_handler import build_callback_handler, set_trace_metadata

handler, trace_id = build_callback_handler(session_id="abc", user_id="42")
chain.invoke(inputs, config={"callbacks": [handler]})
"""
from __future__ import annotations

import os
import uuid
from typing import Any

from langfuse.langchain import CallbackHandler

from config import get_settings

settings = get_settings()

# Ensure env vars are set so Langfuse SDK picks them up
os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)


def build_callback_handler(
    *,
    session_id: str | None = None,
    user_id: str | None = None,
    trace_name: str | None = None,
    metadata: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> tuple[CallbackHandler, str]:
    """
    Return (handler, trace_id).
    Session / user / metadata are attached to the trace after the run via
    the Langfuse client using update_current_trace inside agent wrappers.
    """
    handler = CallbackHandler(public_key=settings.langfuse_public_key)
    trace_id = str(uuid.uuid4())
    # Store extra context on the handler so callers can use it if needed
    handler._pg_session_id = session_id  # type: ignore[attr-defined]
    handler._pg_user_id = user_id        # type: ignore[attr-defined]
    handler._pg_trace_name = trace_name  # type: ignore[attr-defined]
    handler._pg_metadata = metadata      # type: ignore[attr-defined]
    handler._pg_tags = tags              # type: ignore[attr-defined]
    return handler, trace_id
