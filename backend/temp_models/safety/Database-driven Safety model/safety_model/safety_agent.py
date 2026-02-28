from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .db import get_session
from .models import Medicine


@dataclass
class SafetyAssessment:
    medicine_name: str
    requested_daily_dosage_mg: Optional[int]
    requires_prescription: bool
    controlled_level: int
    max_daily_dosage_mg: Optional[int]
    is_safe: bool
    reasons: list[str]


class SafetyAgent:
    """
    Simple safety agent that makes decisions based on the medicines table.
    """

    def assess(self, medicine_name: str, daily_dosage_mg: Optional[int]) -> Optional[SafetyAssessment]:
        medicine_name = medicine_name.strip()
        if not medicine_name:
            return None

        with get_session() as session:
            med: Optional[Medicine] = (
                session.query(Medicine)
                .filter(Medicine.name.ilike(medicine_name))
                .one_or_none()
            )

        if med is None:
            return None

        reasons: list[str] = []
        is_safe = True

        if med.requires_prescription:
            reasons.append("Requires a valid prescription.")

        if med.controlled_level and med.controlled_level > 0:
            reasons.append(f"Controlled substance (level {med.controlled_level}).")

        if daily_dosage_mg is not None and med.max_daily_dosage is not None:
            if daily_dosage_mg > med.max_daily_dosage:
                is_safe = False
                reasons.append(
                    f"Requested dosage {daily_dosage_mg} mg exceeds max daily dosage {med.max_daily_dosage} mg."
                )

        if med.requires_prescription or (med.controlled_level and med.controlled_level > 0):
            # Not necessarily "unsafe", but requires extra checks
            reasons.append("Consult a licensed medical professional before use.")

        return SafetyAssessment(
            medicine_name=med.name,
            requested_daily_dosage_mg=daily_dosage_mg,
            requires_prescription=med.requires_prescription,
            controlled_level=med.controlled_level,
            max_daily_dosage_mg=med.max_daily_dosage,
            is_safe=is_safe,
            reasons=reasons,
        )

