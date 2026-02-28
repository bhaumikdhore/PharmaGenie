from langchain_core.prompts import ChatPromptTemplate
import json
import re

try:
    from langchain_ollama import ChatOllama
except Exception:
    ChatOllama = None

llm = ChatOllama(model="llama3", temperature=0) if ChatOllama else None

planner_prompt = ChatPromptTemplate.from_template("""
You are a pharmacy AI planner.

Classify the user query into one of these intents:

- warehouse_check
- recommendation
- prescription_check
- billing
- general_chat

Extract entities if possible.

Return STRICT JSON only in this format:

{{
  "intent": "...",
  "entities": {{
      "medicine_name": "...",
      "symptoms": "...",
      "items": "...",
      "prescription_text": "...",
      "dosage_mg": 0
  }}
}}

User Query:
{query}
""")


async def plan_query(query: str):
    query_lower = query.lower()
    medicine_match = re.search(r"\b(paracetamol|alprazolam|diazepam|codeine|tramadol)\b", query_lower)
    dosage_match = re.search(r"\b(\d{2,5})\s*mg\b", query_lower)

    # Deterministic guardrail: controlled medicines should always go through safety checks.
    if medicine_match and medicine_match.group(1) in {"alprazolam", "diazepam", "codeine", "tramadol"}:
        return {
            "intent": "prescription_check",
            "entities": {
                "medicine_name": medicine_match.group(1),
                "dosage_mg": int(dosage_match.group(1)) if dosage_match else None,
                "symptoms": "",
                "items": "",
                "prescription_text": "",
            },
        }

    if llm is None:
        # Fallback when LLM dependency is not installed.
        if medicine_match:
            return {
                "intent": "warehouse_check",
                "entities": {
                    "medicine_name": medicine_match.group(1),
                    "dosage_mg": int(dosage_match.group(1)) if dosage_match else None,
                },
            }
        return {
            "intent": "general_chat",
            "entities": {},
        }

    chain = planner_prompt | llm
    try:
        result = await chain.ainvoke({"query": query})
    except Exception:
        # Fallback when Ollama/model endpoint is unavailable.
        if medicine_match:
            return {
                "intent": "warehouse_check",
                "entities": {
                    "medicine_name": medicine_match.group(1),
                    "dosage_mg": int(dosage_match.group(1)) if dosage_match else None,
                },
            }
        return {
            "intent": "general_chat",
            "entities": {},
        }

    try:
        content = result.content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.lower().startswith("json"):
                content = content[4:].strip()
        return json.loads(content)
    except Exception:
        return {
            "intent": "general_chat",
            "entities": {}
        }


async def run(input_data: dict) -> dict:
    query = input_data.get("query", "")
    return await plan_query(query)
