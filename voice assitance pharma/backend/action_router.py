"""PharmaGenie Action Router - Routes intents to backend APIs."""

from typing import Any

from api.cart import add_to_cart, remove_from_cart, view_cart
from api.orders import create_order, check_order_status
from api.search import search_medicines
from intent_detector import detect_intent


def route_action(intent_data: dict[str, Any]) -> dict[str, Any]:
    """
    Route intent to appropriate backend action.
    Returns: {"success": bool, "message": str, "data": Any}
    """
    intent = intent_data.get("intent", "unknown")
    medicine_name = intent_data.get("medicine_name")
    quantity = intent_data.get("quantity", 1)

    try:
        if intent == "add_to_cart":
            result = add_to_cart(medicine_name, quantity)
            return {"success": True, "message": result["message"], "data": result.get("cart")}

        if intent == "remove_from_cart":
            result = remove_from_cart(medicine_name)
            return {"success": True, "message": result["message"], "data": result.get("cart")}

        if intent == "view_cart":
            result = view_cart()
            return {"success": True, "message": result["message"], "data": result.get("items")}

        if intent == "search":
            result = search_medicines(medicine_name or "")
            return {"success": True, "message": result["message"], "data": result.get("results")}

        if intent == "check_order":
            result = check_order_status()
            return {"success": True, "message": result["message"], "data": result.get("orders")}

        if intent == "create_order":
            result = create_order()
            return {"success": True, "message": result["message"], "data": result.get("order")}

        if intent == "check_interactions":
            return {
                "success": True,
                "message": "Please provide medicine names to check interactions. You can add them to cart and we'll verify.",
                "data": None,
            }

        if intent == "greeting":
            return {
                "success": True,
                "message": "Namaste! I'm PharmaGenie, your voice pharmacy assistant. You can ask me to add medicines, search, or check your order.",
                "data": None,
            }

        return {
            "success": False,
            "message": "I didn't quite understand. Try saying 'Add paracetamol' or 'Search for metformin'.",
            "data": None,
        }
    except Exception as e:
        return {"success": False, "message": str(e), "data": None}


def process_voice_text(text: str) -> dict[str, Any]:
    """Full pipeline: speech text → intent → action → response."""
    intent_data = detect_intent(text)
    return route_action(intent_data)
