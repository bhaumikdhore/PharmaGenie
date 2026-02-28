import re

def extract_registration(cleaned_text):
    try:
        # Match Indian format (e.g., MH-12345), DEA # (e.g., 1111111), or NPI # (e.g., 2222222)
        match = re.search(r'\b(?:MH-\d{5}|DEA\s?#:\s?\d{7}|NPI\s?#:\s?\d{7})\b', cleaned_text, re.IGNORECASE)
        if match:
            # Extract only the numeric part for DEA/NPI
            if 'DEA' in match.group(0).upper() or 'NPI' in match.group(0).upper():
                return re.search(r'\d{7}', match.group(0)).group(0)
            return match.group(0)
        return None
    except Exception as e:
        raise RuntimeError(f"Registration extraction failed: {e}")

def extract_date(cleaned_text):
    try:
        match = re.search(r'\b\d{2}/\d{2}/\d{4}\b', cleaned_text)
        return match.group(0) if match else None
    except Exception as e:
        raise RuntimeError(f"Date extraction failed: {e}")

def extract_medicines(cleaned_text):
    try:
        medicines = []
        # Match medicine name + dosage + mg (e.g., "morphine 130 mg", "325-5 mg")
        pattern = re.compile(r'\b([a-zA-Z0-9-]+)\s+(\d{1,4}(?:-\d{1,4})?)\s?mg\b', re.IGNORECASE)
        for line in cleaned_text.splitlines():
            match = pattern.search(line)
            if match:
                medicines.append({"name": match.group(1), "dosage": match.group(2) + " mg"})
        return medicines
    except Exception as e:
        raise RuntimeError(f"Medicine extraction failed: {e}")