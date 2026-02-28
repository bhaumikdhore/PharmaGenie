import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

TAX_RATE = 0.05

async def generate_simple_invoice(order, db: AsyncSession):

    unit_price = order.unit_price
    quantity = order.quantity

    subtotal = unit_price * quantity
    tax = subtotal * TAX_RATE
    total = subtotal + tax

    invoice_number = f"PG-{datetime.utcnow().year}-{str(uuid.uuid4())[:6]}"

    await db.execute(
        text("""
        INSERT INTO invoices (
            invoice_number, order_id, customer_name, customer_email,
            medicine_name, quantity, unit_price,
            subtotal, tax, total
        )
        VALUES (
            :invoice_number, :order_id, :customer_name, :customer_email,
            :medicine_name, :quantity, :unit_price,
            :subtotal, :tax, :total
        )
        """),
        {
            "invoice_number": invoice_number,
            "order_id": str(order.id),
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "medicine_name": order.medicine_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
        }
    )

    await db.commit()

    pdf_path = create_pdf(
        invoice_number,
        order.customer_name,
        order.medicine_name,
        quantity,
        unit_price,
        subtotal,
        tax,
        total,
    )

    return {
        "invoice_number": invoice_number,
        "total": total,
        "pdf_path": pdf_path
    }

def create_pdf(invoice_number, customer_name, medicine, qty, price, subtotal, tax, total):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
        from reportlab.lib.styles import getSampleStyleSheet

        file_path = f"invoices/{invoice_number}.pdf"

        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("PharmaGenie", styles["Title"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph(f"Invoice: {invoice_number}", styles["Normal"]))
        elements.append(Paragraph(f"Customer: {customer_name}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        data = [
            ["Medicine", "Qty", "Unit Price", "Subtotal"],
            [medicine, qty, price, subtotal],
        ]

        table = Table(data)
        elements.append(table)
        elements.append(Spacer(1, 12))

        elements.append(Paragraph(f"Tax (5%): {tax}", styles["Normal"]))
        elements.append(Paragraph(f"Total: {total}", styles["Normal"]))

        doc.build(elements)
        return file_path
    except Exception:
        # Fallback when PDF dependency is unavailable.
        file_path = f"invoices/{invoice_number}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("PharmaGenie Invoice\n")
            f.write(f"Invoice: {invoice_number}\n")
            f.write(f"Customer: {customer_name}\n")
            f.write(f"Medicine: {medicine}\n")
            f.write(f"Qty: {qty}\n")
            f.write(f"Unit Price: {price}\n")
            f.write(f"Subtotal: {subtotal}\n")
            f.write(f"Tax: {tax}\n")
            f.write(f"Total: {total}\n")
        return file_path
