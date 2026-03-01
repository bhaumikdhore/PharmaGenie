import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/users", tags=["Users"])


class UserSyncRequest(BaseModel):
    id: str | None = None
    email: str
    role: str | None = None
    full_name: str | None = None
    password: str | None = None
    password_hash: str | None = None


@router.post("/sync")
async def sync_user(payload: UserSyncRequest, db: AsyncSession = Depends(get_db)):
    """
    Upsert a Supabase-authenticated user into public.users and optionally persist their role.
    """
    desired_role = (payload.role or "customer").strip() or "customer"

    # Keep provided auth user ID when available; otherwise create one.
    resolved_id = (payload.id or "").strip() or str(uuid.uuid4())
    resolved_password_hash = payload.password_hash or payload.password

    # Primary upsert path: id + email + role.
    query_with_role = text(
        """
        INSERT INTO public.users (id, email, password_hash, full_name, role)
        VALUES (:id, :email, :password_hash, :full_name, :role)
        ON CONFLICT (id)
        DO UPDATE SET email = EXCLUDED.email, role = COALESCE(EXCLUDED.role, public.users.role)
        RETURNING id, email, role
        """
    )

    # Fallback path if role column is absent in deployed schema.
    query_without_role = text(
        """
        INSERT INTO public.users (id, email, password_hash, full_name)
        VALUES (:id, :email, :password_hash, :full_name)
        ON CONFLICT (id)
        DO UPDATE SET email = EXCLUDED.email
        RETURNING id, email
        """
    )

    try:
        params = {
            "id": resolved_id,
            "email": payload.email,
            "password_hash": resolved_password_hash,
            "full_name": payload.full_name,
            "role": desired_role,
        }
        try:
            result = await db.execute(query_with_role, params)
            row = result.mappings().first()
        except Exception:
            # Schema without role column.
            fallback_result = await db.execute(query_without_role, params)
            row = fallback_result.mappings().first()

        await db.commit()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to sync user")

        user_dict = dict(row)
        # Ensure a role key is always present for the frontend, even if the column does not exist.
        user_dict.setdefault("role", desired_role)
        return {"status": "synced", "user": user_dict}
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Unable to sync user: {exc}") from exc
