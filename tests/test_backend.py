import os
import unittest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.seed import seed_database
from backend.models import Medicine, Prescription, Transaction, TransactionItem

# In-memory test database
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestBackendModule(unittest.TestCase):

    def setUp(self):
        # Re-create fresh database schema for every test
        Base.metadata.create_all(bind=test_engine)
        self.db = TestingSessionLocal()
        seed_database(self.db)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=test_engine)

    # -------------------------------------------------------------------------
    # Health & System
    # -------------------------------------------------------------------------
    def test_health_endpoint(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["database_connected"])

    def test_root_endpoint(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("docs", data)

    # -------------------------------------------------------------------------
    # Medicine Catalog & Inventory
    # -------------------------------------------------------------------------
    def test_create_and_get_medicine(self):
        new_med = {
            "medicine_id": "M-TEST-1",
            "name": "Ibuprofen",
            "generic_name": "ibuprofen",
            "strength": "400 mg",
            "dosage_form": "tablet",
            "manufacturer": "Advil Corp",
            "batch_number": "IBU-99",
            "stock_quantity": 50,
            "unit_price": 6.50,
            "expiry_date": "2027-01-01",
        }
        res = client.post("/api/medicines", json=new_med)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["medicine_id"], "M-TEST-1")
        self.assertEqual(data["unit_price"], 6.50)

        # Get by ID
        get_res = client.get("/api/medicines/M-TEST-1")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["name"], "Ibuprofen")

    def test_duplicate_medicine_id_rejected(self):
        dup_med = {
            "medicine_id": "M001",  # Already in seed
            "name": "Amoxicillin Duplicate",
            "strength": "500 mg",
            "stock_quantity": 10,
            "unit_price": 5.0,
        }
        res = client.post("/api/medicines", json=dup_med)
        self.assertEqual(res.status_code, 409)

    def test_medicine_search(self):
        res = client.get("/api/medicines/search?name=amox")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["medicine_id"], "M001")

    def test_medicine_update(self):
        update_payload = {"stock_quantity": 200, "unit_price": 5.50}
        res = client.put("/api/medicines/M001", json=update_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["stock_quantity"], 200)
        self.assertEqual(data["unit_price"], 5.50)

    def test_medicine_delete(self):
        # Create temporary medicine
        temp_med = {
            "medicine_id": "M-TEMP",
            "name": "Temp Medicine",
            "strength": "100 mg",
            "stock_quantity": 5,
            "unit_price": 1.0,
        }
        client.post("/api/medicines", json=temp_med)
        
        del_res = client.delete("/api/medicines/M-TEMP")
        self.assertEqual(del_res.status_code, 200)

        get_res = client.get("/api/medicines/M-TEMP")
        self.assertEqual(get_res.status_code, 404)

    # -------------------------------------------------------------------------
    # Prescription Management
    # -------------------------------------------------------------------------
    def test_create_and_update_prescription(self):
        rx_payload = {
            "prescription_id": "RX-TEST-100",
            "patient_reference": "PAT-999",
            "doctor_name": "Dr. House",
            "prescription_date": "2026-10-02",
            "extracted_text": "Amoxicillin 500mg # 20",
        }
        res = client.post("/api/prescriptions", json=rx_payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["prescription_id"], "RX-TEST-100")
        self.assertEqual(data["status"], "PROCESSED")
        self.assertIsNotNone(data["extracted_medicines"])
        self.assertEqual(len(data["extracted_medicines"]), 1)
        self.assertEqual(data["extracted_medicines"][0]["normalized_name"], "amoxicillin")

        # Update status
        patch_res = client.patch(
            "/api/prescriptions/RX-TEST-100/status",
            json={"status": "REVIEW_REQUIRED"},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["status"], "REVIEW_REQUIRED")

    # -------------------------------------------------------------------------
    # Transactions & Stock Operations
    # -------------------------------------------------------------------------
    def test_create_transaction_success(self):
        # Check initial stock of M001 (100) and M002 (150)
        tx_payload = {
            "pharmacist_id": "PHARM-99",
            "prescription_id": "RX-DEMO-001",
            "items": [
                {"medicine_id": "M001", "quantity": 10},
                {"medicine_id": "M002", "quantity": 5},
            ],
        }
        res = client.post("/api/transactions", json=tx_payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("TXN-", data["transaction_id"])
        # Total amount: (10 * 5.00) + (5 * 3.00) = 50.00 + 15.00 = 65.00
        self.assertEqual(data["total_amount"], 65.00)
        self.assertEqual(len(data["items"]), 2)

        # Check stock deduction
        med1 = client.get("/api/medicines/M001").json()
        med2 = client.get("/api/medicines/M002").json()
        self.assertEqual(med1["stock_quantity"], 90)
        self.assertEqual(med2["stock_quantity"], 145)

    def test_transaction_insufficient_stock_rollback(self):
        # M003 has 80 in stock. Requesting 100 should fail and roll back everything
        initial_m1 = client.get("/api/medicines/M001").json()["stock_quantity"]
        initial_m3 = client.get("/api/medicines/M003").json()["stock_quantity"]

        tx_payload = {
            "pharmacist_id": "PHARM-01",
            "items": [
                {"medicine_id": "M001", "quantity": 10},
                {"medicine_id": "M003", "quantity": 100},  # Exceeds stock
            ],
        }
        res = client.post("/api/transactions", json=tx_payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Insufficient stock", res.json()["detail"])

        # Verify full rollback: M001 stock should NOT have been deducted
        after_m1 = client.get("/api/medicines/M001").json()["stock_quantity"]
        after_m3 = client.get("/api/medicines/M003").json()["stock_quantity"]
        self.assertEqual(initial_m1, after_m1)
        self.assertEqual(initial_m3, after_m3)

    def test_transaction_invalid_medicine_rollback(self):
        tx_payload = {
            "pharmacist_id": "PHARM-01",
            "items": [
                {"medicine_id": "NON_EXISTENT_MED", "quantity": 5},
            ],
        }
        res = client.post("/api/transactions", json=tx_payload)
        self.assertEqual(res.status_code, 404)

    def test_transaction_status_update(self):
        patch_res = client.patch(
            "/api/transactions/TXN-DEMO-001/status",
            json={"status": "CLEARED"},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["status"], "CLEARED")

    # -------------------------------------------------------------------------
    # Compliance Analysis Endpoint
    # -------------------------------------------------------------------------
    def test_transaction_compliance_endpoint_covered(self):
        # TXN-DEMO-001 has Amoxicillin (10) and Cetirizine (10) matching RX-DEMO-001
        res = client.get("/api/transactions/TXN-DEMO-001/compliance")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["transaction_id"], "TXN-DEMO-001")
        self.assertTrue(data["is_compliant"])
        self.assertEqual(data["status"], "COMPLIANT")
        self.assertEqual(len(data["matched_items"]), 2)
        self.assertEqual(len(data["uncovered_items"]), 0)

    def test_transaction_compliance_endpoint_uncovered_item(self):
        # Create a sale with an uncovered medicine (Pregabalin) against RX-DEMO-001
        tx_payload = {
            "pharmacist_id": "PHARM-01",
            "prescription_id": "RX-DEMO-001",
            "items": [
                {"medicine_id": "M001", "quantity": 10},
                {"medicine_id": "M006", "quantity": 10},  # Pregabalin (not on prescription)
            ],
        }
        tx_res = client.post("/api/transactions", json=tx_payload)
        self.assertEqual(tx_res.status_code, 201)
        tx_id = tx_res.json()["transaction_id"]

        comp_res = client.get(f"/api/transactions/{tx_id}/compliance")
        self.assertEqual(comp_res.status_code, 200)
        comp_data = comp_res.json()
        self.assertFalse(comp_data["is_compliant"])
        self.assertEqual(comp_data["status"], "REVIEW_REQUIRED")
        self.assertGreaterEqual(len(comp_data["uncovered_items"]), 1)
        self.assertEqual(comp_data["uncovered_items"][0]["medicine"], "Pregabalin")

    # -------------------------------------------------------------------------
    # Dashboard Aggregates
    # -------------------------------------------------------------------------
    def test_dashboard_summary(self):
        res = client.get("/api/dashboard/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total_medicines"], 6)
        self.assertGreaterEqual(data["total_transactions"], 1)
        self.assertGreaterEqual(data["total_prescriptions"], 1)
        self.assertGreaterEqual(data["total_sales"], 90.00)


if __name__ == "__main__":
    unittest.main()
