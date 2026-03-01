"""PharmaGenie Cart API - In-memory cart for demo."""

from typing import Any

# In-memory cart (replace with DB in production)
_cart: list[dict[str, Any]] = []
_id_counter = 1


def add_to_cart(medicine_name: str | None, quantity: int = 1) -> dict[str, Any]:
    """Add medicine to cart."""
    if not medicine_name:
        return {"message": "Please tell me which medicine you want to add.", "cart": _cart}

    global _id_counter
    item = {
        "id": _id_counter,
        "medicine_name": medicine_name.strip().title(),
        "quantity": max(1, quantity),
    }
    _id_counter += 1
    _cart.append(item)
    return {
        "message": f"{item['medicine_name']} added to your cart.",
        "cart": list(_cart),
    }


def remove_from_cart(medicine_name: str | None) -> dict[str, Any]:
    """Remove medicine from cart."""
    global _cart
    if not medicine_name:
        return {"message": "Please tell me which medicine to remove.", "cart": _cart}

    name = medicine_name.strip().title()
    _cart = [i for i in _cart if i["medicine_name"] != name]
    return {"message": f"{name} removed from cart.", "cart": _cart}


def view_cart() -> dict[str, Any]:
    """View cart contents."""
    if not _cart:
        return {"message": "Your cart is empty.", "items": []}
    items_str = ", ".join(f"{i['medicine_name']} x{i['quantity']}" for i in _cart)
    return {"message": f"Your cart has: {items_str}", "items": list(_cart)}
