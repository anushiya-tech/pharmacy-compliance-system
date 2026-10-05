from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database import get_db
from backend.models import Medicine
from backend.schemas import (
    MedicineCreate,
    MedicineUpdate,
    MedicineResponse,
)

router = APIRouter(prefix="/medicines", tags=["Medicines & Inventory"])


@router.post(
    "",
    response_model=MedicineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new medicine",
    description="Add a new medicine to inventory. Medicine ID must be unique. Name and strength are required.",
)
def create_medicine(payload: MedicineCreate, db: Session = Depends(get_db)):
    existing = db.query(Medicine).filter(Medicine.medicine_id == payload.medicine_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Medicine with ID '{payload.medicine_id}' already exists.",
        )

    medicine = Medicine(
        medicine_id=payload.medicine_id,
        name=payload.name,
        generic_name=payload.generic_name,
        strength=payload.strength,
        dosage_form=payload.dosage_form,
        manufacturer=payload.manufacturer,
        batch_number=payload.batch_number,
        stock_quantity=payload.stock_quantity,
        unit_price=payload.unit_price,
        expiry_date=payload.expiry_date,
    )
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.get(
    "",
    response_model=List[MedicineResponse],
    summary="List all medicines",
    description="Retrieve list of medicines with optional pagination.",
)
def list_medicines(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Limit records per page"),
    db: Session = Depends(get_db),
):
    medicines = db.query(Medicine).offset(skip).limit(limit).all()
    return medicines


@router.get(
    "/search",
    response_model=List[MedicineResponse],
    summary="Search medicines",
    description="Search medicines by name or generic name (case-insensitive substring match).",
)
def search_medicines(
    name: str = Query(..., min_length=1, description="Medicine or generic name query"),
    db: Session = Depends(get_db),
):
    pattern = f"%{name}%"
    results = (
        db.query(Medicine)
        .filter(
            or_(
                Medicine.name.ilike(pattern),
                Medicine.generic_name.ilike(pattern),
            )
        )
        .all()
    )
    return results


@router.get(
    "/{medicine_id}",
    response_model=MedicineResponse,
    summary="Get medicine by ID",
    description="Retrieve details for a single medicine by its unique ID.",
)
def get_medicine(medicine_id: str, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine '{medicine_id}' not found.",
        )
    return medicine


@router.put(
    "/{medicine_id}",
    response_model=MedicineResponse,
    summary="Update medicine details",
    description="Update metadata, stock quantity, or pricing for an existing medicine.",
)
def update_medicine(
    medicine_id: str,
    payload: MedicineUpdate,
    db: Session = Depends(get_db),
):
    medicine = db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine '{medicine_id}' not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(medicine, key, value)

    db.commit()
    db.refresh(medicine)
    return medicine


@router.delete(
    "/{medicine_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete medicine",
    description="Remove a medicine from catalog. Returns confirmation message.",
)
def delete_medicine(medicine_id: str, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine '{medicine_id}' not found.",
        )
    db.delete(medicine)
    db.commit()
    return {"message": f"Medicine '{medicine_id}' successfully deleted.", "medicine_id": medicine_id}
