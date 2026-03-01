from __future__ import annotations

from databases import Database

from app.config import get_settings


settings = get_settings()
database = Database(settings.database_url)


async def connect_db() -> None:
    if not database.is_connected:
        await database.connect()


async def disconnect_db() -> None:
    if database.is_connected:
        await database.disconnect()


async def get_db() -> Database:
    if not database.is_connected:
        await database.connect()
    return database

