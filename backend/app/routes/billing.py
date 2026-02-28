from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/{order_id}/pdf")
async def generate_invoice_pdf(order_id: int, db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT 
            o.id, o.quantity, o.total_amount, o.created_at,
            u.full_name, u.phone, u.email, u.age,
            m.name AS medicine_name, m.expiry_date, m.price
        FROM orders o
        JOIN medicines m ON o.medicine_id = m.id
        JOIN public.users u ON o.user_id = u.id
        WHERE o.id = :order_id
    """)

    result = await db.execute(query, {"order_id": order_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Order not found")

    subtotal = round(row.price * row.quantity, 2)
    gst = round(subtotal * 0.18, 2)
    grand_total = round(subtotal + gst, 2)
    invoice_number = f"INV-{str(row.id).zfill(4)}"

    file_path = f"invoice_{order_id}.pdf"

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>PharmaGenie Invoice</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Invoice Number: {invoice_number}", styles["Normal"]))
    elements.append(Paragraph(f"Customer: {row.full_name}", styles["Normal"]))
    elements.append(Paragraph(f"Phone: {row.phone}", styles["Normal"]))
    elements.append(Paragraph(f"Email: {row.email}", styles["Normal"]))
    elements.append(Paragraph(f"Age: {row.age}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [
        ["Medicine", "Expiry Date", "Quantity", "Unit Price", "Subtotal"],
        [row.medicine_name, row.expiry_date, row.quantity, f"{row.price:.2f}", f"{subtotal:.2f}"],
    ]

    table = Table(data, colWidths=[100, 100, 100, 100, 100])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])
    )

    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"GST (18%): {gst:.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Grand Total: {grand_total:.2f}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<i>Authorized Signature</i>", styles["Normal"]))

    doc.build(elements)

    await db.execute(
        text("""
        INSERT INTO invoices (invoice_number, order_id, customer_name, total_amount, pdf_path)
        VALUES (:invoice_number, :order_id, :customer_name, :total_amount, :pdf_path)
        """),
        {
            "invoice_number": invoice_number,
            "order_id": row.id,
            "customer_name": row.full_name,
            "total_amount": grand_total,
            "pdf_path": file_path,
        }
    )
    await db.commit()

    return FileResponse(file_path, media_type="application/pdf", filename=file_path)
