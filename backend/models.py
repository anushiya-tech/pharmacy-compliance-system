from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Date,
    DateTime,
    Text,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Medicine(Base):
    """
    Medicine catalog and inventory entity.
    """
    __tablename__ = "medicines"

    medicine_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    generic_name = Column(String(200), nullable=True, index=True)
    strength = Column(String(50), nullable=False)
    dosage_form = Column(String(50), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    batch_number = Column(String(100), nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    unit_price = Column(Float, nullable=False, default=0.0)
    expiry_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("stock_quantity >= 0", name="check_stock_quantity_non_negative"),
        CheckConstraint("unit_price >= 0", name="check_unit_price_non_negative"),
    )

    transaction_items = relationship("TransactionItem", back_populates="medicine")


class Prescription(Base):
    """
    Prescription record entity holding patient/doctor metadata, image paths, and OCR results.
    """
    __tablename__ = "prescriptions"

    prescription_id = Column(String(50), primary_key=True, index=True)
    patient_reference = Column(String(100), nullable=True)
    doctor_name = Column(String(200), nullable=True)
    prescription_date = Column(Date, nullable=True)
    image_path = Column(String(500), nullable=True)
    extracted_text = Column(Text, nullable=True)
    ocr_metadata = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, PROCESSED, REVIEW_REQUIRED
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="prescription")


class Transaction(Base):
    """
    Pharmacy sale transaction entity.
    """
    __tablename__ = "transactions"

    transaction_id = Column(String(50), primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    pharmacist_id = Column(String(50), nullable=False, index=True)
    prescription_id = Column(String(50), ForeignKey("prescriptions.prescription_id"), nullable=True, index=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="RECORDED", index=True)  # RECORDED, PENDING_REVIEW, FLAGGED, CLEARED
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    prescription = relationship("Prescription", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")


class TransactionItem(Base):
    """
    Line item within a sale transaction, capturing historical snapshots of medicine info.
    """
    __tablename__ = "transaction_items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(50), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    medicine_id = Column(String(50), ForeignKey("medicines.medicine_id"), nullable=False, index=True)
    medicine_name = Column(String(200), nullable=False)  # Historical snapshot
    strength = Column(String(50), nullable=False)        # Historical snapshot
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)          # Historical snapshot from DB price at transaction time
    subtotal = Column(Float, nullable=False)            # quantity * unit_price

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="check_item_unit_price_non_negative"),
        CheckConstraint("subtotal >= 0", name="check_item_subtotal_non_negative"),
    )

    transaction = relationship("Transaction", back_populates="items")
    medicine = relationship("Medicine", back_populates="transaction_items")
