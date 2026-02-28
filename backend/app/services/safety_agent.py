from typing import Dict


CONTROLLED_MEDICINES = [
    "alprazolam",
    "diazepam",
    "codeine",
    "tramadol",
]

PRESCRIPTION_ONLY = [
    "ozempic",
    "semaglutide",
    "insulin",
    "metformin",
    "atorvastatin",
]

MAX_SAFE_DOSAGE = {
    "paracetamol": 4000  # mg per day
}


async def safety_check(medicine_name: str, dosage_mg: int = None) -> Dict:
    medicine_lower = medicine_name.lower()

    # Controlled drug
    if medicine_lower in CONTROLLED_MEDICINES:
        return {
            "status": "restricted",
            "requires_prescription": True,
            "level": "controlled",
            "message": "This medicine is a controlled substance and requires a valid prescription.",
        }

    # Prescription only
    if medicine_lower in PRESCRIPTION_ONLY:
        return {
            "status": "prescription_required",
            "requires_prescription": True,
            "level": "prescription",
            "message": "This medicine requires a valid doctor prescription.",
        }

    # Dosage check
    if dosage_mg and medicine_lower in MAX_SAFE_DOSAGE:
        if dosage_mg > MAX_SAFE_DOSAGE[medicine_lower]:
            return {
                "status": "unsafe_dosage",
                "requires_prescription": False,
                "level": "dosage",
                "message": "Requested dosage exceeds safe daily limit.",
            }

    return {
        "status": "safe",
        "requires_prescription": False,
        "level": "otc",
        "message": "No safety concerns detected.",
    }


async def run(input_data: dict) -> dict:
    medicine_name = input_data.get("medicine_name", "")
    dosage_mg = input_data.get("dosage_mg")
    return await safety_check(medicine_name, dosage_mg)