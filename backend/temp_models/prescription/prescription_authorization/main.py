from models.ocr_engine import extract_text_from_image
from models.text_cleaner import clean_text
from models.extractor import extract_registration, extract_date, extract_medicines
from models.doctor_validator import validate_doctor
from models.medicine_matcher import match_medicines
from models.fraud_detector import check_date_validity
from models.decision_engine import final_decision

import os

def analyze_prescription(image_path: str) -> dict:
    if not os.path.exists(image_path):
        return {
            "status": "error",
            "message": "Image not found"
        }

    try:
        # Step 1: OCR
        raw_text = extract_text_from_image(image_path)

        # Step 2: Clean
        cleaned_text = clean_text(raw_text)

        # Step 3: Extract
        reg_no = extract_registration(cleaned_text)
        date = extract_date(cleaned_text)
        medicines = extract_medicines(cleaned_text)

        # Step 4: Validate
        doctor_valid = validate_doctor(reg_no)
        date_valid = check_date_validity(date)

        # Step 5: Match medicines
        matched, unmatched = match_medicines(medicines)

        # Step 6: Decision
        decision = final_decision(doctor_valid, date_valid, unmatched)

        return {
            "status": "success",
            "doctor_valid": doctor_valid,
            "date_valid": date_valid,
            "matched_medicines": matched,
            "unmatched_medicines": unmatched,
            "decision": decision,
            "registration_number": reg_no,
            "extracted_medicines": medicines
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    result = analyze_prescription("printed prescription.jpeg")
    print(result)
