"""PharmaGenie Intent Detection - LLM layer for multilingual voice input."""

import json
import re
from typing import Any

import httpx

from config import LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL, OPENAI_API_KEY

INTENT_SCHEMA = {
    "add_to_cart": "Add medicine to cart",
    "search": "Search for medicines",
    "check_order": "Check order status",
    "check_interactions": "Check drug interactions",
    "view_cart": "View cart contents",
    "remove_from_cart": "Remove medicine from cart",
    "create_order": "Create/place order",
    "greeting": "Greeting or hello",
    "unknown": "Unclear intent",
}

SYSTEM_PROMPT = """You are a pharmacy intent detector. Extract structured JSON from customer voice input in ANY language (Hindi, English, etc).

Input: Customer speech (e.g., "Mujhe paracetamol chahiye", "Add 2 strips of metformin", "Cart kya hai")

Output ONLY valid JSON (no markdown, no extra text):
{
  "intent": "<one of: add_to_cart, search, check_order, check_interactions, view_cart, remove_from_cart, create_order, greeting, unknown>",
  "medicine_name": "<extracted medicine name or null>",
  "quantity": <number or 1>,
  "extra_info": "<any other relevant info or empty string>"
}

Rules:
- "chahiye", "add", "daalo", "do" → add_to_cart
- "search", "dhundho", "find" → search
- "order status", "kahan hai order" → check_order
- "interaction", "sahi hai" → check_interactions
- "cart", "basket" → view_cart
- "remove", "hatao" → remove_from_cart
- "place order", "order complete" → create_order
- Extract medicine names (e.g., Paracetamol, Insulin, Metformin)
- quantity defaults to 1 if not mentioned
"""


def _call_ollama(text: str) -> str:
    """Call Ollama API for intent detection."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nInput: {text}\nOutput:",
        "stream": False,
    }
    with httpx.Client(timeout=5.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "")


def _call_openai(text: str) -> str:
    """Call OpenAI API for intent detection."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Input: {text}\nOutput:"},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content or ""


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Parse LLM response to JSON, with fallback extraction."""
    raw = raw.strip()
    # Remove markdown code blocks if present
    if "```" in raw:
        raw = re.sub(r"```(?:json)?\s*", "", raw)
        raw = raw.replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Fallback: rule-based extraction for common phrases
    text_lower = raw.lower()
    intent = "unknown"
    medicine_name = None
    quantity = 1

    patterns = [
        (r"add_to_cart|add\s+to\s+cart", "add_to_cart"),
        (r"search", "search"),
        (r"check_order|order\s+status", "check_order"),
        (r"check_interactions|interaction", "check_interactions"),
        (r"view_cart|cart|basket", "view_cart"),
        (r"remove_from_cart|remove", "remove_from_cart"),
        (r"create_order|place\s+order", "create_order"),
        (r"greeting|hello|hi", "greeting"),
    ]
    for pat, i in patterns:
        if re.search(pat, text_lower):
            intent = i
            break

    # Try to extract medicine name from common patterns
    med_match = re.search(
        r"(?:medicine|medication|medicine_name|name)[\"\s:]+([a-zA-Z0-9\s]+)",
        raw,
        re.I,
    )
    if med_match:
        medicine_name = med_match.group(1).strip() or None
    if not medicine_name:
        qty_match = re.search(r"quantity[\"\s:]+(\d+)", raw, re.I)
        if qty_match:
            quantity = int(qty_match.group(1))

    return {
        "intent": intent,
        "medicine_name": medicine_name,
        "quantity": quantity,
        "extra_info": "",
    }


def detect_intent(text: str) -> dict[str, Any]:
    """
    Detect intent from customer voice text.
    Returns: {"intent": str, "medicine_name": str|None, "quantity": int, "extra_info": str}
    """
    if not text or not text.strip():
        return {"intent": "unknown", "medicine_name": None, "quantity": 1, "extra_info": ""}

    try:
        if LLM_PROVIDER == "ollama":
            raw = _call_ollama(text)
        elif LLM_PROVIDER == "openai":
            raw = _call_openai(text)
        else:
            raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")
    except Exception:
        # Fallback to simple rule-based detection if LLM fails
        result = _rule_based_intent(text)
        return result or {"intent": "unknown", "medicine_name": None, "quantity": 1, "extra_info": ""}

    return _parse_json_response(raw)


def _rule_based_intent(text: str) -> dict | None:
    """Simple rule-based intent when LLM is unavailable."""
    t = text.lower().strip()
    words = t.split()
    medicines = {"paracetamol", "metformin", "insulin", "ibuprofen", "amoxicillin", "aspirin"}

    if any(w in t for w in ["chahiye", "add", "daalo", "do", "lao"]):
        for m in medicines:
            if m in t:
                qty = 1
                for i, w in enumerate(words):
                    if w.isdigit() and i < len(words) - 1:
                        qty = int(w)
                        break
                return {"intent": "add_to_cart", "medicine_name": m.title(), "quantity": qty, "extra_info": ""}
        return {"intent": "add_to_cart", "medicine_name": words[-1].title() if words else None, "quantity": 1, "extra_info": ""}
    if any(w in t for w in ["search", "dhundho", "find"]):
        return {"intent": "search", "medicine_name": " ".join(w for w in words if w not in {"search", "for", "me", "karo"}) or None, "quantity": 1, "extra_info": ""}
    if any(w in t for w in ["order", "status", "kahan"]):
        return {"intent": "check_order", "medicine_name": None, "quantity": 1, "extra_info": ""}
    if any(w in t for w in ["cart", "basket", "kyahai"]):
        return {"intent": "view_cart", "medicine_name": None, "quantity": 1, "extra_info": ""}
    if any(w in t for w in ["place", "order", "complete"]):
        return {"intent": "create_order", "medicine_name": None, "quantity": 1, "extra_info": ""}
    if any(w in t for w in ["hello", "hi", "namaste"]):
        return {"intent": "greeting", "medicine_name": None, "quantity": 1, "extra_info": ""}
    return None
