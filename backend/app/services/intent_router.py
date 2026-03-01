from app.services.planner_agent import plan_query
from app.services.warehouse_agent import warehouse_check
from app.services.safety_agent import safety_check

try:
    from langchain_ollama import ChatOllama
    _chat_llm = ChatOllama(model="llama3", temperature=0.4)
except Exception:
    _chat_llm = None

_GENERAL_CHAT_SYSTEM = (
    "You are PharmaGenie, a professional AI pharmacy assistant. "
    "Help users with medicine information, dosage guidance, side effects, drug interactions, "
    "symptoms, and general health questions. "
    "When a user describes symptoms, ALWAYS suggest the most appropriate OTC medicine by name "
    "with dosage. Example: 'For fever, paracetamol 500mg every 6 hours is recommended.' "
    "Always recommend consulting a licensed pharmacist or doctor for personal medical decisions. "
    "Keep answers concise, clear, and professional. "
    "Never make up medicine names or facts not in your training data."
)

# ── Built-in symptom → medicine knowledge base ───────────────────────────────
_SYMPTOM_KB: dict[str, dict] = {
    "fever": {
        "medicines": ["Paracetamol 500mg"],
        "dosage": "500mg every 6 hours (max 4 doses/day)",
        "note": "Take with water. Avoid alcohol. Consult a doctor if fever exceeds 103°F or lasts more than 3 days.",
    },
    "headache": {
        "medicines": ["Paracetamol 500mg", "Ibuprofen 400mg"],
        "dosage": "Paracetamol 500mg or Ibuprofen 400mg every 6–8 hours as needed",
        "note": "Take after food (especially Ibuprofen). Rest in a quiet, dark room.",
    },
    "head ache": {  # alias
        "medicines": ["Paracetamol 500mg", "Ibuprofen 400mg"],
        "dosage": "Paracetamol 500mg or Ibuprofen 400mg every 6–8 hours as needed",
        "note": "Take after food. Rest in a quiet, dark room.",
    },
    "migraine": {
        "medicines": ["Sumatriptan 50mg", "Ibuprofen 400mg"],
        "dosage": "Sumatriptan 50mg at onset; Ibuprofen 400mg every 8 hours",
        "note": "Avoid bright light and noise. See a doctor for recurring migraines.",
    },
    "cold": {
        "medicines": ["Cetirizine 10mg", "Loratadine 10mg"],
        "dosage": "Cetirizine 10mg once daily (at bedtime due to drowsiness)",
        "note": "Stay hydrated. Rest well. Steam inhalation helps with congestion.",
    },
    "cough": {
        "medicines": ["Dextromethorphan (Benadryl cough syrup)", "Ambroxol 30mg"],
        "dosage": "Dextromethorphan 10ml syrup 3 times daily; Ambroxol 30mg 3 times daily",
        "note": "For dry cough use DXM; for productive cough use Ambroxol. Consult doctor if cough persists > 2 weeks.",
    },
    "sore throat": {
        "medicines": ["Strepsils lozenges", "Benzydamine gargle"],
        "dosage": "Strepsils 1 lozenge every 2–3 hours; gargle with warm salt water",
        "note": "Avoid cold drinks. If throat is very red or you have fever, see a doctor.",
    },
    "throat pain": {
        "medicines": ["Strepsils lozenges", "Ibuprofen 400mg"],
        "dosage": "Strepsils 1 lozenge every 2–3 hours; Ibuprofen 400mg every 8 hours for pain",
        "note": "Gargle with warm salt water. Consult a doctor if symptoms worsen.",
    },
    "runny nose": {
        "medicines": ["Cetirizine 10mg", "Chlorpheniramine 4mg"],
        "dosage": "Cetirizine 10mg once daily or Chlorpheniramine 4mg every 6 hours",
        "note": "Chlorpheniramine causes drowsiness. Stay hydrated.",
    },
    "blocked nose": {
        "medicines": ["Xylometazoline nasal drops 0.1%", "Steam inhalation"],
        "dosage": "2 drops in each nostril twice daily (max 3 days)",
        "note": "Do not use nasal drops for more than 3 days to avoid rebound congestion.",
    },
    "stuffy nose": {
        "medicines": ["Xylometazoline nasal drops 0.1%"],
        "dosage": "2 drops in each nostril twice daily (max 3 days)",
        "note": "Steam inhalation also helps. Drink plenty of fluids.",
    },
    "sneezing": {
        "medicines": ["Cetirizine 10mg", "Loratadine 10mg"],
        "dosage": "Cetirizine 10mg once daily",
        "note": "Usually due to allergies or cold. Avoid known allergens.",
    },
    "acidity": {
        "medicines": ["Omeprazole 20mg", "Pantoprazole 40mg", "Antacid (Gelusil/Digene)"],
        "dosage": "Omeprazole 20mg once daily before breakfast; antacid gel 10ml after meals",
        "note": "Avoid spicy food, coffee, and citrus fruits. Eat smaller meals.",
    },
    "acid reflux": {
        "medicines": ["Omeprazole 20mg", "Ranitidine 150mg"],
        "dosage": "Omeprazole 20mg once daily before breakfast",
        "note": "Avoid lying down right after eating. Elevate head while sleeping.",
    },
    "heartburn": {
        "medicines": ["Antacid (Gelusil / Digene)", "Omeprazole 20mg"],
        "dosage": "Antacid 10ml after meals and at bedtime; Omeprazole 20mg before breakfast",
        "note": "Avoid fatty, fried, or spicy foods.",
    },
    "nausea": {
        "medicines": ["Ondansetron 4mg", "Domperidone 10mg"],
        "dosage": "Ondansetron 4mg every 8 hours or Domperidone 10mg 3 times daily before meals",
        "note": "Sip clear fluids slowly. Avoid solid food until nausea improves.",
    },
    "nauseous": {
        "medicines": ["Ondansetron 4mg", "Domperidone 10mg"],
        "dosage": "Ondansetron 4mg every 8 hours",
        "note": "Sip clear fluids slowly. Avoid solid food until nausea improves.",
    },
    "vomiting": {
        "medicines": ["Ondansetron 4mg", "Domperidone 10mg"],
        "dosage": "Ondansetron 4mg every 8 hours (dissolve under tongue for faster effect)",
        "note": "Rehydrate with ORS. If vomiting for > 24h, consult a doctor.",
    },
    "diarrhea": {
        "medicines": ["ORS (Oral Rehydration Salts)", "Loperamide 2mg"],
        "dosage": "ORS: 200ml after each loose stool; Loperamide 2mg after first loose stool (max 8mg/day)",
        "note": "Drink plenty of fluids. Avoid dairy, fatty foods. See doctor if blood in stool.",
    },
    "diarrhoea": {
        "medicines": ["ORS (Oral Rehydration Salts)", "Loperamide 2mg"],
        "dosage": "ORS: 200ml after each loose stool; Loperamide 2mg after first loose stool",
        "note": "Drink plenty of fluids. Avoid dairy, fatty foods.",
    },
    "constipation": {
        "medicines": ["Lactulose syrup", "Bisacodyl 5mg", "Isabgol (Psyllium husk)"],
        "dosage": "Lactulose 15ml twice daily; Bisacodyl 5mg at bedtime; Isabgol 1 sachet in water",
        "note": "Increase fibre and water intake. Exercise regularly.",
    },
    "bloating": {
        "medicines": ["Simethicone (Gas-X)", "Domperidone 10mg"],
        "dosage": "Simethicone 80mg after meals; Domperidone 10mg before meals",
        "note": "Avoid carbonated drinks and gas-producing foods.",
    },
    "gas": {
        "medicines": ["Simethicone (Gas-X)", "Activated charcoal"],
        "dosage": "Simethicone 80mg after meals",
        "note": "Eat slowly and chew food well.",
    },
    "stomach ache": {
        "medicines": ["Antispasmodic (Meftal Spas)", "Domperidone 10mg"],
        "dosage": "Meftal Spas 1 tablet every 8 hours; Domperidone 10mg before meals",
        "note": "Eat bland food. Avoid spicy/fatty food. See doctor if pain is severe.",
    },
    "stomach pain": {
        "medicines": ["Mefenamic acid 500mg", "Antispasmodic (Meftal Spas)"],
        "dosage": "Mefenamic acid 500mg every 8 hours after food",
        "note": "If pain is severe or accompanied by fever, consult a doctor.",
    },
    "cramps": {
        "medicines": ["Mefenamic acid 500mg", "Magnesium supplement"],
        "dosage": "Mefenamic acid 500mg every 8 hours after food",
        "note": "For menstrual cramps, apply a heating pad. Consult a doctor for severe cramps.",
    },
    "dehydration": {
        "medicines": ["ORS (Oral Rehydration Salts)", "Electrolyte drink"],
        "dosage": "ORS: 200–400ml every 1–2 hours",
        "note": "Sip slowly. Seek emergency care if unable to retain fluids.",
    },
    "allergy": {
        "medicines": ["Cetirizine 10mg", "Loratadine 10mg", "Fexofenadine 120mg"],
        "dosage": "Cetirizine 10mg once daily (at bedtime); Loratadine 10mg once daily",
        "note": "Avoid known allergens. Topical hydrocortisone for skin allergies.",
    },
    "allergic": {
        "medicines": ["Cetirizine 10mg", "Loratadine 10mg"],
        "dosage": "Cetirizine 10mg once daily",
        "note": "Identify and avoid the allergen. See a doctor for severe allergic reactions.",
    },
    "rash": {
        "medicines": ["Hydrocortisone cream 1%", "Cetirizine 10mg"],
        "dosage": "Hydrocortisone cream: apply thinly twice daily; Cetirizine 10mg once daily",
        "note": "Do not scratch. Keep skin clean and dry. See a doctor if rash spreads rapidly.",
    },
    "itching": {
        "medicines": ["Cetirizine 10mg", "Calamine lotion"],
        "dosage": "Cetirizine 10mg once daily; calamine lotion: apply as needed",
        "note": "Keep skin moisturised. Avoid harsh soaps.",
    },
    "skin allergy": {
        "medicines": ["Hydrocortisone cream 1%", "Cetirizine 10mg"],
        "dosage": "Apply hydrocortisone cream twice daily; Cetirizine 10mg once daily",
        "note": "Avoid the allergen. See a dermatologist for persistent skin reactions.",
    },
    "pain": {
        "medicines": ["Paracetamol 500mg", "Ibuprofen 400mg"],
        "dosage": "Paracetamol 500mg every 6 hours or Ibuprofen 400mg every 8 hours",
        "note": "Take Ibuprofen with food. Avoid prolonged use without medical advice.",
    },
    "ache": {
        "medicines": ["Paracetamol 500mg", "Ibuprofen 400mg"],
        "dosage": "Paracetamol 500mg every 6 hours or Ibuprofen 400mg every 8 hours",
        "note": "Take Ibuprofen with food.",
    },
    "body ache": {
        "medicines": ["Paracetamol 500mg", "Ibuprofen 400mg"],
        "dosage": "Paracetamol 500mg every 6 hours; rest well and stay hydrated",
        "note": "Usually accompanies viral infections like flu. See doctor if severe.",
    },
    "muscle pain": {
        "medicines": ["Ibuprofen 400mg", "Diclofenac gel (topical)"],
        "dosage": "Ibuprofen 400mg every 8 hours after food; diclofenac gel: apply 3 times daily",
        "note": "Apply ice/heat pack for localised muscle pain. Rest the affected area.",
    },
    "joint pain": {
        "medicines": ["Ibuprofen 400mg", "Diclofenac gel (topical)"],
        "dosage": "Ibuprofen 400mg every 8 hours after food; diclofenac gel: apply 3 times daily",
        "note": "Rest the joint. See a doctor for chronic joint pain.",
    },
    "inflammation": {
        "medicines": ["Ibuprofen 400mg", "Diclofenac 50mg"],
        "dosage": "Ibuprofen 400mg every 8 hours after food",
        "note": "Apply ice pack for localised inflammation. Consult a doctor if severe.",
    },
    "inflamed": {
        "medicines": ["Ibuprofen 400mg", "Diclofenac 50mg"],
        "dosage": "Ibuprofen 400mg every 8 hours after food",
        "note": "Ice and rest for local inflammation.",
    },
    "infection": {
        "medicines": ["Consult a doctor for antibiotics"],
        "dosage": "Antibiotic prescription needed",
        "note": "Do NOT self-prescribe antibiotics. See a doctor for proper diagnosis and prescription.",
    },
    "insomnia": {
        "medicines": ["Melatonin 5mg (OTC)", "Diphenhydramine 25mg (short-term only)"],
        "dosage": "Melatonin 5mg 30 minutes before bed",
        "note": "Prescription medicines (benzodiazepines) require a doctor's prescription. Practice good sleep hygiene.",
    },
    "sleepless": {
        "medicines": ["Melatonin 5mg"],
        "dosage": "Melatonin 5mg 30 minutes before bed",
        "note": "Avoid screens before bed. Maintain a consistent sleep schedule.",
    },
    "anxiety": {
        "medicines": ["Consult a doctor"],
        "dosage": "Prescription required",
        "note": "Anxiolytics (e.g., alprazolam, diazepam) require a prescription. Try deep breathing exercises for mild anxiety.",
    },
    "weakness": {
        "medicines": ["Vitamin B-complex", "Iron supplement (if anaemia suspected)", "ORS for hydration"],
        "dosage": "Vitamin B-complex: 1 tablet daily; Iron supplement as prescribed",
        "note": "Eat balanced meals. Stay hydrated. See a doctor if weakness is persistent.",
    },
    "fatigue": {
        "medicines": ["Vitamin B12 supplement", "Iron supplement", "Vitamin D3"],
        "dosage": "Vitamin B12 500mcg daily; Vitamin D3 1000 IU daily",
        "note": "Rest adequately. Check for anaemia or thyroid issues with a doctor.",
    },
    "diabetes": {
        "medicines": ["Metformin (prescription required)"],
        "dosage": "Prescription required",
        "note": "Diabetes management MUST be supervised by a doctor. Monitor blood sugar regularly.",
    },
    "hypertension": {
        "medicines": ["See a doctor immediately"],
        "dosage": "Prescription required",
        "note": "High blood pressure requires medical management. Do NOT self-medicate. Monitor BP regularly.",
    },
    "high blood pressure": {
        "medicines": ["See a doctor immediately"],
        "dosage": "Prescription required",
        "note": "High blood pressure requires medical supervision. Reduce salt intake and exercise regularly.",
    },
    "cholesterol": {
        "medicines": ["Atorvastatin (prescription required)", "Omega-3 supplements (OTC)"],
        "dosage": "Omega-3 1000mg daily (OTC); statins require a prescription",
        "note": "Adopt a low-fat diet, exercise regularly, and consult a doctor for statin therapy.",
    },
}


def _build_symptom_response(symptoms_str: str) -> str:
    """Build a deterministic pharma response from the symptom knowledge base."""
    symptom_list = [s.strip().lower() for s in symptoms_str.split(",")]
    responses: list[str] = []

    for symptom in symptom_list:
        entry = _SYMPTOM_KB.get(symptom)
        if entry:
            meds = ", ".join(entry["medicines"])
            dosage = entry["dosage"]
            note = entry["note"]
            block = (
                f"**{symptom.title()}**: Recommended medicine(s) — {meds}.\n"
                f"Dosage: {dosage}.\n"
                f"Note: {note}"
            )
            responses.append(block)

    if responses:
        header = "Based on your symptoms, here are my recommendations:\n\n"
        footer = "\n\n⚠️ *Always consult a licensed pharmacist or doctor before starting any medication, especially for children, pregnant women, or if you have other health conditions.*"
        return header + "\n\n".join(responses) + footer
    return ""  # no match — fall through to Ollama


async def _symptom_recommendation_response(symptoms_str: str, query: str) -> str:
    """Return deterministic KB answer, then enrich with Ollama if available."""
    # Try knowledge base first
    kb_answer = _build_symptom_response(symptoms_str)
    if kb_answer:
        return kb_answer

    # Fallback: enhanced Ollama prompt
    if _chat_llm is None:
        return (
            f"For the symptoms you described ({symptoms_str}), I recommend consulting "
            "a licensed pharmacist or doctor. Common OTC options for mild symptoms include "
            "paracetamol for fever/pain, cetirizine for allergies, and omeprazole for acidity. "
            "Please start Ollama ('ollama run llama3') for detailed AI-powered recommendations."
        )
    pharma_prompt = (
        "You are PharmaGenie, a professional AI pharmacy assistant. "
        "The user is experiencing the following symptoms: " + symptoms_str + ". "
        "Provide a clear, professional response that: "
        "1) Names the most appropriate OTC medicine(s) with exact dosage. "
        "2) Advises when to see a doctor. "
        "3) Gives 1-2 home care tips. "
        "Format: symptom → medicine name (dosage) → note. "
        "Example: Fever → Paracetamol 500mg every 6 hours → Consult a doctor if fever > 103°F. "
        "Be concise and specific.\n\nUser query: " + query + "\n\nAssistant:"
    )
    try:
        result = await _chat_llm.ainvoke(pharma_prompt)
        content = str(result.content).strip() if hasattr(result, "content") else str(result).strip()
        if content:
            return content + "\n\n⚠️ *Always consult a licensed pharmacist or doctor before starting any medication.*"
        return (
            f"For {symptoms_str}, common OTC remedies include paracetamol for fever/pain, "
            "cetirizine for allergies, and omeprazole for acidity. Please consult a pharmacist for personalised advice."
        )
    except Exception:
        return (
            f"For {symptoms_str}, common OTC remedies include paracetamol for fever/pain, "
            "cetirizine for allergies, and omeprazole for acidity. Please consult a pharmacist for personalised advice."
        )


async def _general_chat_response(query: str) -> str:
    """Use Ollama llama3 to answer general pharmacy / health queries."""
    if _chat_llm is None:
        return (
            "I'm your PharmaGenie assistant! I can help with medicine information, "
            "dosage guidance, drug interactions, and general health questions. "
            "However, my AI model (Ollama) is not currently running. "
            "Please start Ollama with 'ollama run llama3' to enable full responses. "
            "For urgent medical questions, please consult a licensed pharmacist."
        )
    prompt = f"{_GENERAL_CHAT_SYSTEM}\n\nUser: {query}\n\nAssistant:"
    try:
        result = await _chat_llm.ainvoke(prompt)
        content = str(result.content).strip() if hasattr(result, "content") else str(result).strip()
        return content if content else "I couldn't generate a response. Please try rephrasing your question."
    except Exception as exc:
        return (
            f"I encountered an issue while generating a response ({exc}). "
            "Please ensure Ollama is running with 'ollama run llama3' and try again."
        )


async def route_query(query: str):
    plan = await plan_query(query)

    intent = plan.get("intent")
    entities = plan.get("entities", {})

    if intent == "purchase_order":
        items_raw = entities.get("items", [])
        medicine_name = entities.get("medicine_name", "")

        purchase_items: list[dict] = []
        if isinstance(items_raw, list) and items_raw:
            purchase_items = [
                {"name": str(i.get("name", "")), "quantity": int(i.get("quantity", 1))}
                for i in items_raw if i.get("name")
            ]
        if not purchase_items and medicine_name:
            import re as _re
            qty_m = _re.search(r'\b(\d+)\b', query)
            purchase_items = [{"name": medicine_name, "quantity": int(qty_m.group(1)) if qty_m else 1}]

        # Enrich with live price and stock from warehouse (DB may be unavailable)
        enriched: list[dict] = []
        for item in purchase_items:
            try:
                wh = await warehouse_check(item["name"])
                enriched.append({
                    "name": wh.get("medicine_name", item["name"]),
                    "quantity": item["quantity"],
                    "price": wh.get("price", 0.0),
                    "stock": wh.get("stock", 99),
                })
            except Exception:
                # DB unavailable — use item as-is with safe defaults
                enriched.append({
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "price": 0.0,
                    "stock": 99,
                })

        summary = ", ".join(f"{i['quantity']}× {i['name']}" for i in enriched)
        return {
            "status": "purchase_order",
            "intent": "purchase_order",
            "items": enriched,
            "message": f"Got it! Adding to your cart: {summary}. Taking you to checkout now…",
        }

    if intent == "warehouse_check":
        medicine_name = entities.get("medicine_name")
        try:
            return await warehouse_check(medicine_name)
        except Exception as exc:
            return {"status": "error", "message": f"Could not check warehouse: {exc}"}
    elif intent in ("prescription_check", "recommendation"):
        # "recommendation" from old LLM responses is treated as a safety/availability check
        medicine_name = entities.get("medicine_name")
        dosage_value = entities.get("dosage_mg")
        dosage_mg = None

        if dosage_value is not None:
            try:
                dosage_mg = int(dosage_value)
            except (TypeError, ValueError):
                dosage_mg = None

        if not medicine_name:
            return {
                "status": "error",
                "message": "Medicine name not provided for prescription check."
            }
        try:
            return await safety_check(medicine_name, dosage_mg)
        except Exception as exc:
            return {"status": "error", "message": f"Safety check failed: {exc}"}

    elif intent == "symptom_recommendation":
        symptoms_str = entities.get("symptoms", "")
        if not symptoms_str:
            symptoms_str = query  # fallback: use raw query
        response_text = await _symptom_recommendation_response(symptoms_str, query)
        return {
            "status": "chat",
            "intent": "symptom_recommendation",
            "message": response_text,
        }

    elif intent == "general_chat":
        response_text = await _general_chat_response(query)
        return {
            "status": "chat",
            "intent": "general_chat",
            "message": response_text,
        }

    else:
        # Unrecognised intent — treat as a general chat query so users always get an answer
        response_text = await _general_chat_response(query)
        return {
            "status": "chat",
            "intent": "general_chat",
            "message": response_text,
        }
