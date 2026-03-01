from langchain_core.prompts import ChatPromptTemplate
import json
import re

try:
    from langchain_ollama import ChatOllama
except Exception:
    ChatOllama = None

llm = ChatOllama(model="llama3", temperature=0) if ChatOllama else None

planner_prompt = ChatPromptTemplate.from_template("""
You are a pharmacy AI planner. Classify the user query into EXACTLY one of these intents:

- purchase_order    → user wants to buy, order, or add medicine to cart
- warehouse_check   → user asks if a medicine is available, in stock, or what the price is
- prescription_check → user asks about safety, side effects, interactions, dosage safety, or contraindications
- general_chat      → anything else: greetings, general health questions, how the app works, etc.

IMPORTANT RULES:
- NEVER use "recommendation" — use warehouse_check or general_chat instead
- "Is X available?" → warehouse_check
- "Do you have X?" → warehouse_check
- "What are the side effects of X?" → prescription_check
- "Is X safe?" → prescription_check
- "Buy / order / get me X" → purchase_order
- Everything else → general_chat

Extract entities where possible.

Return STRICT JSON only — no markdown, no explanation:

{{
  "intent": "...",
  "entities": {{
      "medicine_name": "...",
      "symptoms": "...",
      "items": [],
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

    # ── Availability / stock check (deterministic, before LLM) ───────────────
    _AVAIL_PHRASES = re.compile(
        r'\b(available|in stock|do you have|have you got|is there|stock|stocked|carry|get)\b'
    )
    if _AVAIL_PHRASES.search(query_lower):
        # Extract medicine name: word(s) that follow "is", "are", a verb, or come before "available"
        # Try: "is X available", "do you have X", "X available", "X in stock"
        med_name = None
        patterns = [
            r'(?:is|are|have you got|do you have|do you carry|do you stock|get)\s+([a-zA-Z][a-zA-Z0-9\s\-]{1,30?}?)(?:\s+available|\s+in stock|\s+stocked|\?|$)',
            r'([a-zA-Z][a-zA-Z0-9\s\-]{1,30?}?)(?:\s+available|\s+in stock|\s+stocked)',
        ]
        for pat in patterns:
            m = re.search(pat, query_lower)
            if m:
                candidate = m.group(1).strip()
                # strip filler words
                candidate = re.sub(r'\b(the|a|an|any|some|this|that|my)\b', '', candidate).strip()
                if len(candidate) >= 2:
                    med_name = candidate
                    break
        if not med_name:
            # fallback: take longest capitalised word from original query
            words = re.findall(r'\b[A-Za-z][a-z]{2,}\b', query)
            stop = {'is', 'are', 'the', 'do', 'you', 'have', 'got', 'any', 'can', 'available', 'stock', 'there'}
            candidates = [w for w in words if w.lower() not in stop]
            if candidates:
                med_name = candidates[0]
        if med_name:
            return {
                "intent": "warehouse_check",
                "entities": {
                    "medicine_name": med_name,
                    "dosage_mg": int(dosage_match.group(1)) if dosage_match else None,
                },
            }

    # ── Safety / interaction check (deterministic, before LLM) ──────────────
    _SAFETY_PHRASES = re.compile(
        r'\b(safe|safety|interaction|interact|side effect|contraindic|overdose|danger|react)\b'
    )
    if _SAFETY_PHRASES.search(query_lower):
        # Try to extract medicine name from query
        med_name = None
        m = re.search(r'(?:of|for|with|take|taking|on)\s+([a-zA-Z][a-zA-Z0-9\s\-]{1,25?}?)(?:\s+safe|\s+and|\?|$)', query_lower)
        if m:
            med_name = re.sub(r'\b(the|a|an)\b', '', m.group(1)).strip()
        if not med_name:
            words = re.findall(r'\b[A-Za-z][a-z]{3,}\b', query)
            stop = {'safe', 'safety', 'interaction', 'side', 'effect', 'effects', 'with', 'take', 'taking', 'what', 'are', 'the', 'for', 'this'}
            candidates = [w for w in words if w.lower() not in stop]
            if candidates:
                med_name = candidates[0]
        if med_name:
            return {
                "intent": "prescription_check",
                "entities": {
                    "medicine_name": med_name,
                    "dosage_mg": int(dosage_match.group(1)) if dosage_match else None,
                },
            }

    # ── Symptom → medicine recommendation (deterministic, before LLM) ────────
    _SYMPTOM_WORDS = re.compile(
        r'\b(fever|cold|cough|headache|head ache|migraine|pain|ache|diarrhea|diarrhoea|'
        r'vomiting|nausea|nauseous|infection|allergy|allergic|inflammation|inflamed|anxiety|'
        r'insomnia|sleepless|acidity|acid reflux|heartburn|constipation|bloating|gas|'
        r'diabetes|hypertension|high blood pressure|cholesterol|sore throat|throat pain|'
        r'body ache|muscle pain|joint pain|runny nose|blocked nose|stuffy nose|sneezing|'
        r'rash|itching|skin allergy|stomach ache|stomach pain|cramps|dehydration|weakness|fatigue)\b'
    )
    _SYMPTOM_TRIGGERS = re.compile(
        r'\b(i have|i am having|i feel|i\'m feeling|i suffer|suffering from|experiencing|'
        r'got|what (medicine|drug|tablet|pill) (should|can|do) i|what (should|can) i take|'
        r'suggest|recommend|medicine for|tablet for|pill for|remedy for|treatment for)\b'
    )
    sym_match = _SYMPTOM_WORDS.search(query_lower)
    trigger_match = _SYMPTOM_TRIGGERS.search(query_lower)
    if sym_match and (trigger_match or re.search(r'\b(medicine|tablet|pill|drug|remedy|take)\b', query_lower)):
        # Extract all matching symptoms
        all_symptoms = _SYMPTOM_WORDS.findall(query_lower)
        # Deduplicate keeping order
        seen = set()
        unique_symptoms = [s for s in all_symptoms if not (s in seen or seen.add(s))]
        return {
            "intent": "symptom_recommendation",
            "entities": {
                "symptoms": ", ".join(unique_symptoms),
                "medicine_name": "",
                "items": [],
                "prescription_text": "",
                "dosage_mg": int(dosage_match.group(1)) if dosage_match else None,
            },
        }
    # Also catch plain "I have fever / I have headache" patterns without explicit medicine ask
    if sym_match and trigger_match:
        all_symptoms = _SYMPTOM_WORDS.findall(query_lower)
        seen = set()
        unique_symptoms = [s for s in all_symptoms if not (s in seen or seen.add(s))]
        return {
            "intent": "symptom_recommendation",
            "entities": {
                "symptoms": ", ".join(unique_symptoms),
                "medicine_name": "",
                "items": [],
                "prescription_text": "",
                "dosage_mg": int(dosage_match.group(1)) if dosage_match else None,
            },
        }

    # ── Greetings / simple conversational openers ─────────────────────────
    _GREET = re.compile(r'^(hi|hello|hey|good\s+\w+|how are you|what can you|help me|what do you do)\b')
    if _GREET.search(query_lower.strip()):
        return {"intent": "general_chat", "entities": {}}


    _PURCHASE_VERBS = re.compile(
        r'\b(buy|purchase|order|get me|add|i want|i need|place an order for|i\'d like)\b'
    )
    if _PURCHASE_VERBS.search(query_lower):
        items: list[dict] = []
        # Try "N medicine_name" pattern first
        for m in re.finditer(
            r'(\d+)\s+([a-zA-Z][a-zA-Z0-9\s]*?)(?=\s*(?:,|\band\b|$))',
            query_lower
        ):
            name = m.group(2).strip()
            if name:
                items.append({"name": name, "quantity": int(m.group(1))})
        if not items:
            # Try "medicine_name N" or just medicine_name
            qty_m = re.search(r'\b(\d+)\b', query_lower)
            clean = re.sub(
                r'\b(buy|purchase|order|get|add|want|need|please|me|i|some|a|the|of|place|an|for|like|d)\b',
                '', query_lower
            )
            clean = re.sub(r'\b\d+\b', '', clean).strip()
            name = ' '.join(clean.split())
            if not name and medicine_match:
                name = medicine_match.group(1)
            if name:
                items.append({"name": name, "quantity": int(qty_m.group(1)) if qty_m else 1})
        if items:
            return {
                "intent": "purchase_order",
                "entities": {
                    "medicine_name": items[0]["name"],
                    "items": items,
                    "dosage_mg": int(dosage_match.group(1)) if dosage_match else None,
                },
            }
    # ─────────────────────────────────────────────────────────────────────────

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
