from datetime import datetime

def check_date_validity(prescription_date):
    try:
        if not prescription_date:
            return False

        date = datetime.strptime(prescription_date, '%m/%d/%Y')
        return date <= datetime.now()
    except Exception as e:
        raise RuntimeError(f"Date validity check failed: {e}")