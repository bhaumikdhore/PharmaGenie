from fastapi import APIRouter
from app.services.data_loader import (
    load_medicines_from_csv,
    load_customer_history_from_csv,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/load-data")
async def load_data():
    await load_medicines_from_csv("medicine_master.csv")
    await load_customer_history_from_csv("customer_history.csv")
    return {"status": "Data loaded successfully"}