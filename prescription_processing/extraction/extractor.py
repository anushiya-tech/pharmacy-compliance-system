"""
Prescription entity extractor for parsing clinical fields from OCR text lines.
"""

import re
from typing import List, Optional, Tuple

from prescription_processing.normalization import (
    clean_ocr_noise,
    normalize_dosage_form,
    normalize_medicine_name,
    normalize_strength_unit,
)
from .models import ExtractedMedicineItem, ExtractedPrescription
from .patterns import (
    DOSAGE_FORM_PATTERN,
    EXPLICIT_QUANTITY_PATTERN,
    FREQUENCY_EXPLICIT_PATTERN,
    FREQUENCY_INLINE_PATTERN,
    NON_MEDICINE_PREFIX_PATTERN,
    QUANTITY_WITH_FORM_PATTERN,
    STRENGTH_PATTERN,
    TRAILING_COUNT_PATTERN,
)


class PrescriptionEntityExtractor:
    """
    Parses unstructured OCR text lines into structured ExtractedMedicineItem records.
    """

    def extract(self, ocr_text: str) -> ExtractedPrescription:
        """
        Extract all medicine items detected in the raw OCR text.

        Args:
            ocr_text: Raw text string produced by OCR service.

        Returns:
            ExtractedPrescription containing list of ExtractedMedicineItem objects.
        """
        if not ocr_text or not ocr_text.strip():
            return ExtractedPrescription(medicines=[], raw_ocr_text=ocr_text or "")

        lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
        medicines: List[ExtractedMedicineItem] = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 1. Skip non-medicine administrative lines (doctor, clinic, patient, etc.)
            if self._is_administrative_line(line):
                i += 1
                continue

            # 2. Check if this line looks like a medicine line
            if self._is_medicine_line(line):
                matched_lines = [line]
                frequency_from_next: Optional[str] = None
                quantity_from_next: Optional[int] = None

                # Look ahead for attached Sig/Disp lines
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if self._is_administrative_line(next_line):
                        break

                    sig_match = FREQUENCY_EXPLICIT_PATTERN.search(next_line)
                    qty_match = EXPLICIT_QUANTITY_PATTERN.search(next_line)

                    if sig_match and not frequency_from_next:
                        frequency_from_next = sig_match.group("freq").strip()
                        matched_lines.append(next_line)
                        j += 1
                    elif qty_match and not quantity_from_next and not self._is_medicine_line(next_line):
                        quantity_from_next = int(qty_match.group("qty"))
                        matched_lines.append(next_line)
                        j += 1
                    else:
                        break

                combined_text = " | ".join(matched_lines)
                item = self._parse_medicine_entry(
                    primary_line=line,
                    combined_text=combined_text,
                    extra_frequency=frequency_from_next,
                    extra_quantity=quantity_from_next,
                )
                if item:
                    medicines.append(item)

                i = j
            else:
                i += 1

        return ExtractedPrescription(
            medicines=medicines,
            raw_ocr_text=ocr_text,
            total_medicines_detected=len(medicines),
        )

    def _is_administrative_line(self, line: str) -> bool:
        """Detect whether a line is clearly clinical metadata rather than a medicine entry."""
        cleaned = clean_ocr_noise(line)
        if NON_MEDICINE_PREFIX_PATTERN.search(cleaned):
            return True

        lower = cleaned.lower()
        # General clinic / hospital header check without medicine indicators
        if any(term in lower for term in ["clinic", "hospital", "pharmacy", "department", "tel:", "phone:"]):
            if not STRENGTH_PATTERN.search(cleaned) and not DOSAGE_FORM_PATTERN.search(cleaned):
                return True

        if lower.startswith("date:") or lower.startswith("refills:"):
            return True

        return False

    def _is_medicine_line(self, line: str) -> bool:
        """Check if a line contains distinct medicine markers (strength, dosage form, or Rx prefix)."""
        cleaned = clean_ocr_noise(line)
        has_strength = bool(STRENGTH_PATTERN.search(cleaned))
        has_dosage_form = bool(DOSAGE_FORM_PATTERN.search(cleaned))
        starts_with_rx = bool(re.match(r"^(?:rx\b|rx[:.\s]+|\d+[\.\)]\s+)", cleaned, re.IGNORECASE))

        # A line is a medicine candidate if it has strength OR dosage form, or is an explicit Rx item
        if has_strength or has_dosage_form:
            return True
        if starts_with_rx and len(cleaned.split()) >= 2:
            return True

        return False

    def _parse_medicine_entry(
        self,
        primary_line: str,
        combined_text: str,
        extra_frequency: Optional[str] = None,
        extra_quantity: Optional[int] = None,
    ) -> Optional[ExtractedMedicineItem]:
        """Parse individual fields from candidate medicine lines."""
        cleaned_primary = clean_ocr_noise(primary_line)

        # 1. Strength & Unit extraction
        strength_val: Optional[float] = None
        strength_unit: Optional[str] = None
        strength_match = STRENGTH_PATTERN.search(cleaned_primary)
        if strength_match:
            try:
                strength_val = float(strength_match.group("val"))
                raw_unit = strength_match.group("unit")
                strength_unit = normalize_strength_unit(raw_unit)
            except (ValueError, TypeError):
                strength_val = None
                strength_unit = None

        # 2. Dosage Form extraction
        dosage_form: Optional[str] = None
        form_match = DOSAGE_FORM_PATTERN.search(cleaned_primary)
        if form_match:
            dosage_form = normalize_dosage_form(form_match.group("form"))

        # 3. Quantity extraction
        quantity: Optional[int] = extra_quantity
        if quantity is None:
            # Check explicit pattern (Qty: 10, Disp: 30)
            qty_match = EXPLICIT_QUANTITY_PATTERN.search(cleaned_primary)
            if qty_match:
                quantity = int(qty_match.group("qty"))
            else:
                # Check trailing count (Tablet 30)
                trailing_match = TRAILING_COUNT_PATTERN.search(cleaned_primary)
                if trailing_match:
                    quantity = int(trailing_match.group("qty"))
                else:
                    # Check '- 6 Tablets'
                    form_qty_match = QUANTITY_WITH_FORM_PATTERN.search(cleaned_primary)
                    if form_qty_match:
                        quantity = int(form_qty_match.group("qty"))

        # 4. Frequency / Directions extraction
        frequency: Optional[str] = extra_frequency
        if not frequency:
            sig_match = FREQUENCY_EXPLICIT_PATTERN.search(cleaned_primary)
            if sig_match:
                frequency = sig_match.group("freq").strip()
            else:
                inline_match = FREQUENCY_INLINE_PATTERN.search(cleaned_primary)
                if inline_match:
                    frequency = inline_match.group("freq").strip()

        # 5. Medicine Name Extraction
        raw_name, normalized_name = self._extract_names(
            cleaned_primary,
            strength_match,
            form_match,
        )

        if not normalized_name:
            return None

        # 6. Confidence Scoring
        confidence, status = self._calculate_confidence(
            has_name=bool(normalized_name),
            has_strength=strength_val is not None,
            has_form=dosage_form is not None,
            has_quantity=quantity is not None,
        )

        return ExtractedMedicineItem(
            medicine_name=raw_name,
            normalized_name=normalized_name,
            strength_value=strength_val,
            strength_unit=strength_unit,
            dosage_form=dosage_form,
            quantity=quantity,
            frequency=frequency,
            original_text=combined_text,
            confidence=confidence,
            extraction_status=status,
        )

    def _extract_names(
        self,
        line: str,
        strength_match: Optional[re.Match],
        form_match: Optional[re.Match],
    ) -> Tuple[str, str]:
        """
        Derive the raw medicine name and normalized canonical name.
        Uses boundaries of strength or dosage form to cleanly segment the drug identity.
        """
        # Strip leading numbering like '1. ', 'Rx: '
        trimmed = re.sub(r"^(?:rx\b|rx[:.\s]+|\d+[\.\)]\s+|[-*•]\s+)", "", line, flags=re.IGNORECASE).strip()

        # Determine cutoff position before strength or dosage form
        cut_positions = []
        if strength_match:
            # Find start position relative to trimmed string
            pos = trimmed.lower().find(strength_match.group(0).lower())
            if pos > 0:
                cut_positions.append(pos)
        if form_match:
            pos = trimmed.lower().find(form_match.group(0).lower())
            if pos > 0:
                cut_positions.append(pos)

        if cut_positions:
            candidate_raw = trimmed[: min(cut_positions)].strip()
        else:
            candidate_raw = trimmed

        # Clean trailing separators (- or :)
        candidate_raw = re.sub(r"[\s\-:,]+$", "", candidate_raw).strip()

        normalized = normalize_medicine_name(candidate_raw if candidate_raw else trimmed)

        # Fallback if cutting was too aggressive
        if not normalized:
            normalized = normalize_medicine_name(trimmed)
            raw_name = trimmed
        else:
            raw_name = candidate_raw

        return raw_name, normalized

    def _calculate_confidence(
        self,
        has_name: bool,
        has_strength: bool,
        has_form: bool,
        has_quantity: bool,
    ) -> Tuple[float, str]:
        """Calculate confidence score and qualitative status."""
        score = 0.4 if has_name else 0.0
        if has_strength:
            score += 0.3
        if has_form:
            score += 0.2
        if has_quantity:
            score += 0.1

        score = round(min(1.0, score), 2)
        if score >= 0.8:
            status = "success"
        elif score >= 0.6:
            status = "partial"
        else:
            status = "uncertain"

        return score, status
