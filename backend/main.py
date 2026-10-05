import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import Base, engine, SessionLocal
from backend.seed import seed_database
from backend.routes.health import router as health_router
from backend.routes.medicines import router as medicines_router
from backend.routes.prescriptions import router as prescriptions_router
from backend.routes.transactions import router as transactions_router
from backend.routes.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler:
    1. Initialize database schema (create tables if not existing)
    2. Run idempotent database seeder if configured
    3. Ensure upload directories exist
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Ensure uploads directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Seed initial data
    if settings.AUTO_SEED:
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()

    yield


app = FastAPI(
    title="Pharmacy Compliance Monitoring System",
    description=(
        "Core Backend and API Integration layer for the Pharmacy Compliance Monitoring System.\n\n"
        "Integrates inventory management, prescription OCR processing, atomic sales transactions, "
        "and automated prescription compliance checking."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static uploads directory if available
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API Routers under /api
app.include_router(health_router, prefix="/api")
app.include_router(medicines_router, prefix="/api")
app.include_router(prescriptions_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to Pharmacy Compliance Monitoring System API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health",
    }
