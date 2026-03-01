"""Gemini-powered prescription scanner — POST /prescription/scan
Uses a 2-pass approach (gemini-2.5-flash):
  Pass 1 — extract raw text from the image
  Pass 2 — parse raw text into structured JSON
This mirrors the gemini-agent/prescription_authorization logic for higher reliability.
"""
import json
import logging
import re
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prescription", tags=["Prescription"])


def _strip_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?", "", t).strip()
        t = re.sub(r"```$", "", t).strip()
    return t


def _parse_result(raw: str) -> dict:
    """Extract JSON from Gemini response, return safe defaults on failure."""
    clean = _strip_fence(raw)
    match = re.search(r"\{.*\}", clean, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


@router.post("/scan")
async def scan_prescription(file: UploadFile = File(...)):
    """
    Upload a prescription image → Gemini Vision (2-pass) extracts medicines.

    Returns:
      {
        status, filename,
        medicines: [{name, dosage, frequency, duration, quantity, instructions}],
        doctor_name, patient_name, diagnosis, date, confidence
      }
    """
    if not file.filename:
        raise HTTPException(400, "File is required")
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only image files are supported (JPG, PNG, HEIC, etc.)")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(400, "Uploaded file is empty")

    if not settings.GEMINI_API_KEY:
        raise HTTPException(503, "GEMINI_API_KEY is not configured in the backend .env")

    try:
        import google.generativeai as genai  # older SDK — google-generativeai in requirements.txt
        from PIL import Image

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        pil_image = Image.open(BytesIO(image_bytes))

        # ── Pass 1: extract raw OCR text ──────────────────────────────────────
        ocr_prompt = (
            "Extract all readable text from this prescription image exactly as written. "
            "Return plain text only, no formatting."
        )
        ocr_response = model.generate_content([ocr_prompt, pil_image])
        raw_text = (ocr_response.text or "").strip()

        # ── Pass 2: parse raw text into structured JSON ───────────────────────
        parse_prompt = (
            "You are a medical document parser. Convert the following prescription text "
            "into strict JSON only — no markdown, no backticks, no explanations.\n\n"
            "Use EXACTLY this schema:\n"
            "{\n"
            '  "patient_name": "string or null",\n'
            '  "doctor_name": "string or null",\n'
            '  "prescription_date": "string or null",\n'
            '  "diagnosis": "string or null",\n'
            '  "medicines": [\n'
            '    {\n'
            '      "name": "Medicine Name",\n'
            '      "dosage": "e.g. 500mg",\n'
            '      "frequency": "e.g. twice daily",\n'
            '      "duration": "e.g. 7 days",\n'
            '      "quantity": 10,\n'
            '      "instructions": "e.g. take with food"\n'
            '    }\n'
            '  ],\n'
            '  "notes": "string or null",\n'
            '  "confidence": "high | medium | low"\n'
            "}\n\n"
            "Rules:\n"
            "- Extract EVERY medicine listed.\n"
            "- If quantity is not stated, use 1.\n"
            "- If a field is unknown, use null or empty string.\n"
            "- Return ONLY the JSON object.\n\n"
            f"Prescription text:\n{raw_text}"
        )
        parse_response = model.generate_content(parse_prompt)
        parsed = _parse_result(parse_response.text or "")

        # Normalise medicines array
        medicines = []
        for med in parsed.get("medicines", []):
            if not isinstance(med, dict):
                continue
            medicines.append({
                "name":         str(med.get("name", "")).strip(),
                "dosage":       str(med.get("dosage", "")).strip(),
                "frequency":    str(med.get("frequency", "")).strip(),
                "duration":     str(med.get("duration", "")).strip(),
                "quantity":     int(med.get("quantity") or 1),
                "instructions": str(med.get("instructions", "")).strip(),
            })

        return {
            "status":     "success",
            "filename":   file.filename,
            "raw_text":   raw_text,
            "medicines":  medicines,
            "doctor_name":   parsed.get("doctor_name"),
            "patient_name":  parsed.get("patient_name"),
            "diagnosis":     parsed.get("diagnosis"),
            "date":          parsed.get("prescription_date"),
            "notes":         parsed.get("notes"),
            "confidence":    parsed.get("confidence", "low"),
        }

    except ImportError as e:
        raise HTTPException(500, f"Missing dependency: {e}. Run: pip install google-generativeai pillow")
    except Exception as e:
        msg = str(e)
        logger.error("Gemini scan error: %s", msg)
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
            raise HTTPException(
                429,
                "Gemini API quota exhausted. Wait for daily reset (midnight PT) "
                "or enable billing at https://console.cloud.google.com",
            )
        if "API_KEY_INVALID" in msg or "invalid api key" in msg.lower() or "api key not valid" in msg.lower():
            raise HTTPException(503, f"Gemini API key is invalid — {msg}")
        if "403" in msg or "permission" in msg.lower():
            raise HTTPException(503, f"Gemini API access denied — {msg}")
        raise HTTPException(500, f"Prescription scan failed: {msg}")
