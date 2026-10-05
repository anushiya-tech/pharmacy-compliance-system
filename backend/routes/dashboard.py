from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import Transaction, Medicine, Prescription
from backend.schemas import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Dashboard aggregate metrics",
    description="Compute live aggregate statistics from the database for transactions, inventory, compliance status, and revenue.",
)
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_tx = db.query(func.count(Transaction.transaction_id)).scalar() or 0
    total_meds = db.query(func.count(Medicine.medicine_id)).scalar() or 0
    total_rx = db.query(func.count(Prescription.prescription_id)).scalar() or 0
    
    pending_review = db.query(func.count(Transaction.transaction_id)).filter(Transaction.status == "PENDING_REVIEW").scalar() or 0
    flagged = db.query(func.count(Transaction.transaction_id)).filter(Transaction.status == "FLAGGED").scalar() or 0
    cleared = db.query(func.count(Transaction.transaction_id)).filter(Transaction.status == "CLEARED").scalar() or 0
    
    total_sales_val = db.query(func.sum(Transaction.total_amount)).scalar()
    total_sales = float(total_sales_val) if total_sales_val is not None else 0.0

    return DashboardSummaryResponse(
        total_transactions=total_tx,
        total_medicines=total_meds,
        total_prescriptions=total_rx,
        pending_review=pending_review,
        flagged_transactions=flagged,
        cleared_transactions=cleared,
        total_sales=round(total_sales, 2),
    )
