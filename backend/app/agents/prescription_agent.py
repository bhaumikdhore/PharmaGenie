from __future__ import annotations

import os
import sys
import importlib
from contextlib import contextmanager
from pathlib import Path


PRESCRIPTION_ROOT = Path(__file__).resolve().parents[2] / "temp_models" / "prescription" / "prescription_authorization"


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


async def run(input_data: dict) -> dict:
    try:
        _ensure_sys_path(PRESCRIPTION_ROOT)

        image_path = input_data.get("image_path") or input_data.get("prescription_image_path")
        if not image_path:
            return {
                "agent": "prescription",
                "status": "error",
                "message": "Provide `image_path` (or `prescription_image_path`) for prescription analysis.",
            }

        with _working_directory(PRESCRIPTION_ROOT):
            analyze_prescription = importlib.import_module("main").analyze_prescription
            result = analyze_prescription(str(image_path))

        return {"agent": "prescription", **result}
    except Exception as e:
        return {"agent": "prescription", "status": "error", "message": str(e)}
