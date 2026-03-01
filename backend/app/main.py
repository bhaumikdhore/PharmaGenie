import sys
import os

# Ensure the project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Load .env before anything else
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except Exception:
    pass

import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.admin import router as admin_router
from app.routes.ai import router as ai_router
from app.routes.health import router as health_router
from app.routes.llm_test import router as llm_test_router
from app.routes.orders import router as orders_router, legacy_router as legacy_orders_router
from app.routes.analytics import router as analytics_router
from app.routes.users import router as users_router
from app.routes.warehouse import router as warehouse_router
from app.routes import simple_billing, payment
from app.routes.prescription import router as prescription_router
from app.routes.delivery import router as delivery_router
from app.routes.notification import router as notification_router
from app.routes.prescription_storage import router as prescription_storage_router
from app.routes.refill_notifications import router as refill_notifications_router
from app.core.config import settings
from app.db.init_db import init_db

app = FastAPI(
    title=settings.APP_NAME,
    openapi_tags=[
        {"name": "Orders", "description": "Order creation and webhook trigger endpoints"},
        {"name": "Billing", "description": "Billing and invoice generation endpoints"},
        {"name": "admin", "description": "Administrative data-loading endpoints"},
    ],
)
logger = logging.getLogger(__name__)

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

frontend_dev_origin = os.getenv("FRONTEND_DEV_ORIGIN")
if frontend_dev_origin and frontend_dev_origin not in CORS_ORIGINS:
    CORS_ORIGINS.append(frontend_dev_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(health_router)
app.include_router(ai_router)
app.include_router(llm_test_router)
app.include_router(orders_router)
app.include_router(legacy_orders_router)
app.include_router(analytics_router)
app.include_router(users_router)
app.include_router(warehouse_router)
app.include_router(simple_billing.router)
app.include_router(payment.router)
app.include_router(prescription_router)
app.include_router(delivery_router)
app.include_router(notification_router)
app.include_router(prescription_storage_router)
app.include_router(refill_notifications_router)

REQUIRED_POST_ROUTES = {
    "/orders/create",
    "/post/order",
    "/billing/generate/{order_id}",
}
REQUIRED_GET_ROUTES = {
    "/billing/{order_id}",
    "/billing/{order_id}/pdf",
}


def _verify_required_routes() -> None:
    methods_by_path: dict[str, set[str]] = {}
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if not methods:
            continue
        methods_by_path.setdefault(route.path, set()).update(methods)

    missing_post = sorted(path for path in REQUIRED_POST_ROUTES if "POST" not in methods_by_path.get(path, set()))
    missing_get = sorted(path for path in REQUIRED_GET_ROUTES if "GET" not in methods_by_path.get(path, set()))
    missing = missing_post + missing_get
    if missing:
        raise RuntimeError(f"Missing required route(s): {', '.join(missing)}")


@app.on_event("startup")
async def startup_event() -> None:
    _verify_required_routes()
    # Avoid blocking the entire API if DB is temporarily unreachable.
    try:
        await asyncio.wait_for(init_db(), timeout=10)
    except Exception as exc:
        logger.warning("DB init skipped during startup: %s", exc)


@app.get("/")
async def root():
    return {"message": "PharmaGenie API running"}
