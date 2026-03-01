"""
PharmaGenie Agent Integration Layer
=====================================
Defines pre-built LangChain chains for every PharmaGenie AI use-case.
Each chain automatically attaches a Langfuse callback so every run is traced.

Chains provided
---------------
- safety_check_chain          → medicine safety + prescription requirement
- prescription_analysis_chain → analyse a prescription image description
- drug_interaction_chain      → check interactions between multiple drugs
- planner_chain               → pharmacy planner / order suggestion
- custom_chain                → generic free-form chain (prompt + model)
"""
from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from callbacks.langfuse_handler import build_callback_handler
from config import get_settings

settings = get_settings()


# ── Shared LLM factory ────────────────────────────────────────────────────────
def _llm(temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.default_llm_model,
        temperature=temperature,
        openai_api_key=settings.openai_api_key,
        streaming=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Medicine Safety Check
# ─────────────────────────────────────────────────────────────────────────────
SAFETY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a licensed pharmacist AI assistant for PharmaGenie, an Indian pharmacy.
Your job is to evaluate medicine safety and prescription requirements for Indian regulations.

Respond in strict JSON:
{{
  "medicine_name": "<name>",
  "is_approved": true/false,
  "approval_status": "AVAILABLE / PRESCRIPTION REQUIRED / BANNED",
  "can_buy_without_prescription": true/false,
  "requires_prescription": true/false,
  "controlled_level": 0-3,
  "safety_warnings": ["..."],
  "common_uses": ["..."],
  "dosage_guidance": "...",
  "side_effects": ["..."],
  "ai_analysis": "...",
  "source": "openai_gpt4"
}}""",
        ),
        (
            "human",
            "Medicine: {medicine_name}\nDosage: {dosage}\nPatient notes: {patient_notes}",
        ),
    ]
)


async def run_safety_check(
    medicine_name: str,
    dosage: str = "standard",
    patient_notes: str = "",
    session_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    handler, _ = build_callback_handler(
        session_id=session_id,
        user_id=user_id,
        trace_name="medicine-safety-check",
        metadata={"medicine": medicine_name, "dosage": dosage},
        tags=["safety", "pharmacy", "pharmagenie"],
    )
    chain = SAFETY_PROMPT | _llm() | StrOutputParser()
    raw = await chain.ainvoke(
        {"medicine_name": medicine_name, "dosage": dosage, "patient_notes": patient_notes},
        config={"callbacks": [handler]},
    )
    import json, re
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"raw_response": raw, "source": "openai_gpt4"}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Prescription Analysis
# ─────────────────────────────────────────────────────────────────────────────
PRESCRIPTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a pharmacy assistant AI. Analyse prescription details provided by the user.
Extract all medicines, dosages, frequencies, and durations. Flag anything unusual.

Respond in strict JSON:
{{
  "medicines": [
    {{
      "name": "...", "dosage": "...", "frequency": "...",
      "duration": "...", "requires_prescription": true/false
    }}
  ],
  "doctor_name": "...",
  "patient_name": "...",
  "validity_days": 30,
  "warnings": ["..."],
  "total_medicines": 0
}}""",
        ),
        ("human", "Prescription details:\n{prescription_text}"),
    ]
)


async def run_prescription_analysis(
    prescription_text: str,
    session_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    handler, _ = build_callback_handler(
        session_id=session_id,
        user_id=user_id,
        trace_name="prescription-analysis",
        tags=["prescription", "pharmacy", "pharmagenie"],
    )
    chain = PRESCRIPTION_PROMPT | _llm(temperature=0.1) | StrOutputParser()
    raw = await chain.ainvoke(
        {"prescription_text": prescription_text},
        config={"callbacks": [handler]},
    )
    import json, re
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"raw_response": raw}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Drug Interaction Check
# ─────────────────────────────────────────────────────────────────────────────
INTERACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a clinical pharmacist AI. Check for drug interactions between medicines.
Rate severity: NONE / MINOR / MODERATE / SEVERE / CONTRAINDICATED.

Respond in strict JSON:
{{
  "medicines_checked": ["..."],
  "interactions": [
    {{
      "drug_a": "...", "drug_b": "...", "severity": "...",
      "description": "...", "recommendation": "..."
    }}
  ],
  "overall_risk": "LOW / MEDIUM / HIGH / CRITICAL",
  "summary": "..."
}}""",
        ),
        ("human", "Check interactions for these medicines: {medicines_list}"),
    ]
)


async def run_drug_interaction_check(
    medicines: list[str],
    session_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    handler, _ = build_callback_handler(
        session_id=session_id,
        user_id=user_id,
        trace_name="drug-interaction-check",
        metadata={"medicine_count": len(medicines)},
        tags=["interaction", "safety", "pharmagenie"],
    )
    chain = INTERACTION_PROMPT | _llm(temperature=0) | StrOutputParser()
    raw = await chain.ainvoke(
        {"medicines_list": ", ".join(medicines)},
        config={"callbacks": [handler]},
    )
    import json, re
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"raw_response": raw}


# ─────────────────────────────────────────────────────────────────────────────
# 4. Pharmacy Planner
# ─────────────────────────────────────────────────────────────────────────────
PLANNER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are PharmaGenie's intelligent pharmacy planner.
Based on the customer's purchase history and current prescription, suggest a monthly refill plan.
Consider stock availability, cost optimisation, and generic alternatives.

Respond in strict JSON:
{{
  "refill_schedule": [
    {{"medicine": "...", "quantity": 0, "refill_date": "YYYY-MM-DD", "estimated_cost_inr": 0}}
  ],
  "generic_substitutes": [
    {{"original": "...", "generic": "...", "savings_inr": 0}}
  ],
  "monthly_budget_inr": 0,
  "notes": "..."
}}""",
        ),
        (
            "human",
            "Customer history: {history}\nCurrent prescription: {prescription}\nBudget preference: {budget}",
        ),
    ]
)


async def run_planner(
    history: str,
    prescription: str,
    budget: str = "no preference",
    session_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    handler, _ = build_callback_handler(
        session_id=session_id,
        user_id=user_id,
        trace_name="pharmacy-planner",
        tags=["planner", "recommendations", "pharmagenie"],
    )
    chain = PLANNER_PROMPT | _llm(temperature=0.3) | StrOutputParser()
    raw = await chain.ainvoke(
        {"history": history, "prescription": prescription, "budget": budget},
        config={"callbacks": [handler]},
    )
    import json, re
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"raw_response": raw}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Custom / Generic Chain
# ─────────────────────────────────────────────────────────────────────────────
async def run_custom_chain(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.5,
    session_id: str | None = None,
    user_id: str | None = None,
    trace_name: str = "custom-chain",
    tags: list[str] | None = None,
) -> str:
    handler, _ = build_callback_handler(
        session_id=session_id,
        user_id=user_id,
        trace_name=trace_name,
        tags=tags or ["custom", "pharmagenie"],
    )
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", "{input}")]
    )
    chain = prompt | _llm(temperature=temperature) | StrOutputParser()
    return await chain.ainvoke(
        {"input": user_message},
        config={"callbacks": [handler]},
    )
