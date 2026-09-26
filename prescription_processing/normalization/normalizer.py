"""
Medicine name and clinical entity normalization logic for prescription matching.
"""

import re
from typing import Optional

from .rules import (
    DOSAGE_FORM_MAPPINGS,
    GLUED_UNIT_PATTERN,
    LINE_PREFIX_PATTERN,
    STRENGTH_UNIT_MAPPINGS,
)


def clean_ocr_noise(text: str) -> str:
    """
    Apply safe, deterministic OCR text cleanup:
    - Normalizes glued values and units: '500MG' -> '500 mg'.
    - Collapses multiple whitespace characters and tabs into single spaces.
    - Trims leading/trailing whitespace.
    """
    if not text:
        return ""

    # Replace fancy quotes, bullets, non-breaking spaces
    cleaned = text.replace("\u00a0", " ").replace("“", '"').replace("”", '"')

    # Normalize glued numbers and units: e.g. 500mg -> 500 mg, 10ML -> 10 ml
    def _normalize_unit_match(match: re.Match) -> str:
        return f"{match.group(1)} {match.group(2).lower()}"

    cleaned = GLUED_UNIT_PATTERN.sub(_normalize_unit_match, cleaned)

    # Collapse multiple spaces and tabs
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    return cleaned.strip()


def normalize_dosage_form(raw_form: Optional[str]) -> Optional[str]:
    """
    Normalize dosage form abbreviations into standard canonical forms:
    e.g. 'tab', 'tabs', 'Tab.' -> 'tablet'; 'cap', 'caps' -> 'capsule'.
    """
    if not raw_form:
        return None

    cleaned = raw_form.strip().lower().rstrip(".,;:")
    return DOSAGE_FORM_MAPPINGS.get(cleaned, cleaned)


def normalize_strength_unit(raw_unit: Optional[str]) -> Optional[str]:
    """
    Normalize strength units to standard lowercase symbols:
    e.g. 'MG', 'milligrams' -> 'mg'; 'UG', 'microgram' -> 'mcg'.
    """
    if not raw_unit:
        return None

    cleaned = raw_unit.strip().lower().rstrip(".,;:")
    return STRENGTH_UNIT_MAPPINGS.get(cleaned, cleaned)


def normalize_medicine_name(raw_name: str) -> str:
    """
    Normalize a raw medicine name for downstream catalog and inventory matching:
    - Lowercase conversion.
    - Stripping leading prescription prefixes (e.g. 'Rx:', '1.', '*').
    - Removing surrounding punctuation and symbols.
    - Stripping trailing dosage forms or strength numbers if attached.
    - Collapsing repeated spaces.

    Example:
        'Amoxicillin 500MG Capsule' -> 'amoxicillin'
        '  Rx: Cetirizine Tab.  '   -> 'cetirizine'
    """
    if not raw_name:
        return ""

    # 1. Clean OCR noise and lower-case
    name = clean_ocr_noise(raw_name).lower()

    # 2. Strip leading prescription prefixes (Rx:, #1, 1., -, *)
    name = LINE_PREFIX_PATTERN.sub("", name).strip()

    # 3. Strip trailing or embedded strength indicators: e.g. '500 mg', '250mg', '10 ml'
    name = re.sub(r"\b\d+(?:\.\d+)?\s*(?:mg|ml|g|gm|mcg|ug|iu|%)\b", "", name, flags=re.IGNORECASE)

    # 4. Strip dosage form terms from the medicine identity
    dosage_keywords = sorted(DOSAGE_FORM_MAPPINGS.keys(), key=len, reverse=True)
    dosage_pattern = r"\b(?:" + "|".join(re.escape(k) for k in dosage_keywords) + r")\b"
    name = re.sub(dosage_pattern, "", name, flags=re.IGNORECASE)

    # 5. Strip quantity keywords if caught in name: e.g. 'qty 30', 'x 10', '#60'
    name = re.sub(r"(?:\b(?:qty|quantity|disp|count|no|pack)\b|[#x])\s*[:.-]?\s*\d+\b", "", name, flags=re.IGNORECASE)

    # 6. Strip standalone trailing numbers (e.g. 'metformin 30' -> 'metformin')
    name = re.sub(r"\s+\d+\b", "", name)

    # 7. Remove non-alphanumeric punctuation except internal hyphens / slashes in drug names
    name = re.sub(r"^[^\w]+|[^\w]+$", "", name)
    name = re.sub(r"[,;:_(){}\[\]\"\']", " ", name)

    # 8. Collapse spaces and trim
    name = re.sub(r"\s+", " ", name).strip()

    return name


class MedicineNormalizer:
    """
    Facade class encapsulating clinical text and entity normalization rules.
    """

    def clean_text(self, text: str) -> str:
        return clean_ocr_noise(text)

    def normalize_name(self, raw_name: str) -> str:
        return normalize_medicine_name(raw_name)

    def normalize_dosage_form(self, raw_form: Optional[str]) -> Optional[str]:
        return normalize_dosage_form(raw_form)

    def normalize_strength_unit(self, raw_unit: Optional[str]) -> Optional[str]:
        return normalize_strength_unit(raw_unit)
