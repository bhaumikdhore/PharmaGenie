from __future__ import annotations

import os
import re
import sys
import importlib
from contextlib import contextmanager
from pathlib import Path

from app.core.langfuse_config import langfuse


TEMP_MODELS_DIR = Path(__file__).resolve().parents[2] / "temp_models"
PLANNER_ROOT = TEMP_MODELS_DIR / "planner"
BILLING_ROOT = TEMP_MODELS_DIR / "billing" / "billing_agent"
PRESCRIPTION_ROOT = TEMP_MODELS_DIR / "prescription" / "prescription_authorization"


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


def _load_dependencies():
    _ensure_sys_path(PLANNER_ROOT)

    from planner_agent.planner import Planner
    return Planner


def _build_order_items(query: str) -> list[dict]:
    if not query:
        return []

    items: list[dict] = []
    for qty, name in re.findall(r"(\d+)\s+([a-zA-Z][a-zA-Z0-9_-]*)", query.lower()):
        items.append({"name": name, "quantity": int(qty), "in_stock": True})

    if not items:
        simple = re.findall(r"\b([a-zA-Z][a-zA-Z0-9_-]*)\b", query.lower())
        if simple:
            items.append({"name": simple[-1], "quantity": 1, "in_stock": True})

    return items


def _normalize_order_items(input_data: dict) -> list[dict]:
    order_items = input_data.get("order_items")
    if isinstance(order_items, list) and order_items:
        normalized = []
        for item in order_items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip().lower()
            if not name:
                continue
            quantity = int(item.get("quantity", 1))
            normalized.append({"name": name, "quantity": quantity, "in_stock": bool(item.get("in_stock", True))})
        if normalized:
            return normalized

    cart_items = input_data.get("cart_items")
    if isinstance(cart_items, list) and cart_items:
        normalized = []
        for item in cart_items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip().lower()
            if not name:
                continue
            quantity = int(item.get("quantity", 1))
            normalized.append({"name": name, "quantity": quantity, "in_stock": bool(item.get("in_stock", True))})
        if normalized:
            return normalized

    query = str(input_data.get("query", "")).strip()
    return _build_order_items(query)


async def run(input_data: dict) -> dict:
    _out: dict = {}
    with langfuse.start_as_current_span(name="planner-agent", input=input_data) as span:
        try:
            Planner = _load_dependencies()
            _ensure_sys_path(BILLING_ROOT)
            _ensure_sys_path(PRESCRIPTION_ROOT)

            order_items = _normalize_order_items(input_data)
            if not order_items:
                _out = {
                    "agent": "planner",
                    "status": "error",
                    "message": "Provide `order_items`, `cart_items`, or a parsable `query` (e.g. 'buy 2 paracetamol').",
                }
            else:
                prescription_image_path = input_data.get("prescription_image_path") or input_data.get("image_path")

                def prescription_analyzer(path: str | None) -> dict:
                    if path:
                        with _working_directory(PRESCRIPTION_ROOT):
                            analyze_prescription = importlib.import_module("main").analyze_prescription
                            return analyze_prescription(path)
                    return {
                        "status": "success",
                        "decision": "APPROVED",
                        "message": "No prescription image provided for test route.",
                    }

                def billing_processor(items: list[dict]) -> dict:
                    cart_items = [{"name": item["name"], "quantity": int(item.get("quantity", 1))} for item in items]
                    with _working_directory(BILLING_ROOT):
                        process_billing = importlib.import_module("billing_main").process_billing
                        return process_billing(cart_items)

                planner = Planner(
                    stock_checker=lambda items: {"status": "success", "items": items},
                    prescription_analyzer=prescription_analyzer,
                    billing_processor=billing_processor,
                )
                result = planner.execute_workflow(order_items, prescription_image_path)
                _out = {"agent": "planner", **result}
        except Exception as e:
            _out = {"agent": "planner", "status": "error", "message": str(e)}
        finally:
            try:
                span.update(output=_out)
                langfuse.flush()
            except Exception:
                pass
    return _out
