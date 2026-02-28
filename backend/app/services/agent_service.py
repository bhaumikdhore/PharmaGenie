from app.ai.agent import agent as app_agent
from app.core.config import settings
from langfuse import Langfuse

try:
    from langfuse.langchain import CallbackHandler
except Exception:
    CallbackHandler = None


langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST,
)


def _build_callbacks(trace_id: str | None):
    if CallbackHandler is None:
        return None

    try:
        if trace_id:
            handler = CallbackHandler(
                update_trace=True,
                trace_context={"trace_id": trace_id},
            )
        else:
            handler = CallbackHandler(update_trace=True)
        return [handler]
    except Exception:
        return None


async def run_agent(query: str):
    with langfuse.start_as_current_span(
        name="pharmagenie-search",
        input={"query": query},
        metadata={"feature": "medicine-search", "route": "/search"},
    ):
        langfuse.update_current_trace(
            name="pharmagenie-search",
            user_id="api-user",
            input={"query": query},
            metadata={"feature": "medicine-search", "route": "/search"},
        )

        trace_id = langfuse.get_current_trace_id()
        callbacks = _build_callbacks(trace_id)

        try:
            response = await app_agent.arun(query, callbacks=callbacks)
            langfuse.update_current_span(output={"response": response})
            langfuse.update_current_trace(output={"response": response})
            return response
        except Exception as exc:
            langfuse.update_current_span(level="ERROR", status_message=str(exc))
            raise
        finally:
            try:
                langfuse.flush()
            except Exception:
                pass
