"""PharmaGenie Search API - Medicine search."""

from typing import Any

# Demo medicine catalog (expand in production)
MEDICINES = [
    {"name": "Paracetamol", "strength": "500mg", "type": "Tablet"},
    {"name": "Paracetamol", "strength": "650mg", "type": "Tablet"},
    {"name": "Metformin", "strength": "500mg", "type": "Tablet"},
    {"name": "Metformin", "strength": "850mg", "type": "Tablet"},
    {"name": "Insulin", "strength": "100 U/ml", "type": "Injection"},
    {"name": "Ibuprofen", "strength": "400mg", "type": "Tablet"},
    {"name": "Amoxicillin", "strength": "500mg", "type": "Capsule"},
    {"name": "Aspirin", "strength": "75mg", "type": "Tablet"},
    {"name": "Cetirizine", "strength": "10mg", "type": "Tablet"},
    {"name": "Omeprazole", "strength": "20mg", "type": "Capsule"},
]


def search_medicines(query: str) -> dict[str, Any]:
    """Search medicines by name."""
    q = (query or "").strip().lower()
    if not q:
        return {"message": "Here are some common medicines: Paracetamol, Metformin, Ibuprofen.", "results": MEDICINES[:5]}

    results = [m for m in MEDICINES if q in m["name"].lower()]
    if not results:
        return {"message": f"No medicines found for '{query}'. Try Paracetamol or Metformin.", "results": []}
    msg = f"Found {len(results)} result(s): " + ", ".join(f"{m['name']} {m['strength']}" for m in results[:5])
    return {"message": msg, "results": results}
