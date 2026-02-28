from datetime import datetime
import uuid

def generate_invoice(bill_details, subtotal, tax):

    invoice_id = str(uuid.uuid4())[:8]
    total_amount = subtotal + tax

    return {
        "invoice_id": invoice_id,
        "date": str(datetime.now()),
        "items": bill_details,
        "subtotal": subtotal,
        "tax": tax,
        "total": round(total_amount, 2)
    }