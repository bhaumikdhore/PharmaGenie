def final_decision(doctor_valid, date_valid, unmatched_medicines):
    try:
        if not doctor_valid:
            return "REJECTED - Invalid Doctor"
        if not date_valid:
            return "REJECTED - Invalid Date"
        if unmatched_medicines:
            return "REJECTED - Unmatched Medicines"
        return "APPROVED"
    except Exception as e:
        raise RuntimeError(f"Final decision computation failed: {e}")