# Pharmacy Compliance Monitoring System

A centralized pharmacy transaction monitoring, prescription compliance, and audit system integrating OCR prescription extraction, atomic sales inventory management, real-time compliance rule verification, and CCTV evidence linking.

---

## 🏗️ System Architecture & Team Roles

```
                              ┌──────────────────────────────────────────────┐
                              │  Member 4: Frontend & Dashboard (Next/Vite)  │
                              └──────────────────────┬───────────────────────┘
                                                     │ HTTP / REST
                                                     ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           MEMBER 1: CORE BACKEND & DATABASE (FastAPI)                          │
│                                                                                                │
│   ┌────────────────────────┐  ┌─────────────────────────┐  ┌───────────────────────────────┐   │
│   │   Medicine Catalog     │  │   Prescription Mgmt     │  │   Atomic Transactions & POS   │   │
│   │   & Inventory Engine   │  │   & Image Storage       │  │   & Historical Snapshots      │   │
│   └───────────┬────────────┘  └───────────┬─────────────┘  └───────────────┬───────────────┘   │
│               │                           │                                │                   │
│               └───────────────────────────┼────────────────────────────────┘                   │
│                                           │                                                    │
│                                           ▼                                                    │
│                             ┌───────────────────────────┐                                      │
│                             │   Compliance Adapter      │                                      │
│                             └─────────────┬─────────────┘                                      │
└───────────────────────────────────────────┼────────────────────────────────────────────────────┘
                                            │ Python Calls
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │    MEMBER 2: OCR, EXTRACTION & MATCHING       │
                    │                                               │
                    │  • Tesseract OCR Engine                       │
                    │  • Clinical Entity Extractor & Normalizer     │
                    │  • Prescription-Sale Matcher                  │
                    │  • Regulatory & Clinical Validation Engine    │
                    └───────────────────────────────────────────────┘
                                            ▲
                                            │ Future Integration
                    ┌───────────────────────┴───────────────────────┐
                    │     MEMBER 3: CCTV, EVIDENCE & AUDIT          │
                    │                                               │
                    │  • Transaction Time-stamped Video Indexing    │
                    │  • Camera Feed Operator Verification          │
                    └───────────────────────────────────────────────┘
```

---

## 🚀 Technology Stack

- **Language & Runtime**: Python 3.10+ / 3.11
- **API Framework**: [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **Data Validation & Schemas**: [Pydantic V2](https://docs.pydantic.dev/) + Pydantic-Settings
- **Database & ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (SQLite for development / PostgreSQL ready)
- **Prescription OCR & Processing**: Tesseract OCR, Pytesseract, Pillow, Regular Expression Normalization
- **Testing**: Pytest & FastAPI TestClient

---

## 📂 Repository Structure

```
pharmacy-compliance-system/
├── backend/                              # [MEMBER 1] Core Backend Module
│   ├── routes/                           # REST API Route Controllers
│   │   ├── __init__.py
│   │   ├── health.py                     # GET /api/health
│   │   ├── medicines.py                  # CRUD & Search for medicines
│   │   ├── prescriptions.py              # Upload, OCR parsing, Rx records
│   │   ├── transactions.py               # Atomic POS sales & compliance check
│   │   └── dashboard.py                  # Live aggregate statistics
│   ├── compliance_adapter.py             # Adapter bridge to Member 2's algorithms
│   ├── config.py                         # Environment settings & CORS config
│   ├── database.py                       # SQLAlchemy engine & session dependency
│   ├── models.py                         # ORM Models (Medicine, Rx, Txn, Items)
│   ├── schemas.py                        # Pydantic request / response schemas
│   ├── seed.py                           # Repeatable idempotent database seeder
│   └── main.py                           # FastAPI application entry & lifespan
├── compliance/                           # [MEMBER 2] Compliance & Matching
│   ├── matching/                         # Prescription-sale matching engine
│   └── validation/                       # Regulatory & clinical rules
├── prescription_processing/              # [MEMBER 2] OCR & Normalization
│   ├── ocr/                              # Tesseract & Mock OCR engines
│   ├── extraction/                       # Entity regex extraction
│   └── normalization/                    # Medicine name & unit normalizers
├── docs/                                 # Documentation & Architecture
│   ├── api_contract.md                   # Full REST API Contract specification
│   └── README.md
├── tests/                                # Automated Test Suites
│   ├── test_backend.py                   # Member 1 backend & API test suite
│   ├── test_compliance_integration.py    # Compliance pipeline tests
│   ├── test_extraction.py                # Prescription OCR extraction tests
│   ├── test_matching.py                  # Prescription-sale matcher tests
│   └── test_validation.py                # Regulatory validation tests
├── requirements.txt                      # Project-wide Python dependencies
├── run.py                                # Backend startup script
├── .env.example                          # Environment variable configuration template
└── README.md                             # Project overview & guide
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10+
- (Optional for live OCR) Tesseract-OCR installed on system ([Windows installer](https://github.com/UB-Mannheim/tesseract/wiki))

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

---

## 🏃 Running the Backend

### Start Server
```bash
python run.py
```
Or directly with Uvicorn:
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The server automatically initializes the database tables and runs idempotent seeding on startup.

### Interactive API Documentation
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 🧪 Running Automated Tests

Run the full test suite (including Member 1 backend tests and Member 2 OCR/matching tests):
```bash
pytest
```

All 43 tests run against isolated in-memory test databases without affecting runtime data.

---

## 🔗 Team Integration Guidelines

### Member 2 (Prescription OCR & Compliance)
- Member 2's OCR, entity extraction, normalizer, and matching engines are preserved and directly invoked through `backend/compliance_adapter.py`.
- To update OCR rules or matching heuristics, edit files in `prescription_processing/` or `compliance/`. The backend will automatically use the updated logic.

### Member 3 (CCTV & Evidence)
- Every transaction record generated via `POST /api/transactions` contains audit-ready metadata:
  - `transaction_id`: Unique identifier (e.g. `TXN-20261005-XXXX`)
  - `timestamp`: UTC ISO timestamp
  - `pharmacist_id`: Operator ID
  - `prescription_id`: Associated prescription
  - `status`: `RECORDED`, `PENDING_REVIEW`, `FLAGGED`, `CLEARED`
- Member 3 can link video files, frame indexes, or camera audit logs to transactions by querying `GET /api/transactions/{transaction_id}`.

### Member 4 (Frontend & Dashboard)
- Connect any web client (React, Vue, Next.js, Vite).
- CORS is configured to accept requests from `http://localhost:3000` and `http://localhost:5173`.
- Key endpoints for the frontend:
  - Live statistics: `GET /api/dashboard/summary`
  - POS Checkout: `POST /api/transactions`
  - Inventory search: `GET /api/medicines/search?name=...`
  - Prescription upload: `POST /api/prescriptions/upload`
  - Compliance audit view: `GET /api/transactions/{transaction_id}/compliance`

---

## 🌿 Git Workflow

1. Always branch off from the team's latest work.
2. Develop features on designated feature branches (`feature/backend`, `feature/cctv`, `feature/frontend`).
3. Run `pytest` before committing to ensure zero regression.
4. Submit pull requests to the development or main branch.
