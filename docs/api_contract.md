# Pharmacy Compliance Monitoring System - API Contract & Integration Guide

This document defines the REST API contract for the **Pharmacy Compliance Monitoring System**, serving as the central integration standard for all team members (Member 1: Core Backend, Member 2: OCR/Compliance, Member 3: CCTV/Evidence, Member 4: Frontend Dashboard).

---

## 1. System Architecture & Component Roles

- **Member 1 (Core Backend & Database)**: Central REST API, relational SQLite/PostgreSQL database (SQLAlchemy), transaction integrity, stock validation, and compliance orchestration.
- **Member 2 (OCR & Matching)**: OCR extraction engine (`prescription_processing/ocr`), entity normalization (`prescription_processing/normalization`), sale matching (`compliance/matching`), and regulatory rules (`compliance/validation`).
- **Member 3 (CCTV & Evidence)**: Links physical audit events to `transaction_id`, `pharmacist_id`, and `timestamp`.
- **Member 4 (Frontend & UI)**: React / Next.js / Vite web application consuming REST endpoints and WebSocket/event feeds.

---

## 2. Server Base URLs & Interactive Documentation

- **Base URL**: `http://127.0.0.1:8000/api`
- **Swagger Interactive UI**: `http://127.0.0.1:8000/docs`
- **ReDoc Interactive UI**: `http://127.0.0.1:8000/redoc`
- **Health Endpoint**: `http://127.0.0.1:8000/api/health`

---

## 3. API Endpoints Specification

### 3.1 Health & System

#### `GET /api/health`
Checks backend and database connectivity.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "Pharmacy Compliance Monitoring System",
  "version": "1.0.0",
  "database_connected": true
}
```

---

### 3.2 Medicines & Inventory Management

#### `POST /api/medicines`
Add a new medicine to catalog and inventory.
- **Status Code**: `201 Created` / `409 Conflict` (if duplicate ID)
- **Request Body**:
```json
{
  "medicine_id": "M001",
  "name": "Amoxicillin",
  "generic_name": "amoxicillin",
  "strength": "500 mg",
  "dosage_form": "capsule",
  "manufacturer": "GSK Pharmaceuticals",
  "batch_number": "AMX-2026-01",
  "stock_quantity": 100,
  "unit_price": 5.00,
  "expiry_date": "2027-12-31"
}
```
- **Validation**:
  - `name`: Required, non-empty string.
  - `strength`: Required, non-empty string.
  - `stock_quantity`: Integer $\ge 0$.
  - `unit_price`: Float $\ge 0.0$.
  - `medicine_id`: Unique identifier.

#### `GET /api/medicines`
List medicines with optional pagination.
- **Query Parameters**:
  - `skip` (default `0`): Offset.
  - `limit` (default `100`, max `500`): Page size.
- **Response `200 OK`**: Array of medicine objects.

#### `GET /api/medicines/search`
Search catalog by name or generic name (case-insensitive substring).
- **Query Parameters**:
  - `name`: Search query string (e.g. `?name=amox`).
- **Response `200 OK`**: Matching medicine objects.

#### `GET /api/medicines/{medicine_id}`
Retrieve a single medicine by its unique ID.
- **Status Code**: `200 OK` / `404 Not Found`.

#### `PUT /api/medicines/{medicine_id}`
Update medicine fields (stock, price, metadata).
- **Status Code**: `200 OK` / `404 Not Found`.

#### `DELETE /api/medicines/{medicine_id}`
Delete a medicine from catalog.
- **Status Code**: `200 OK` / `404 Not Found`.

---

### 3.3 Prescriptions & OCR Processing

#### `POST /api/prescriptions`
Create a prescription record directly with optional structured or OCR text.
- **Status Code**: `201 Created` / `409 Conflict`.
- **Request Body**:
```json
{
  "prescription_id": "RX001",
  "patient_reference": "PAT-7701",
  "doctor_name": "Dr. Sarah Jenkins, MD",
  "prescription_date": "2026-10-01",
  "extracted_text": "Amoxicillin 500mg capsule # 10\nCetirizine 10mg tablet # 10"
}
```

#### `POST /api/prescriptions/upload`
Upload a prescription image file (`.png`, `.jpg`, `.jpeg`).
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Image binary.
  - `prescription_id` (optional): Custom ID (auto-generated if omitted).
  - `patient_reference` (optional).
  - `doctor_name` (optional).
  - `prescription_date` (optional, `YYYY-MM-DD`).
- **Workflow**:
  1. Stores image to server uploads storage.
  2. Runs Member 2 OCR Engine (`PrescriptionOCRService`).
  3. Executes Entity Extractor & Normalizer (`PrescriptionEntityExtractor`).
  4. Stores record in database and returns structured extracted medicines.

#### `GET /api/prescriptions`
List all prescriptions.
- **Query Parameters**:
  - `status` (`PENDING`, `PROCESSED`, `REVIEW_REQUIRED`).
  - `skip`, `limit`.

#### `GET /api/prescriptions/{prescription_id}`
Retrieve single prescription with parsed extracted medicine entities.
- **Response `200 OK`**:
```json
{
  "prescription_id": "RX001",
  "patient_reference": "PAT-7701",
  "doctor_name": "Dr. Sarah Jenkins, MD",
  "prescription_date": "2026-10-01",
  "image_path": null,
  "extracted_text": "Amoxicillin 500mg capsule # 10\nCetirizine 10mg tablet # 10",
  "status": "PROCESSED",
  "created_at": "2026-10-05T14:30:00Z",
  "extracted_medicines": [
    {
      "medicine_name": "Amoxicillin",
      "normalized_name": "amoxicillin",
      "strength_value": 500.0,
      "strength_unit": "mg",
      "dosage_form": "capsule",
      "quantity": 10,
      "frequency": null,
      "confidence": 1.0,
      "extraction_status": "complete"
    }
  ]
}
```

#### `PATCH /api/prescriptions/{prescription_id}/status`
Update prescription status (`PENDING`, `PROCESSED`, `REVIEW_REQUIRED`).

#### `PATCH /api/prescriptions/{prescription_id}/ocr-result`
Manually correct OCR text and re-extract medicine entities.

---

### 3.4 Transactions & Compliance

#### `POST /api/transactions`
Process a retail sale transaction atomically.
- **Status Code**: `201 Created` / `400 Bad Request` / `404 Not Found`.
- **Request Body**:
```json
{
  "pharmacist_id": "PHARM-01",
  "prescription_id": "RX001",
  "items": [
    {
      "medicine_id": "M001",
      "quantity": 10
    },
    {
      "medicine_id": "M003",
      "quantity": 10
    }
  ]
}
```
- **Backend Atomic Workflow**:
  1. Validates pharmacist ID and prescription existence (if provided).
  2. Queries all medicines from the database.
  3. Verifies stock availability (`stock_quantity >= item.quantity`).
  4. Reads price directly from database (`medicine.unit_price`). **Frontend-submitted prices are never trusted.**
  5. Deducts inventory stock atomically.
  6. Snapshots `medicine_name`, `strength`, and `unit_price` on `TransactionItem` to preserve historical integrity.
  7. If prescription is attached, runs compliance analysis and automatically updates transaction status to `RECORDED`, `PENDING_REVIEW`, or `FLAGGED`.
  8. **Atomic Rollback**: If any stock or medicine check fails, the entire transaction rolls back with 0 changes committed.

#### `GET /api/transactions`
List transactions.
- **Query Parameters**: `status`, `pharmacist_id`, `prescription_id`, `skip`, `limit`.

#### `GET /api/transactions/{transaction_id}`
Retrieve a transaction with its snapshot items.

#### `PATCH /api/transactions/{transaction_id}/status`
Update transaction status (`RECORDED`, `PENDING_REVIEW`, `FLAGGED`, `CLEARED`).

#### `GET /api/transactions/{transaction_id}/items`
Retrieve line items for a specific transaction.

#### `GET /api/transactions/{transaction_id}/compliance`
**Integrated Compliance Engine Endpoint**:
Retrieves transaction and linked prescription, passes them to Member 2's `MatchingService` and `ComplianceValidationService`, and returns structured audit results.
- **Response `200 OK`**:
```json
{
  "transaction_id": "TXN-20261005-A1B2C3",
  "prescription_id": "RX001",
  "is_compliant": false,
  "status": "REVIEW_REQUIRED",
  "matched_items": [
    {
      "medicine": "Amoxicillin",
      "strength": "500 mg",
      "prescribed_quantity": 10,
      "sold_quantity": 10,
      "status": "COVERED",
      "reason": "Medicine and available quantity matched."
    }
  ],
  "missing_items": [],
  "quantity_mismatches": [],
  "uncovered_items": [
    {
      "medicine": "Pregabalin",
      "strength": "75 mg",
      "quantity": 10,
      "status": "NOT_COVERED",
      "reason": "Medicine sold without matching prescription coverage."
    }
  ],
  "validation_issues": [
    {
      "medicine_name": "Diazepam",
      "rule": "restricted_medicine",
      "status": "WARNING",
      "message": "Medicine requires restricted-drug handling verification"
    }
  ],
  "summary": "1 item(s) sold without prescription coverage."
}
```

---

### 3.5 Dashboard Summary

#### `GET /api/dashboard/summary`
Live aggregated system metrics computed directly from database tables.
- **Response `200 OK`**:
```json
{
  "total_transactions": 142,
  "total_medicines": 6,
  "total_prescriptions": 85,
  "pending_review": 12,
  "flagged_transactions": 3,
  "cleared_transactions": 127,
  "total_sales": 14520.50
}
```

---

## 4. Guide for Team Members

### How Member 2 (OCR / Compliance) Integrates
- Member 2's components in `prescription_processing/` and `compliance/` are directly imported by `backend/compliance_adapter.py` and `backend/routes/prescriptions.py`.
- No duplicated algorithms: database records are mapped cleanly to Member 2's `ExtractedMedicineItem` and `SaleItem` dataclasses.

### How Member 3 (CCTV / Evidence / Audit) Integrates
- Every sale transaction exposes standard audit keys:
  - `transaction_id` (Unique string identifier)
  - `timestamp` (UTC datetime ISO format)
  - `pharmacist_id` (Operator identity)
  - `prescription_id` (Linked Rx)
  - `status` (`RECORDED`, `PENDING_REVIEW`, `FLAGGED`, `CLEARED`)
- Member 3 can build audit logging, video timestamp indexing, and CCTV clip association by keying directly on `transaction_id` and `timestamp`.

### How Member 4 (Frontend / Dashboard) Integrates
- All endpoints return standard JSON with Pydantic validation.
- CORS is enabled for frontend origins (`http://localhost:3000`, `http://localhost:5173`).
- Frontend dashboard metrics: use `GET /api/dashboard/summary`.
- Point of sale terminal: use `POST /api/transactions`.
- Rx Image upload: use `POST /api/prescriptions/upload`.
- Audit / Compliance review modal: use `GET /api/transactions/{id}/compliance`.
