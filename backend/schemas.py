from datetime import date, datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ==============================================================================
# Base / Generic Schemas
# ==============================================================================

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "Pharmacy Compliance Monitoring System"
    version: str = "1.0.0"
    database_connected: bool = True


# ==============================================================================
# Medicine Schemas
# ==============================================================================

class MedicineBase(BaseModel):
    name: str = Field(..., min_length=1, description="Brand or trade name of the medicine", examples=["Amoxicillin"])
    generic_name: Optional[str] = Field(None, description="Active pharmaceutical ingredient / generic name", examples=["amoxicillin"])
    strength: str = Field(..., min_length=1, description="Strength dosage indicator", examples=["500 mg"])
    dosage_form: Optional[str] = Field(None, description="Dosage form such as tablet, capsule, syrup", examples=["capsule"])
    manufacturer: Optional[str] = Field(None, description="Manufacturer or pharma company", examples=["GSK"])
    batch_number: Optional[str] = Field(None, description="Batch / lot number", examples=["B-2026-X1"])
    stock_quantity: int = Field(0, ge=0, description="Available stock quantity (must be >= 0)", examples=[100])
    unit_price: float = Field(0.0, ge=0.0, description="Price per individual unit/dispense (must be >= 0)", examples=[5.00])
    expiry_date: Optional[date] = Field(None, description="Expiry date of the batch", examples=["2027-12-31"])


class MedicineCreate(MedicineBase):
    medicine_id: str = Field(..., min_length=1, description="Unique identifier for the medicine", examples=["M001"])


class MedicineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    generic_name: Optional[str] = None
    strength: Optional[str] = Field(None, min_length=1)
    dosage_form: Optional[str] = None
    manufacturer: Optional[str] = None
    batch_number: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, ge=0.0)
    expiry_date: Optional[date] = None


class MedicineResponse(MedicineBase):
    medicine_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Prescription Schemas
# ==============================================================================

class PrescriptionBase(BaseModel):
    patient_reference: Optional[str] = Field(None, description="Anonymized patient reference or ID", examples=["PAT-9842"])
    doctor_name: Optional[str] = Field(None, description="Prescribing physician name", examples=["Dr. Sarah Jenkins"])
    prescription_date: Optional[date] = Field(None, description="Date of the prescription", examples=["2026-10-01"])
    image_path: Optional[str] = Field(None, description="Server storage path or filename for prescription image")
    extracted_text: Optional[str] = Field(None, description="Raw or cleaned OCR text from prescription")


class PrescriptionCreate(PrescriptionBase):
    prescription_id: Optional[str] = Field(None, description="Unique ID for prescription (auto-generated if omitted)", examples=["RX001"])


class PrescriptionUpdateStatus(BaseModel):
    status: str = Field(..., description="Prescription status: PENDING, PROCESSED, REVIEW_REQUIRED", examples=["PROCESSED"])

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"PENDING", "PROCESSED", "REVIEW_REQUIRED"}
        v_upper = v.upper()
        if v_upper not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v_upper


class PrescriptionUpdateOCR(BaseModel):
    extracted_text: str = Field(..., min_length=1, description="Updated OCR text")
    ocr_metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata dictionary")


class ExtractedMedicineItemSchema(BaseModel):
    medicine_name: str
    normalized_name: str
    strength_value: Optional[float] = None
    strength_unit: Optional[str] = None
    dosage_form: Optional[str] = None
    quantity: Optional[int] = None
    frequency: Optional[str] = None
    confidence: float = 1.0
    extraction_status: str = "success"


class PrescriptionResponse(PrescriptionBase):
    prescription_id: str
    status: str
    ocr_metadata: Optional[str] = None
    extracted_medicines: Optional[List[ExtractedMedicineItemSchema]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Transaction & TransactionItem Schemas
# ==============================================================================

class TransactionItemCreate(BaseModel):
    medicine_id: str = Field(..., min_length=1, description="ID of the medicine being sold", examples=["M001"])
    quantity: int = Field(..., gt=0, description="Quantity being sold (must be > 0)", examples=[10])


class TransactionCreate(BaseModel):
    pharmacist_id: str = Field(..., min_length=1, description="ID or license number of the pharmacist", examples=["P001"])
    prescription_id: Optional[str] = Field(None, description="Associated prescription ID if applicable", examples=["RX001"])
    items: List[TransactionItemCreate] = Field(..., min_length=1, description="List of medicine items in the sale")


class TransactionItemResponse(BaseModel):
    item_id: int
    transaction_id: str
    medicine_id: str
    medicine_name: str
    strength: str
    quantity: int
    unit_price: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    transaction_id: str
    timestamp: datetime
    pharmacist_id: str
    prescription_id: Optional[str] = None
    total_amount: float
    status: str
    created_at: datetime
    items: List[TransactionItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TransactionStatusUpdate(BaseModel):
    status: str = Field(..., description="Transaction status: RECORDED, PENDING_REVIEW, FLAGGED, CLEARED", examples=["CLEARED"])

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"RECORDED", "PENDING_REVIEW", "FLAGGED", "CLEARED"}
        v_upper = v.upper()
        if v_upper not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v_upper


# ==============================================================================
# Compliance & Matching Schemas
# ==============================================================================

class MatchedItemResponse(BaseModel):
    medicine: str
    strength: Optional[str] = None
    prescribed_quantity: Optional[int] = None
    sold_quantity: Optional[int] = None
    status: str = "COVERED"
    reason: str


class MissingItemResponse(BaseModel):
    medicine: str
    prescribed_quantity: Optional[int] = None
    status: str = "MISSING"
    reason: str


class QuantityMismatchResponse(BaseModel):
    medicine: str
    prescribed_quantity: Optional[int] = None
    sold_quantity: Optional[int] = None
    quantity_difference: Optional[int] = None
    status: str = "QUANTITY_MISMATCH"
    reason: str


class ExtraItemResponse(BaseModel):
    medicine: str
    strength: Optional[str] = None
    quantity: Optional[int] = None
    status: str = "NOT_COVERED"
    reason: str = "Item sold without matching prescription coverage."


class ValidationIssueResponse(BaseModel):
    medicine_name: str
    rule: str
    status: str
    message: str


class ComplianceCheckResponse(BaseModel):
    transaction_id: str
    prescription_id: Optional[str] = None
    is_compliant: bool
    status: str = Field(..., description="Overall compliance status: COMPLIANT, REVIEW_REQUIRED, FLAGGED")
    matched_items: List[MatchedItemResponse] = []
    missing_items: List[MissingItemResponse] = []
    quantity_mismatches: List[QuantityMismatchResponse] = []
    uncovered_items: List[ExtraItemResponse] = []
    validation_issues: List[ValidationIssueResponse] = []
    summary: str


# ==============================================================================
# Dashboard Summary Schema
# ==============================================================================

class DashboardSummaryResponse(BaseModel):
    total_transactions: int
    total_medicines: int
    total_prescriptions: int
    pending_review: int
    flagged_transactions: int
    cleared_transactions: int
    total_sales: float
