import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Transaction, TransactionItem, Medicine, Prescription
from backend.schemas import (
    TransactionCreate,
    TransactionResponse,
    TransactionItemResponse,
    TransactionStatusUpdate,
    ComplianceCheckResponse,
)
from backend.compliance_adapter import compliance_adapter

router = APIRouter(prefix="/transactions", tags=["Transactions & Sales"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create sale transaction",
    description="Atomic transaction creation. Validates stock, reads database prices, snapshots medicine details, deducts inventory, evaluates compliance, and commits atomically.",
)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    # 1. Validate items presence
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction must contain at least one medicine item.",
        )

    # 2. Validate prescription if supplied
    prescription = None
    if payload.prescription_id:
        prescription = db.query(Prescription).filter(Prescription.prescription_id == payload.prescription_id).first()
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Associated prescription '{payload.prescription_id}' not found.",
            )

    # 3. Validate pharmacist ID
    if not payload.pharmacist_id or not payload.pharmacist_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pharmacist ID is required.",
        )

    # 4. Generate unique transaction ID
    date_str = datetime.utcnow().strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    transaction_id = f"TXN-{date_str}-{unique_suffix}"

    # 5. Process and validate all items atomically
    prepared_items: List[TransactionItem] = []
    total_amount = 0.0

    try:
        for item_in in payload.items:
            # Check quantity validation
            if item_in.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity for medicine '{item_in.medicine_id}' must be greater than zero.",
                )

            # Query medicine from DB (with row lock if supported, or standard check)
            medicine = db.query(Medicine).filter(Medicine.medicine_id == item_in.medicine_id).first()
            if not medicine:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Medicine '{item_in.medicine_id}' does not exist in inventory.",
                )

            # Check stock availability
            if medicine.stock_quantity < item_in.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Insufficient stock for medicine '{medicine.name}' ({medicine.medicine_id}). "
                        f"Requested: {item_in.quantity}, Available: {medicine.stock_quantity}."
                    ),
                )

            # Deduct stock
            medicine.stock_quantity -= item_in.quantity

            # Calculate subtotal using database price (Never trust frontend price)
            unit_price = float(medicine.unit_price)
            subtotal = round(item_in.quantity * unit_price, 2)
            total_amount += subtotal

            # Snapshot historical data
            tx_item = TransactionItem(
                transaction_id=transaction_id,
                medicine_id=medicine.medicine_id,
                medicine_name=medicine.name,
                strength=medicine.strength,
                quantity=item_in.quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )
            prepared_items.append(tx_item)

        total_amount = round(total_amount, 2)

        # 6. Create Transaction record
        transaction = Transaction(
            transaction_id=transaction_id,
            timestamp=datetime.utcnow(),
            pharmacist_id=payload.pharmacist_id.strip(),
            prescription_id=payload.prescription_id,
            total_amount=total_amount,
            status="RECORDED",
            created_at=datetime.utcnow(),
        )
        db.add(transaction)
        db.flush()

        for item in prepared_items:
            db.add(item)
        db.flush()

        # 7. Evaluate compliance status if prescription is attached
        if prescription:
            comp_eval = compliance_adapter.evaluate_compliance(transaction, prescription)
            if comp_eval.status == "FLAGGED":
                transaction.status = "FLAGGED"
            elif comp_eval.status == "REVIEW_REQUIRED":
                transaction.status = "PENDING_REVIEW"
            else:
                transaction.status = "RECORDED"

        # Commit all changes atomically
        db.commit()
        db.refresh(transaction)
        return transaction

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction processing failed: {str(e)}",
        )


@router.get(
    "",
    response_model=List[TransactionResponse],
    summary="List transactions",
    description="Retrieve transactions with optional filtering by status, pharmacist, or prescription ID.",
)
def list_transactions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (RECORDED, PENDING_REVIEW, FLAGGED, CLEARED)"),
    pharmacist_id: Optional[str] = Query(None, description="Filter by pharmacist ID"),
    prescription_id: Optional[str] = Query(None, description="Filter by prescription ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)
    if status_filter:
        query = query.filter(Transaction.status == status_filter.upper())
    if pharmacist_id:
        query = query.filter(Transaction.pharmacist_id == pharmacist_id)
    if prescription_id:
        query = query.filter(Transaction.prescription_id == prescription_id)

    transactions = query.order_by(Transaction.timestamp.desc()).offset(skip).limit(limit).all()
    return transactions


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get transaction by ID",
    description="Retrieve a single transaction with all purchased items and snapshot details.",
)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found.",
        )
    return transaction


@router.patch(
    "/{transaction_id}/status",
    response_model=TransactionResponse,
    summary="Update transaction status",
    description="Update transaction status (RECORDED, PENDING_REVIEW, FLAGGED, CLEARED) during review or audit.",
)
def update_transaction_status(
    transaction_id: str,
    payload: TransactionStatusUpdate,
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found.",
        )

    transaction.status = payload.status
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get(
    "/{transaction_id}/items",
    response_model=List[TransactionItemResponse],
    summary="Get transaction items",
    description="Retrieve the line items belonging to a specific transaction.",
)
def get_transaction_items(transaction_id: str, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found.",
        )
    return transaction.items


@router.get(
    "/{transaction_id}/compliance",
    response_model=ComplianceCheckResponse,
    summary="Get transaction compliance analysis",
    description="Run and return the structured compliance report comparing this transaction against its prescription using Member 2's OCR matching and validation engine.",
)
def get_transaction_compliance(transaction_id: str, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found.",
        )

    prescription = None
    if transaction.prescription_id:
        prescription = db.query(Prescription).filter(Prescription.prescription_id == transaction.prescription_id).first()

    report = compliance_adapter.evaluate_compliance(transaction, prescription)
    return report
