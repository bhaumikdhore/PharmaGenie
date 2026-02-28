from __future__ import annotations

import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path


SAFETY_PROJECT_ROOT = Path(__file__).resolve().parents[2] / "temp_models" / "safety" / "Database-driven Safety model"


def _ensure_sys_path(path: Path) -> None:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


async def run(input_data: dict) -> dict:
    try:
        _ensure_sys_path(SAFETY_PROJECT_ROOT)
        from safety_model.safety_agent import SafetyAgent

        medicine_name = (input_data.get("medicine_name") or input_data.get("medicine") or "").strip()
        dosage_mg = input_data.get("dosage_mg", input_data.get("dosage"))

        if not medicine_name:
            return {
                "agent": "safety",
                "status": "error",
                "message": "Provide `medicine_name` (or `medicine`).",
            }

        agent = SafetyAgent()
        result = agent.assess(medicine_name, dosage_mg)

        if result is None:
            return {
                "agent": "safety",
                "status": "not_found",
                "message": f"Medicine '{medicine_name}' not found in safety database.",
            }

        if is_dataclass(result):
            return {"agent": "safety", "status": "success", **asdict(result)}

        if isinstance(result, dict):
            return {"agent": "safety", "status": "success", **result}

        return {"agent": "safety", "status": "success", "result": str(result)}
    except Exception as e:
        return {"agent": "safety", "status": "error", "message": str(e)}
