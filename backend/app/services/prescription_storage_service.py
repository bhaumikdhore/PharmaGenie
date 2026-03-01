"""
Prescription Storage Service
Manages storing, retrieving, and managing prescription photos for repetitive orders
"""

from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prescription_storage import PrescriptionStorage
from pathlib import Path
import os


class PrescriptionStorageService:
    """Service for managing stored prescriptions"""
    
    UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "prescriptions"
    
    @classmethod
    async def store_prescription(
        cls,
        session: AsyncSession,
        customer_id: str,
        medicine_name: str,
        photo_path: str,
        photo_data: bytes,
        doctor_name: str = None,
        dosage: str = None,
        frequency: str = None,
        duration_days: int = None,
        expiry_days: int = 180,  # Default 6 months
        notes: str = None,
    ) -> PrescriptionStorage:
        """Store a new prescription photo"""
        
        expiry_date = datetime.utcnow() + timedelta(days=expiry_days)
        
        prescription = PrescriptionStorage(
            customer_id=customer_id,
            medicine_name=medicine_name,
            prescription_photo_path=photo_path,
            prescription_photo_data=photo_data,
            doctor_name=doctor_name,
            dosage=dosage,
            frequency=frequency,
            duration_days=duration_days,
            expiry_date=expiry_date,
            notes=notes,
            is_active=True,
        )
        
        session.add(prescription)
        await session.flush()  # Get the ID but don't commit yet
        
        return prescription
    
    @classmethod
    async def get_stored_prescriptions(
        cls,
        session: AsyncSession,
        customer_id: str,
        is_active: bool = True,
    ) -> list[PrescriptionStorage]:
        """Get all stored prescriptions for a customer"""
        
        query = select(PrescriptionStorage).where(
            and_(
                PrescriptionStorage.customer_id == customer_id,
                PrescriptionStorage.is_active == is_active,
            )
        ).order_by(desc(PrescriptionStorage.upload_date))
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def get_prescription_by_medicine(
        cls,
        session: AsyncSession,
        customer_id: str,
        medicine_name: str,
    ) -> PrescriptionStorage | None:
        """Get stored prescription for a specific medicine"""
        
        query = select(PrescriptionStorage).where(
            and_(
                PrescriptionStorage.customer_id == customer_id,
                PrescriptionStorage.medicine_name.ilike(f"%{medicine_name}%"),
                PrescriptionStorage.is_active == True,
            )
        ).order_by(desc(PrescriptionStorage.upload_date))
        
        result = await session.execute(query)
        return result.scalars().first()
    
    @classmethod
    async def use_prescription(
        cls,
        session: AsyncSession,
        prescription_id: int,
    ) -> PrescriptionStorage | None:
        """Mark prescription as used (increment usage count and update last_used)"""
        
        query = select(PrescriptionStorage).where(PrescriptionStorage.id == prescription_id)
        result = await session.execute(query)
        prescription = result.scalars().first()
        
        if prescription:
            prescription.usage_count += 1
            prescription.last_used = datetime.utcnow()
            session.add(prescription)
            await session.flush()
        
        return prescription
    
    @classmethod
    async def deactivate_prescription(
        cls,
        session: AsyncSession,
        prescription_id: int,
    ) -> bool:
        """Deactivate a stored prescription"""
        
        query = select(PrescriptionStorage).where(PrescriptionStorage.id == prescription_id)
        result = await session.execute(query)
        prescription = result.scalars().first()
        
        if prescription:
            prescription.is_active = False
            session.add(prescription)
            await session.flush()
            return True
        
        return False
    
    @classmethod
    async def get_active_prescriptions(
        cls,
        session: AsyncSession,
    ) -> list[PrescriptionStorage]:
        """Get all active prescriptions (for admin purposes)"""
        
        query = select(PrescriptionStorage).where(
            PrescriptionStorage.is_active == True,
        ).order_by(desc(PrescriptionStorage.upload_date))
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def cleanup_expired_prescriptions(
        cls,
        session: AsyncSession,
    ) -> int:
        """Deactivate expired prescriptions and return count"""
        
        query = select(PrescriptionStorage).where(
            and_(
                PrescriptionStorage.expiry_date <= datetime.utcnow(),
                PrescriptionStorage.is_active == True,
            )
        )
        
        result = await session.execute(query)
        expired = result.scalars().all()
        
        for prescription in expired:
            prescription.is_active = False
            session.add(prescription)
        
        await session.flush()
        return len(expired)
    
    @classmethod
    async def get_prescription_stats(
        cls,
        session: AsyncSession,
        customer_id: str,
    ) -> dict:
        """Get prescription usage statistics for a customer"""
        
        prescriptions = await cls.get_stored_prescriptions(session, customer_id)
        
        total_prescriptions = len(prescriptions)
        total_uses = sum(p.usage_count for p in prescriptions)
        most_used = max(prescriptions, key=lambda p: p.usage_count) if prescriptions else None
        
        return {
            "total_stored": total_prescriptions,
            "total_uses": total_uses,
            "most_used_medicine": most_used.medicine_name if most_used else None,
            "most_used_count": most_used.usage_count if most_used else 0,
        }
