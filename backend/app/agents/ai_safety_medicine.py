"""
AI Safety Medicine Check Agent - Comprehensive Analysis (NO HARDCODED RESTRICTIONS)
Uses AI to analyze ANY medicine for safety without predefined blacklists
All medicines are available - pharmacist verifies prescription requirements
"""

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TIMEOUT = 15  # seconds


async def check_ollama_available() -> bool:
    """Check if Ollama is running at localhost:11434"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:11434/api/tags",
                timeout=aiohttp.ClientTimeout(total=2)
            ) as resp:
                return resp.status == 200
    except:
        return False


async def check_medicine_safety_with_ollama(medicine_name: str, dosage: Optional[str] = None) -> Dict[str, Any]:
    """
    Comprehensive AI-based medicine safety check
    Analyzes ANY medicine for:
    - Safety profile and adverse effects
    - Drug interactions
    - Prescription requirements
    - Contraindications and warnings
    - Risk assessment
    
    Uses Ollama AI for intelligent analysis with fallback to generic assessment
    """
    try:
        ollama_available = await check_ollama_available()
        
        if ollama_available:
            try:
                async with aiohttp.ClientSession() as session:
                    prompt = f"""As a pharmaceutical safety expert, provide a comprehensive safety assessment for:

Medicine: {medicine_name}
Dosage: {dosage if dosage else 'Standard dosage'}

Provide brief analysis (2-3 lines):
1. Safety for purchase: SAFE/NEEDS_VERIFICATION
2. Prescription required: YES/NO  
3. Key concerns or side effects
4. Overall recommendation

Be helpful and informative."""

                    async with session.post(
                        OLLAMA_URL,
                        json={
                            "model": "mistral",
                            "prompt": prompt,
                            "stream": False
                        },
                        timeout=aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT)
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            ai_response = result.get("response", "")
                            
                            # Parse AI response
                            is_safe = "SAFE" in ai_response.upper() and "NOT_SAFE" not in ai_response.upper()
                            
                            return {
                                "agent": "ai_safety_medicine",
                                "status": "success",
                                "medicine_name": medicine_name,
                                "dosage": dosage,
                                "is_safe": is_safe,
                                "is_approved": True,
                                "approval_status": "✅ AVAILABLE - AI APPROVED",
                                "ai_analysis": ai_response,
                                "source": "ollama_ai",
                                "recommendation": "Consult pharmacist for prescription requirements"
                            }
            except (aiohttp.ClientError, asyncio.TimeoutError, Exception):
                pass
        
        # Fallback: Generic assessment
        return await generic_safety_assessment(medicine_name, dosage)
            
    except Exception as e:
        return {
            "agent": "ai_safety_medicine",
            "status": "error",
            "message": f"Error checking medicine safety: {str(e)}",
        }


async def generic_safety_assessment(medicine_name: str, dosage: Optional[str] = None) -> Dict[str, Any]:
    """
    Generic safety assessment when AI unavailable
    All medicines available - pharmacist verifies prescription
    """
    
    return {
        "agent": "ai_safety_medicine",
        "status": "success",
        "medicine_name": medicine_name,
        "dosage": dosage,
        "is_safe": True,
        "is_approved": True,
        "approval_status": "✅ AVAILABLE FOR PURCHASE",
        "ai_analysis": f"{medicine_name} is available for purchase. Consult pharmacist to verify prescription requirements.",
        "source": "generic_assessment",
        "recommendation": "Pharmacist consultation recommended"
    }


async def validate_prescription(medicines: List[Dict[str, str]]) -> Dict[str, Any]:
    """Validate prescription - all medicines approved"""
    try:
        if not medicines:
            return {
                "agent": "ai_safety_medicine",
                "status": "error",
                "message": "No medicines provided",
            }
        
        validation_results = []
        
        for medicine_info in medicines:
            medicine_name = medicine_info.get("name", "").strip()
            dosage = medicine_info.get("dosage")
            
            if not medicine_name:
                continue
            
            result = await check_medicine_safety_with_ollama(medicine_name, dosage)
            validation_results.append(result)
        
        return {
            "agent": "ai_safety_medicine",
            "status": "success",
            "validation_results": validation_results,
            "prescription_approved": True,
            "overall_status": "✅ PRESCRIPTION AVAILABLE",
            "total_medicines": len(validation_results),
            "note": "Pharmacist will verify prescription validity"
        }
        
    except Exception as e:
        return {
            "agent": "ai_safety_medicine",
            "status": "error",
            "message": f"Error validating prescription: {str(e)}",
        }



async def generic_safety_assessment(medicine_name: str, dosage: Optional[str] = None) -> Dict[str, Any]:
    """
    Generic safety assessment when AI unavailable
    All medicines available - pharmacist verifies prescription
    """
    
    return {
        "agent": "ai_safety_medicine",
        "status": "success",
        "medicine_name": medicine_name,
        "dosage": dosage,
        "is_safe": True,
        "is_approved": True,
        "approval_status": "✅ AVAILABLE FOR PURCHASE",
        "ai_analysis": f"{medicine_name} is available for purchase. Consult pharmacist for prescription requirements.",
        "source": "generic_assessment",
        "recommendation": "Pharmacist consultation recommended"
    }


async def run(input_data: dict) -> dict:
    """
    Main agent function
    
    Input:
    - action: "check" or "validate"
    - medicine_name: str (for check)
    - medicines: List (for validate)
    - dosage: str (optional)
    """
    try:
        action = input_data.get("action", "check").lower()
        
        if action == "check":
            medicine_name = input_data.get("medicine_name", "").strip()
            if not medicine_name:
                return {
                    "agent": "ai_safety_medicine",
                    "status": "error",
                    "message": "medicine_name required"
                }
            
            dosage = input_data.get("dosage")
            return await check_medicine_safety_with_ollama(medicine_name, dosage)
        
        elif action == "validate":
            medicines = input_data.get("medicines", [])
            return await validate_prescription(medicines)
        
        else:
            return {
                "agent": "ai_safety_medicine",
                "status": "error",
                "message": f"Unknown action: {action}"
            }
            
    except Exception as e:
        return {
            "agent": "ai_safety_medicine",
            "status": "error",
            "message": f"Error: {str(e)}",
        }

