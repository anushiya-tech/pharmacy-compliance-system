"""
Prescription Processing - Entity Extraction Module.

Extracts structured medicine entities, strengths, dosage forms, and quantities from OCR text.
"""

from .extractor import PrescriptionEntityExtractor
from .models import ExtractedMedicineItem, ExtractedPrescription
from .patterns import (
    DOSAGE_FORM_PATTERN,
    EXPLICIT_QUANTITY_PATTERN,
    FREQUENCY_EXPLICIT_PATTERN,
    FREQUENCY_INLINE_PATTERN,
    NON_MEDICINE_PREFIX_PATTERN,
    STRENGTH_PATTERN,
)
from .service import PrescriptionExtractionService

__all__ = [
    "ExtractedMedicineItem",
    "ExtractedPrescription",
    "PrescriptionEntityExtractor",
    "PrescriptionExtractionService",
    "STRENGTH_PATTERN",
    "DOSAGE_FORM_PATTERN",
    "EXPLICIT_QUANTITY_PATTERN",
    "FREQUENCY_EXPLICIT_PATTERN",
    "FREQUENCY_INLINE_PATTERN",
    "NON_MEDICINE_PREFIX_PATTERN",
]
