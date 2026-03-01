"""PharmaGenie Orders API - Create and check orders."""

from typing import Any

from api.cart import _cart

# Demo order storage
_orders: list[dict[str, Any]] = []
_order_counter = 1000


def create_order() -> dict[str, Any]:
    """Create order from current cart."""
    global _orders, _order_counter, _cart

    if not _cart:
        return {"message": "Your cart is empty. Add medicines first.", "order": None}

    order = {
        "order_id": f"ORD-{_order_counter}",
        "items": list(_cart),
        "status": "placed",
    }
    _orders.append(order)
    _order_counter += 1
    _cart.clear()

    items_str = ", ".join(f"{i['medicine_name']} x{i['quantity']}" for i in order["items"])
    return {
        "message": f"Order {order['order_id']} placed! Items: {items_str}",
        "order": order,
    }


def check_order_status() -> dict[str, Any]:
    """Check latest order status."""
    if not _orders:
        return {"message": "No orders yet. Add items and place an order.", "orders": []}
    latest = _orders[-1]
    return {
        "message": f"Your latest order {latest['order_id']} status: {latest['status']}",
        "orders": list(_orders),
    }
