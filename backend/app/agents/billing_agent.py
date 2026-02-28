from __future__ import annotations

import os
import re
import sys
import importlib
from contextlib import contextmanager
from pathlib import Path


BILLING_ROOT = Path(__file__).resolve().parents[2] / "temp_models" / "billing" / "billing_agent"


def _ensure_sys_path(path: Path) -> None:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


@contextmanager
def _working_directory(path: Path):
    current = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(current)


def _normalize_cart_items(input_data: dict) -> list[dict]:
    cart_items = input_data.get("cart_items") or input_data.get("items") or []
    normalized: list[dict] = []

    if isinstance(cart_items, list):
        for item in cart_items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip().lower()
            if not name:
                continue
            quantity = int(item.get("quantity", 1))
            normalized.append({"name": name, "quantity": quantity})

    if normalized:
        return normalized

    query = str(input_data.get("query", "")).strip().lower()
    for qty, name in re.findall(r"(\d+)\s+([a-zA-Z][a-zA-Z0-9_-]*)", query):
        normalized.append({"name": name, "quantity": int(qty)})

    return normalized


async def run(input_data: dict) -> dict:
    try:
        _ensure_sys_path(BILLING_ROOT)

        cart_items = _normalize_cart_items(input_data)
        if not cart_items:
            return {
                "agent": "billing",
                "status": "error",
                "message": "Provide `cart_items`/`items` or a parsable `query` (e.g. 'buy 2 paracetamol').",
            }

        with _working_directory(BILLING_ROOT):
            process_billing = importlib.import_module("billing_main").process_billing
            invoice = process_billing(cart_items)

        return {"agent": "billing", "status": "success", "invoice": invoice}
    except Exception as e:
        return {"agent": "billing", "status": "error", "message": str(e)}
