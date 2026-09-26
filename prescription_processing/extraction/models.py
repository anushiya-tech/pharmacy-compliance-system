"""
Data structures for extracted prescription items and processed prescriptions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExtractedMedicineItem:
    """
    Structured representation of a single medicine item extracted from a prescription.
    """
    medicine_name: str                      # Raw medicine name before normalization
    normalized_name: str                    # Canonical lowercase normalized name for matching
    strength_value: Optional[float] = None  # Numeric strength (e.g. 500.0)
    strength_unit: Optional[str] = None     # Normalized unit (e.g. 'mg', 'ml', 'g')
    dosage_form: Optional[str] = None       # Normalized dosage form (e.g. 'tablet', 'capsule')
    quantity: Optional[int] = None          # Dispense quantity count (e.g. 30, 6)
    frequency: Optional[str] = None         # Directions / frequency (e.g. 'once daily')
    original_text: str = ""                 # Exact source text line(s) from OCR
    confidence: float = 1.0                 # Confidence score (0.0 - 1.0)
    extraction_status: str = "success"      # Status ('success', 'partial', 'uncertain')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "medicine_name": self.medicine_name,
            "normalized_name": self.normalized_name,
            "strength_value": self.strength_value,
            "strength_unit": self.strength_unit,
            "dosage_form": self.dosage_form,
            "quantity": self.quantity,
            "frequency": self.frequency,
            "original_text": self.original_text,
            "confidence": round(self.confidence, 2),
            "extraction_status": self.extraction_status,
        }


@dataclass
class ExtractedPrescription:
    """
    Complete structured prescription containing all extracted medicine items.
    """
    medicines: List[ExtractedMedicineItem] = field(default_factory=list)
    raw_ocr_text: str = ""
    total_medicines_detected: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.total_medicines_detected and self.medicines:
            self.total_medicines_detected = len(self.medicines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire prescription result to dictionary."""
        return {
            "total_medicines_detected": self.total_medicines_detected,
            "medicines": [m.to_dict() for m in self.medicines],
            "metadata": self.metadata,
        }
