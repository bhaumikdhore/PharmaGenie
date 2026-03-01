import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().parents[2] / "local_orders_fallback.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fallback_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            medicine_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            total_amount REAL,
            requires_prescription INTEGER NOT NULL DEFAULT 0,
            fallback_reason TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def create_fallback_order(order_data: dict[str, Any], fallback_reason: str) -> dict[str, Any]:
    with _connect() as conn:
        _init_table(conn)
        cursor = conn.execute(
            """
            INSERT INTO fallback_orders (
                user_id,
                medicine_id,
                quantity,
                status,
                total_amount,
                requires_prescription,
                fallback_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_data["user_id"],
                int(order_data["medicine_id"]),
                int(order_data["quantity"]),
                order_data.get("status") or "pending",
                float(order_data["total_amount"]) if order_data.get("total_amount") is not None else None,
                1 if order_data.get("requires_prescription") else 0,
                fallback_reason,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM fallback_orders WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row) if row else {}


def get_fallback_order(order_id: int) -> dict[str, Any] | None:
    with _connect() as conn:
        _init_table(conn)
        row = conn.execute("SELECT * FROM fallback_orders WHERE id = ?", (order_id,)).fetchone()
        return dict(row) if row else None


def list_fallback_orders_by_user(user_id: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        _init_table(conn)
        rows = conn.execute(
            "SELECT * FROM fallback_orders WHERE user_id = ? ORDER BY datetime(created_at) DESC, id DESC",
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def update_fallback_order_status(order_id: int, status: str) -> bool:
    with _connect() as conn:
        _init_table(conn)
        cursor = conn.execute(
            "UPDATE fallback_orders SET status = ? WHERE id = ?",
            (status, order_id),
        )
        conn.commit()
        return cursor.rowcount > 0
