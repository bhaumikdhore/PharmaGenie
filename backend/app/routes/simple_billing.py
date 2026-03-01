import csv
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.services.local_order_fallback import get_fallback_order
from app.services.simple_billing import generate_simple_invoice
from app.models.order import Order

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.post("/generate/{order_id}")
async def generate_invoice(order_id: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    invoice = await generate_simple_invoice(order, db)

    return invoice


@router.get("/{order_id}")
async def get_billing_order(order_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return {
            "order_id": order.id,
            "user_id": order.user_id,
            "medicine_id": order.medicine_id,
            "quantity": order.quantity,
            "status": order.status,
            "total_amount": float(order.total_amount) if order.total_amount is not None else None,
            "requires_prescription": order.requires_prescription,
            "storage": "primary_db",
        }
    except HTTPException:
        raise
    except Exception:
        if not order_id.isdigit():
            raise HTTPException(status_code=404, detail="Order not found")
        fallback = get_fallback_order(int(order_id))
        if not fallback:
            raise HTTPException(status_code=404, detail="Order not found")

        return {
            "order_id": fallback["id"],
            "user_id": fallback["user_id"],
            "medicine_id": fallback["medicine_id"],
            "quantity": fallback["quantity"],
            "status": fallback["status"],
            "total_amount": fallback["total_amount"],
            "requires_prescription": bool(fallback["requires_prescription"]),
            "storage": "local_fallback",
        }


@router.get("/{order_id}/pdf")
async def download_bill(order_id: str, db: AsyncSession = Depends(get_db)):
    if not order_id.isdigit():
        raise HTTPException(status_code=400, detail="order_id must be numeric")

    file_path = await generate_invoice_pdf_file(int(order_id), db)
    invoice_filename = f"invoice_{order_id}.pdf"

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=invoice_filename,
    )


async def generate_invoice_pdf_file(order_id: int, db: AsyncSession) -> str:
    row = await _fetch_invoice_row(order_id, db)
    if not row:
        raise HTTPException(status_code=404, detail="Order or related billing data not found")

    quantity = int(row["quantity"])
    unit_price = Decimal(str(row["price"]))
    subtotal = (unit_price * Decimal(quantity)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    gst = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = (subtotal + gst).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    invoice_number = f"INV-{order_id:04d}"
    invoice_date = str(row["created_at"])
    invoice_filename = f"invoice_{order_id}.pdf"
    invoices_dir = Path("invoices")
    invoices_dir.mkdir(parents=True, exist_ok=True)
    file_path = invoices_dir / invoice_filename

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(file_path), pagesize=(8.27 * inch, 11.69 * inch))
    elements = []

    elements.append(Paragraph("PharmaGenie", styles["Title"]))
    elements.append(Paragraph("TAX INVOICE", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(f"Invoice Number: {invoice_number}", styles["Normal"]))
    elements.append(Paragraph(f"Invoice Date: {invoice_date}", styles["Normal"]))
    elements.append(Spacer(1, 0.25 * inch))

    elements.append(Paragraph("Customer Details", styles["Heading3"]))
    customer_table = Table(
        [
            ["Name", str(row["full_name"])],
            ["Phone", str(row["phone"])],
            ["Email", str(row["email"])],
            ["Age", str(row["age"])],
        ],
        colWidths=[1.5 * inch, 5.8 * inch],
    )
    customer_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(customer_table)
    elements.append(Spacer(1, 0.25 * inch))

    elements.append(Paragraph("Medicine Details", styles["Heading3"]))
    medicine_table = Table(
        [
            ["Medicine", "Expiry", "Qty", "Unit Price", "Subtotal"],
            [
                str(row["medicine_name"]),
                str(row["expiry_date"]),
                str(quantity),
                f"{unit_price:.2f}",
                f"{subtotal:.2f}",
            ],
        ],
        colWidths=[2.2 * inch, 1.4 * inch, 0.7 * inch, 1.2 * inch, 1.2 * inch],
    )
    medicine_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F4F4F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(medicine_table)
    elements.append(Spacer(1, 0.25 * inch))

    summary_table = Table(
        [
            ["Subtotal", f"{subtotal:.2f}"],
            ["GST (18%)", f"{gst:.2f}"],
            ["Grand Total", f"{total:.2f}"],
        ],
        colWidths=[2.5 * inch, 1.5 * inch],
        hAlign="RIGHT",
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 2), (-1, 2), colors.lightgrey),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Authorized Pharmacist Signature", styles["Normal"]))

    doc.build(elements)
    return str(file_path.resolve())


async def _fetch_invoice_row(order_id: int, db: AsyncSession):
    invoice_query = text(
        """
        SELECT
            COALESCE(u.full_name, 'N/A') AS full_name,
            COALESCE(u.phone, 'N/A') AS phone,
            COALESCE(u.email, 'N/A') AS email,
            COALESCE(CAST(u.age AS TEXT), 'N/A') AS age,
            COALESCE(m.name, CONCAT('Medicine-', CAST(o.medicine_id AS TEXT))) AS medicine_name,
            'N/A' AS expiry_date,
            COALESCE(m.price, 0) AS price,
            o.quantity,
            o.created_at
        FROM public.orders o
        LEFT JOIN public.users u ON CAST(u.id AS TEXT) = o.user_id
        LEFT JOIN public.medicines m ON m.id = o.medicine_id
        WHERE o.id = :order_id
        """
    )

    try:
        result = await db.execute(invoice_query, {"order_id": order_id})
        row = result.mappings().first()
    except SQLAlchemyError:
        row = None
    except Exception:
        row = None

    if row:
        return row
    return _build_local_invoice_row(order_id)


def _read_customers_csv() -> dict[str, dict]:
    csv_path = Path(__file__).resolve().parents[2] / "customers.csv"
    customers: dict[str, dict] = {}
    if not csv_path.exists():
        return customers
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = (row.get("customer_id") or "").strip()
            if cid:
                customers[cid] = row
    return customers


def _read_medicines_csv() -> dict[int, dict]:
    csv_path = Path(__file__).resolve().parents[2] / "medicine_master.csv"
    meds: dict[int, dict] = {}
    if not csv_path.exists():
        return meds
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                mid = int((row.get("medicine_id") or "").strip())
            except Exception:
                continue
            meds[mid] = row
    return meds


def _build_local_invoice_row(order_id: int) -> dict | None:
    fallback = get_fallback_order(order_id)
    if not fallback:
        return None

    customers = _read_customers_csv()
    medicines = _read_medicines_csv()

    raw_user_id = str(fallback.get("user_id", "")).strip()
    mapped_customer_id = raw_user_id if raw_user_id.upper().startswith("C") else f"C{int(raw_user_id):03d}" if raw_user_id.isdigit() else raw_user_id
    customer = customers.get(mapped_customer_id, {})

    medicine_id = int(fallback.get("medicine_id", 0) or 0)
    medicine = medicines.get(medicine_id, {})
    quantity = int(fallback.get("quantity", 1) or 1)
    total_amount = Decimal(str(fallback.get("total_amount", 0) or 0))
    unit_price = (total_amount / Decimal(quantity)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if quantity else Decimal("0.00")

    return {
        "full_name": customer.get("customer_name", f"Customer {mapped_customer_id or raw_user_id}"),
        "phone": customer.get("phone", "N/A"),
        "email": customer.get("email", "N/A"),
        "age": "N/A",
        "medicine_name": medicine.get("medicine_name", f"Medicine-{medicine_id}"),
        "expiry_date": "N/A",
        "price": unit_price,
        "quantity": quantity,
        "created_at": fallback.get("created_at", datetime.utcnow().isoformat()),
    }
