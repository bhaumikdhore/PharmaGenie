from app.agents import (
    planner_agent,
    safety_agent,
    warehouse_agent,
    billing_agent,
    prescription_agent,
)

async def route_query(query: str):
    planner_result = await planner_agent.run({"query": query})

    intent = planner_result.get("intent")

    if intent == "check_stock":
        return await warehouse_agent.run(planner_result)

    elif intent == "safety_check":
        return await safety_agent.run(planner_result)

    elif intent == "billing":
        return await billing_agent.run(planner_result)

    elif intent == "prescription_validation":
        return await prescription_agent.run(planner_result)

    else:
        return {"error": "Unknown intent"}