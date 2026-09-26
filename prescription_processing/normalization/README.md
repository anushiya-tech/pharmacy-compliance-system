# Prescription Processing - Normalization Module

This folder standardizes extracted entities (e.g., brand names to generic names, dosage formats, medical abbreviations, and units) against standard drug databases and terminology dictionaries.

It ensures clinical records extracted from noisy OCR text are transformed into clean, canonical forms ready for exact or fuzzy inventory matching.

---

## 1. Purpose

OCR text from scanned prescriptions frequently contains typographical noise, inconsistent casing, irregular spacing, and diverse clinical abbreviations. The normalization layer provides:
- Safe OCR text cleaning (glued units, extra whitespace, noisy punctuation).
- Canonical dosage form mapping (e.g., `Tab`, `tabs`, `tab.` → `tablet`).
- Standardized strength unit representation (`MG`, `milligrams` → `mg`).
- Medicine name normalization (lowercasing, punctuation stripping, separating active drug identity from dosage forms, strengths, and quantities).

---

## 2. Normalization Rules & Behavior

### A. OCR Noise & Spacing Cleanup
- **Glued Numbers & Units**: Standardizes `500MG` → `500 mg`, `10ML` → `10 ml`, `0.5G` → `0.5 g`.
- **Spacing**: Replaces multiple spaces, tabs, and non-breaking spaces (`\u00a0`) with a single space.
- **Punctuation**: Normalizes curly quotes and stray OCR hyphens/bullets.

### B. Medicine Name Normalization
- Converts strings to lowercase.
- Trims whitespace and removes leading prescription line numbers (`1.`, `Rx:`, `-`, `*`).
- Removes embedded or trailing strength figures (`500 mg`, `250mg`).
- Strips trailing dosage-form tokens (`tablet`, `capsule`, `tab`).
- Strips explicit quantity expressions (`Qty 30`, `#60`, `x 10`).
- Removes trailing standalone counts (`Metformin 500 mg Tablet 30` → `metformin`).
- Preserves internal chemical hyphens/slashes while removing surrounding brackets or trailing commas.

### C. Dosage Form Standardization
Canonical dictionary ([`rules.py`](rules.py)) maps abbreviations and plural forms:
- `tab`, `tabs`, `tablet`, `tablets`, `caplet`, `pill` → `tablet`
- `cap`, `caps`, `capsule`, `capsules` → `capsule`
- `syr`, `syrup`, `susp`, `suspension` → `syrup` / `suspension`
- `inj`, `injection`, `vial`, `ampoule` → `injection`
- `crm`, `cream`, `oint`, `ointment`, `gel` → `cream` / `ointment` / `gel`
- `drop`, `drops` → `drops`
- `inhaler`, `puff` → `inhaler`

### D. Strength Unit Standardization
- `mg`, `milligram`, `milligrams` → `mg`
- `g`, `gm`, `gram`, `grams` → `g`
- `mcg`, `ug`, `microgram` → `mcg`
- `ml`, `milliliter`, `milliliters` → `ml`
- `iu`, `units` → `iu`
- `%` → `%`

---

## 3. Example Transformations

| Raw Input from OCR | Normalized Medicine Name | Normalized Strength | Normalized Dosage Form |
| :--- | :--- | :--- | :--- |
| `Paracetamol 500 mg Tablet` | `paracetamol` | `500.0 mg` | `tablet` |
| `Amoxicillin 500MG Capsule` | `amoxicillin` | `500.0 mg` | `capsule` |
| `Azithromycin 250 mg - 6 Tablets` | `azithromycin` | `250.0 mg` | `tablet` |
| `Cetirizine 10mg Tab Qty 10` | `cetirizine` | `10.0 mg` | `tablet` |
| `Metformin 500 mg Tablet 30` | `metformin` | `500.0 mg` | `tablet` |
| `Ibuprofen 400 mg Tab #60` | `ibuprofen` | `400.0 mg` | `tablet` |

---

## 4. Python API Usage

```python
from prescription_processing.normalization import (
    clean_ocr_noise,
    normalize_medicine_name,
    normalize_dosage_form,
    normalize_strength_unit,
)

# Clean OCR text
clean_line = clean_ocr_noise("Amoxicillin   500MG    Capsule")
# "Amoxicillin 500 mg Capsule"

# Canonical drug identity
name = normalize_medicine_name("  1. Amoxicillin 500MG Capsule  ")
# "amoxicillin"

# Dosage form
form = normalize_dosage_form("Tabs")
# "tablet"

# Strength unit
unit = normalize_strength_unit("MILLIGRAMS")
# "mg"
```

---

## 5. Limitations & Design Principles

- **No Medical Guessing**: Normalization strictly regularizes string representations. It does not infer or guess active pharmaceutical ingredients when absent from the OCR line.
- **No Incomplete Dictionaries**: Does not rely on rigid static lists of brand names; regex-based canonicalization dynamically accommodates international and generic drug nomenclature.
