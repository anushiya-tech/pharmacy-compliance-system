"""
Database seeder for Pharmacy Compliance System.
Ensures repeatable, idempotent population of catalog and test fixtures without duplicates.
"""

from datetime import date, datetime
from sqlalchemy.orm import Session

from backend.models import Medicine, Prescription, Transaction, TransactionItem


def seed_database(db: Session) -> None:
    """
    Seed initial catalog data and reference test fixtures idempotently.
    """
    sample_medicines = [
        Medicine(
            medicine_id="M001",
            name="Amoxicillin",
            generic_name="amoxicillin",
            strength="500 mg",
            dosage_form="capsule",
            manufacturer="GSK Pharmaceuticals",
            batch_number="AMX-2026-01",
            stock_quantity=100,
            unit_price=5.00,
            expiry_date=date(2027, 12, 31),
        ),
        Medicine(
            medicine_id="M002",
            name="Paracetamol",
            generic_name="paracetamol",
            strength="650 mg",
            dosage_form="tablet",
            manufacturer="Cipla Ltd",
            batch_number="PCM-2026-09",
            stock_quantity=150,
            unit_price=3.00,
            expiry_date=date(2028, 6, 30),
        ),
        Medicine(
            medicine_id="M003",
            name="Cetirizine",
            generic_name="cetirizine",
            strength="10 mg",
            dosage_form="tablet",
            manufacturer="Sun Pharma",
            batch_number="CTZ-2026-03",
            stock_quantity=80,
            unit_price=4.00,
            expiry_date=date(2027, 8, 15),
        ),
        Medicine(
            medicine_id="M004",
            name="Metformin",
            generic_name="metformin",
            strength="500 mg",
            dosage_form="tablet",
            manufacturer="USV Ltd",
            batch_number="MTF-2026-11",
            stock_quantity=120,
            unit_price=2.50,
            expiry_date=date(2027, 10, 20),
        ),
        Medicine(
            medicine_id="M005",
            name="Diazepam",
            generic_name="diazepam",
            strength="5 mg",
            dosage_form="tablet",
            manufacturer="Roche",
            batch_number="DZP-2026-05",
            stock_quantity=50,
            unit_price=8.00,
            expiry_date=date(2027, 11, 30),
        ),
        Medicine(
            medicine_id="M006",
            name="Pregabalin",
            generic_name="pregabalin",
            strength="75 mg",
            dosage_form="capsule",
            manufacturer="Pfizer",
            batch_number="PGB-2026-08",
            stock_quantity=60,
            unit_price=12.00,
            expiry_date=date(2027, 5, 15),
        ),
    ]

    for med in sample_medicines:
        existing = db.query(Medicine).filter(Medicine.medicine_id == med.medicine_id).first()
        if not existing:
            db.add(med)

    db.commit()

    # Seed initial demo prescription if not exists
    demo_rx_id = "RX-DEMO-001"
    existing_rx = db.query(Prescription).filter(Prescription.prescription_id == demo_rx_id).first()
    if not existing_rx:
        demo_rx = Prescription(
            prescription_id=demo_rx_id,
            patient_reference="PAT-7701",
            doctor_name="Dr. Sarah Jenkins, MD",
            prescription_date=date(2026, 10, 1),
            extracted_text="Rx:\nAmoxicillin 500mg capsule # 10\nCetirizine 10mg tablet # 10",
            status="PROCESSED",
            created_at=datetime.utcnow(),
        )
        db.add(demo_rx)
        db.commit()

    # Seed initial demo transaction if not exists
    demo_tx_id = "TXN-DEMO-001"
    existing_tx = db.query(Transaction).filter(Transaction.transaction_id == demo_tx_id).first()
    if not existing_tx:
        demo_tx = Transaction(
            transaction_id=demo_tx_id,
            timestamp=datetime.utcnow(),
            pharmacist_id="PHARM-01",
            prescription_id=demo_rx_id,
            total_amount=90.00,
            status="RECORDED",
            created_at=datetime.utcnow(),
        )
        db.add(demo_tx)
        db.flush()

        item1 = TransactionItem(
            transaction_id=demo_tx_id,
            medicine_id="M001",
            medicine_name="Amoxicillin",
            strength="500 mg",
            quantity=10,
            unit_price=5.00,
            subtotal=50.00,
        )
        item2 = TransactionItem(
            transaction_id=demo_tx_id,
            medicine_id="M003",
            medicine_name="Cetirizine",
            strength="10 mg",
            quantity=10,
            unit_price=4.00,
            subtotal=40.00,
        )
        db.add(item1)
        db.add(item2)
        db.commit()
