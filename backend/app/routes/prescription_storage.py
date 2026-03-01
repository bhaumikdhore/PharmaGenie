"""
Prescription Storage Routes
Handles storing and retrieving prescription photos for repetitive orders
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.db.session import get_session
from app.services.prescription_storage_service import PrescriptionStorageService
from pathlib import Path
import os

router = APIRouter(prefix="/prescriptions/storage", tags=["Prescription Storage"])


async def ensure_upload_dir():
    """Ensure upload directory exists"""
    os.makedirs(PrescriptionStorageService.UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_prescription(
    customer_id: str = Form(...),
    medicine_name: str = Form(...),
    photo: UploadFile = File(...),
    doctor_name: str = Form(None),
    dosage: str = Form(None),
    frequency: str = Form(None),
    duration_days: int = Form(None),
    expiry_days: int = Form(180),
    notes: str = Form(None),
    session: AsyncSession = Depends(get_session),
):
    """
    Upload and store a prescription photo for future use
    
    **Body Parameters:**
    - customer_id: str - Customer ID (required)
    - medicine_name: str - Medicine name (required)
    - photo: file - Prescription photo file (required)
    - doctor_name: str - Doctor name (optional)
    - dosage: str - Dosage info (optional)
    - frequency: str - Frequency e.g., "Once daily" (optional)
    - duration_days: int - Duration in days (optional)
    - expiry_days: int - Expiry duration in days, default 180 (optional)
    - notes: str - Additional notes (optional)
    """
    
    try:
        await ensure_upload_dir()
        
        # Read file content
        photo_data = await photo.read()
        
        # Create file path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_medicine_name = medicine_name.replace(" ", "_").lower()
        filename = f"{customer_id}_{safe_medicine_name}_{timestamp}.{photo.filename.split('.')[-1]}"
        photo_path = PrescriptionStorageService.UPLOAD_DIR / filename
        
        # Save file
        with open(photo_path, "wb") as f:
            f.write(photo_data)
        
        # Store in database
        prescription = await PrescriptionStorageService.store_prescription(
            session=session,
            customer_id=customer_id,
            medicine_name=medicine_name,
            photo_path=str(photo_path),
            photo_data=photo_data,
            doctor_name=doctor_name,
            dosage=dosage,
            frequency=frequency,
            duration_days=duration_days,
            expiry_days=expiry_days,
            notes=notes,
        )
        
        await session.commit()
        
        return {
            "status": "success",
            "message": f"Prescription photo stored successfully for {medicine_name}",
            "prescription": {
                "id": prescription.id,
                "medicine_name": prescription.medicine_name,
                "doctor_name": prescription.doctor_name,
                "upload_date": prescription.upload_date.isoformat(),
                "expiry_date": prescription.expiry_date.isoformat(),
            },
        }
    
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading prescription: {str(e)}")


@router.get("/list/{customer_id}")
async def list_prescriptions(
    customer_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get all stored prescriptions for a customer
    
    **Path Parameters:**
    - customer_id: str - Customer ID
    """
    
    try:
        prescriptions = await PrescriptionStorageService.get_stored_prescriptions(
            session=session,
            customer_id=customer_id,
        )
        
        return {
            "status": "success",
            "count": len(prescriptions),
            "prescriptions": [
                {
                    "id": p.id,
                    "medicine_name": p.medicine_name,
                    "doctor_name": p.doctor_name,
                    "dosage": p.dosage,
                    "frequency": p.frequency,
                    "upload_date": p.upload_date.isoformat(),
                    "expiry_date": p.expiry_date.isoformat() if p.expiry_date else None,
                    "usage_count": p.usage_count,
                    "last_used": p.last_used.isoformat() if p.last_used else None,
                    "is_active": p.is_active,
                }
                for p in prescriptions
            ],
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prescriptions: {str(e)}")


@router.get("/medicine/{customer_id}/{medicine_name}")
async def get_prescription_for_medicine(
    customer_id: str,
    medicine_name: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get stored prescription for a specific medicine (for auto-reuse in repetitive orders)
    
    **Path Parameters:**
    - customer_id: str - Customer ID
    - medicine_name: str - Medicine name
    """
    
    try:
        prescription = await PrescriptionStorageService.get_prescription_by_medicine(
            session=session,
            customer_id=customer_id,
            medicine_name=medicine_name,
        )
        
        if not prescription:
            return {
                "status": "not_found",
                "message": f"No stored prescription found for {medicine_name}",
            }
        
        return {
            "status": "success",
            "prescription": {
                "id": prescription.id,
                "medicine_name": prescription.medicine_name,
                "doctor_name": prescription.doctor_name,
                "dosage": prescription.dosage,
                "frequency": prescription.frequency,
                "upload_date": prescription.upload_date.isoformat(),
                "expiry_date": prescription.expiry_date.isoformat() if prescription.expiry_date else None,
                "usage_count": prescription.usage_count,
                "last_used": prescription.last_used.isoformat() if prescription.last_used else None,
                "is_active": prescription.is_active,
            },
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prescription: {str(e)}")


@router.post("/use/{prescription_id}")
async def use_prescription(
    prescription_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Mark a stored prescription as used (for tracking repetitive order usage)
    
    **Path Parameters:**
    - prescription_id: int - Prescription ID
    """
    
    try:
        prescription = await PrescriptionStorageService.use_prescription(
            session=session,
            prescription_id=prescription_id,
        )
        
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        await session.commit()
        
        return {
            "status": "success",
            "message": "Prescription usage recorded",
            "prescription": {
                "id": prescription.id,
                "usage_count": prescription.usage_count,
                "last_used": prescription.last_used.isoformat(),
            },
        }
    
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error using prescription: {str(e)}")


@router.delete("/deactivate/{prescription_id}")
async def deactivate_prescription(
    prescription_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Deactivate a stored prescription (won't be used for repetitive orders)
    
    **Path Parameters:**
    - prescription_id: int - Prescription ID
    """
    
    try:
        success = await PrescriptionStorageService.deactivate_prescription(
            session=session,
            prescription_id=prescription_id,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        await session.commit()
        
        return {
            "status": "success",
            "message": "Prescription deactivated successfully",
        }
    
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deactivating prescription: {str(e)}")


@router.get("/stats/{customer_id}")
async def get_prescription_stats(
    customer_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get prescription storage statistics for a customer
    
    **Path Parameters:**
    - customer_id: str - Customer ID
    """
    
    try:
        stats = await PrescriptionStorageService.get_prescription_stats(
            session=session,
            customer_id=customer_id,
        )
        
        return {
            "status": "success",
            "stats": stats,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


@router.post("/cleanup")
async def cleanup_expired_prescriptions(
    session: AsyncSession = Depends(get_session),
):
    """
    Cleanup: Deactivate all expired prescriptions (admin endpoint)
    """
    
    try:
        count = await PrescriptionStorageService.cleanup_expired_prescriptions(
            session=session,
        )
        
        await session.commit()
        
        return {
            "status": "success",
            "message": f"Deactivated {count} expired prescriptions",
            "count": count,
        }
    
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error cleaning up prescriptions: {str(e)}")
