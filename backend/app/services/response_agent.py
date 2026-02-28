import json

try:
    from langchain_ollama import ChatOllama
except Exception:
    ChatOllama = None

_llm = ChatOllama(model="llama3", temperature=0.2) if ChatOllama else None


async def format_response(structured_result) -> str:
    if isinstance(structured_result, dict) and structured_result.get("message"):
        status = structured_result.get("status")
        # Keep strict policy/safety messages unmodified.
        if status in {"restricted", "unsafe_dosage", "error", "unsupported"}:
            return str(structured_result["message"])

    if _llm is None:
        if isinstance(structured_result, dict) and structured_result.get("message"):
            return str(structured_result["message"])
        return json.dumps(structured_result)

    prompt = (
        "Convert this pharmacy agent JSON into one short user-facing response. "
        "Do not add facts not present in the JSON.\n\n"
        f"JSON: {json.dumps(structured_result, ensure_ascii=False)}"
    )

    try:
        result = await _llm.ainvoke(prompt)
        if hasattr(result, "content") and result.content:
            return str(result.content).strip()
        return str(result)
    except Exception:
        if isinstance(structured_result, dict) and structured_result.get("message"):
            return str(structured_result["message"])
        return json.dumps(structured_result)
