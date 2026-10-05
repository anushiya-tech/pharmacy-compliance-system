import os
import uuid
import json
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import Prescription
from backend.schemas import (
    PrescriptionCreate,
    PrescriptionUpdateStatus,
    PrescriptionUpdateOCR,
    PrescriptionResponse,
    ExtractedMedicineItemSchema,
)
from backend.compliance_adapter import compliance_adapter
from prescription_processing.extraction.service import PrescriptionExtractionService

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions & OCR"])
extraction_service = PrescriptionExtractionService()


def _format_prescription_response(prescription: Prescription) -> PrescriptionResponse:
    """Helper to populate parsed extracted medicines into response."""
    extracted_items = compliance_adapter.extract_prescription_items(prescription)
    schema_items = [
        ExtractedMedicineItemSchema(
            medicine_name=item.medicine_name,
            normalized_name=item.normalized_name,
            strength_value=item.strength_value,
            strength_unit=item.strength_unit,
            dosage_form=item.dosage_form,
            quantity=item.quantity,
            frequency=item.frequency,
            confidence=item.confidence,
            extraction_status=item.extraction_status,
        )
        for item in extracted_items
    ]

    return PrescriptionResponse(
        prescription_id=prescription.prescription_id,
        patient_reference=prescription.patient_reference,
        doctor_name=prescription.doctor_name,
        prescription_date=prescription.prescription_date,
        image_path=prescription.image_path,
        extracted_text=prescription.extracted_text,
        ocr_metadata=prescription.ocr_metadata,
        status=prescription.status,
        created_at=prescription.created_at,
        extracted_medicines=schema_items,
    )


@router.post(
    "",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create prescription record",
    description="Create a prescription entry directly with optional extracted text or metadata.",
)
def create_prescription(payload: PrescriptionCreate, db: Session = Depends(get_db)):
    rx_id = payload.prescription_id or f"RX-{uuid.uuid4().hex[:8].upper()}"
    existing = db.query(Prescription).filter(Prescription.prescription_id == rx_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Prescription with ID '{rx_id}' already exists.",
        )

    # Initial status based on whether extracted text is present
    initial_status = "PROCESSED" if payload.extracted_text else "PENDING"

    prescription = Prescription(
        prescription_id=rx_id,
        patient_reference=payload.patient_reference,
        doctor_name=payload.doctor_name,
        prescription_date=payload.prescription_date,
        image_path=payload.image_path,
        extracted_text=payload.extracted_text,
        status=initial_status,
        created_at=datetime.utcnow(),
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return _format_prescription_response(prescription)


@router.post(
    "/upload",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload prescription image and run OCR extraction",
    description="Uploads a prescription image file, stores it locally, executes Member 2 OCR & entity extraction, and records the prescription in database.",
)
async def upload_prescription_image(
    file: UploadFile = File(..., description="Prescription image file (.png, .jpg, .jpeg)"),
    prescription_id: Optional[str] = Form(None, description="Optional custom prescription ID"),
    patient_reference: Optional[str] = Form(None, description="Optional patient reference code"),
    doctor_name: Optional[str] = Form(None, description="Optional doctor name"),
    prescription_date: Optional[str] = Form(None, description="Optional prescription date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    rx_id = prescription_id or f"RX-{uuid.uuid4().hex[:8].upper()}"

    # Check for duplicates
    existing = db.query(Prescription).filter(Prescription.prescription_id == rx_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Prescription with ID '{rx_id}' already exists.",
        )

    # Save uploaded file
    file_ext = os.path.splitext(file.filename or "")[1] or ".png"
    safe_filename = f"{rx_id}{file_ext}"
    saved_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    file_bytes = await file.read()
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # Execute OCR and entity extraction
    extracted_text = ""
    ocr_metadata_json = None
    extracted_status = "PROCESSED"

    try:
        extracted_rx = extraction_service.extract_from_image(saved_path)
        extracted_text = extracted_rx.raw_ocr_text
        ocr_metadata_json = json.dumps(extracted_rx.to_dict())
    except Exception as e:
        # Fallback if tesseract binary is not on host: record file and mark for review
        extracted_text = ""
        ocr_metadata_json = json.dumps({"error": str(e), "message": "OCR engine execution deferred or requires manual review"})
        extracted_status = "REVIEW_REQUIRED"

    parsed_date = None
    if prescription_date:
        try:
            parsed_date = datetime.strptime(prescription_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    prescription = Prescription(
        prescription_id=rx_id,
        patient_reference=patient_reference,
        doctor_name=doctor_name,
        prescription_date=parsed_date,
        image_path=saved_path,
        extracted_text=extracted_text,
        ocr_metadata=ocr_metadata_json,
        status=extracted_status,
        created_at=datetime.utcnow(),
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    return _format_prescription_response(prescription)


@router.get(
    "",
    response_model=List[PrescriptionResponse],
    summary="List prescriptions",
    description="Retrieve prescriptions with optional status filtering and pagination.",
)
def list_prescriptions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: PENDING, PROCESSED, REVIEW_REQUIRED"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Prescription)
    if status_filter:
        query = query.filter(Prescription.status == status_filter.upper())
    prescriptions = query.order_by(Prescription.created_at.desc()).offset(skip).limit(limit).all()
    return [_format_prescription_response(rx) for rx in prescriptions]


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionResponse,
    summary="Get prescription by ID",
    description="Retrieve a single prescription record including structured extracted medicines.",
)
def get_prescription(prescription_id: str, db: Session = Depends(get_db)):
    prescription = db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription '{prescription_id}' not found.",
        )
    return _format_prescription_response(prescription)


@router.patch(
    "/{prescription_id}/status",
    response_model=PrescriptionResponse,
    summary="Update prescription status",
    description="Update the workflow status of a prescription (PENDING, PROCESSED, REVIEW_REQUIRED).",
)
def update_prescription_status(
    prescription_id: str,
    payload: PrescriptionUpdateStatus,
    db: Session = Depends(get_db),
):
    prescription = db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription '{prescription_id}' not found.",
        )
    prescription.status = payload.status
    db.commit()
    db.refresh(prescription)
    return _format_prescription_response(prescription)


@router.patch(
    "/{prescription_id}/ocr-result",
    response_model=PrescriptionResponse,
    summary="Update prescription OCR text",
    description="Update or manually correct OCR text and re-extract structured medicine entities.",
)
def update_prescription_ocr(
    prescription_id: str,
    payload: PrescriptionUpdateOCR,
    db: Session = Depends(get_db),
):
    prescription = db.query(Prescription).filter(Prescription.prescription_id == prescription_id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription '{prescription_id}' not found.",
        )
    
    prescription.extracted_text = payload.extracted_text
    if payload.ocr_metadata:
        prescription.ocr_metadata = json.dumps(payload.ocr_metadata)
    
    prescription.status = "PROCESSED"
    db.commit()
    db.refresh(prescription)
    return _format_prescription_response(prescription)
