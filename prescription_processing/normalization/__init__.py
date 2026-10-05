"""
Prescription Processing - Normalization Module.

Provides medicine name, dosage form, and strength unit canonicalization.
"""

from .normalizer import (
    MedicineNormalizer,
    clean_ocr_noise,
    normalize_dosage_form,
    normalize_medicine_name,
    normalize_strength_unit,
)
from .rules import (
    ADMINISTRATIVE_LINE_INDICATORS,
    DOSAGE_FORM_MAPPINGS,
    GLUED_UNIT_PATTERN,
    LINE_PREFIX_PATTERN,
    STRENGTH_UNIT_MAPPINGS,
)

__all__ = [
    "clean_ocr_noise",
    "normalize_medicine_name",
    "normalize_dosage_form",
    "normalize_strength_unit",
    "MedicineNormalizer",
    "DOSAGE_FORM_MAPPINGS",
    "STRENGTH_UNIT_MAPPINGS",
    "LINE_PREFIX_PATTERN",
    "GLUED_UNIT_PATTERN",
    "ADMINISTRATIVE_LINE_INDICATORS",
]
