from app.services.planner_agent import plan_query
from app.services.warehouse_agent import warehouse_check
from app.services.safety_agent import safety_check


async def route_query(query: str):
    plan = await plan_query(query)

    intent = plan.get("intent")
    entities = plan.get("entities", {})

    if intent == "warehouse_check":
        medicine_name = entities.get("medicine_name")
        return await warehouse_check(medicine_name)
    elif intent == "prescription_check":
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

        return await safety_check(medicine_name, dosage_mg)

    elif intent == "general_chat":
        return {
            "status": "chat",
            "message": "General conversation not implemented yet."
        }

    else:
        return {
            "status": "unsupported",
            "message": f"Intent '{intent}' not implemented yet."
        }
