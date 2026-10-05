from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database import get_db
from backend.schemas import HealthResponse

router = APIRouter(tags=["System & Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System health check",
    description="Returns backend service operational status and database connectivity.",
)
def health_check(db: Session = Depends(get_db)):
    db_connected = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        service="Pharmacy Compliance Monitoring System",
        version="1.0.0",
        database_connected=db_connected,
    )
