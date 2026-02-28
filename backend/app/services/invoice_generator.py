import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

INVOICE_FOLDER = "invoices"

os.makedirs(INVOICE_FOLDER, exist_ok=True)

def _value(item, key):
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key)


def generate_invoice_pdf(invoice, order, medicine):
    invoice_number = _value(invoice, "invoice_number")
    file_path = f"{INVOICE_FOLDER}/{invoice_number}.pdf"

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>PharmaGenie</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Invoice Number: {invoice_number}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {_value(invoice, 'created_at')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [
        ["Medicine", "Quantity", "Price", "Total"],
        [
            medicine.name,
            str(order.quantity),
            str(medicine.price),
            str(_value(invoice, "subtotal")),
        ],
    ]

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Tax: {_value(invoice, 'tax_amount')}", styles["Normal"]))
    elements.append(Paragraph(f"Total Amount: {_value(invoice, 'total_amount')}", styles["Normal"]))

    doc.build(elements)

    return file_path
