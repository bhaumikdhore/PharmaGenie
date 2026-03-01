"""
Prescription Requirement Agent
Checks if a medicine requires prescription and provides purchasing information
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any


async def run(input_data: dict) -> dict:
    """
    Check if a medicine requires prescription
    
    Params:
    - medicine_name: str (required) - Name of the medicine to check
    
    Returns:
    - agent: str = "prescription_requirement"
    - status: str = "success" | "error" | "not_found"
    - medicine_name: str
    - requires_prescription: bool
    - can_buy_without_prescription: bool
    - category: str
    - message: str
    """
    try:
        medicine_name = (input_data.get("medicine_name") or "").strip()
        
        if not medicine_name:
            return {
                "agent": "prescription_requirement",
                "status": "error",
                "message": "Provide `medicine_name`.",
            }
        
        # Load medicine master data
        csv_path = Path(__file__).resolve().parents[2] / "medicine_master.csv"
        
        if not csv_path.exists():
            return {
                "agent": "prescription_requirement",
                "status": "error",
                "message": "Medicine database not found.",
            }
        
        df = pd.read_csv(csv_path)
        
        # Case-insensitive search
        medicine_data = df[df['medicine_name'].str.lower() == medicine_name.lower()]
        
        if medicine_data.empty:
            return {
                "agent": "prescription_requirement",
                "status": "not_found",
                "message": f"Medicine '{medicine_name}' not found in database.",
                "medicine_name": medicine_name,
            }
        
        row = medicine_data.iloc[0]
        
        requires_prescription = str(row.get("prescription_required", "")).lower() in ["yes", "true", "1"]
        can_buy_without_prescription = not requires_prescription
        
        return {
            "agent": "prescription_requirement",
            "status": "success",
            "medicine_name": str(row.get("medicine_name", "")),
            "category": str(row.get("category", "")),
            "requires_prescription": requires_prescription,
            "can_buy_without_prescription": can_buy_without_prescription,
            "stock_status": "In Stock" if int(row.get("stock_quantity", 0)) > 0 else "Out of Stock",
            "stock_quantity": int(row.get("stock_quantity", 0)),
            "message": (
                f"This medicine {'REQUIRES' if requires_prescription else 'DOES NOT REQUIRE'} a prescription. "
                f"You can {'NOT ' if requires_prescription else ''}purchase it without prescription."
            ),
        }
        
    except Exception as e:
        return {
            "agent": "prescription_requirement",
            "status": "error",
            "message": f"Error checking prescription requirement: {str(e)}",
        }
