# Prescription Processing - Entity Extraction Module

This folder contains logic for parsing structured clinical fields from raw OCR text, converting unstructured text lines into structured prescription medicine items for downstream compliance matching.

It represents Stage 2 of **Member 2's Prescription OCR and Matching Engine**.

---

## 1. Purpose

The entity extraction module bridges raw OCR recognition and the compliance matching engine. It extracts:
- Raw medicine name
- Normalized canonical medicine identity
- Active ingredient strength value and unit
- Standardized dosage form
- Dispense quantity
- Administration frequency / directions (Sig)
- Original OCR text context and extraction confidence score

It does not make medical recommendations or infer missing information; it only extracts entities explicitly present in the OCR text.

---

## 2. Input Format

The module accepts input through three entry points:
1. **Raw OCR text string** (`str`): Multi-line text string with preserved line structure.
2. **`OCRResult` instance**: The output object produced by [`PrescriptionOCRService`](../ocr/service.py).
3. **Prescription image file path** (`.png`, `.jpg`, `.jpeg`): Automatically passed through the existing OCR service before entity extraction.

---

## 3. Output Structure

Extracted records are encapsulated in typed Python dataclasses:

### `ExtractedMedicineItem`
| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `medicine_name` | `str` | Raw medicine name from OCR | `"Amoxicillin"` |
| `normalized_name` | `str` | Lowercase canonical drug name for matching | `"amoxicillin"` |
| `strength_value` | `Optional[float]` | Numeric strength | `500.0` (or `None`) |
| `strength_unit` | `Optional[str]` | Normalized unit (`mg`, `ml`, `g`, `mcg`) | `"mg"` (or `None`) |
| `dosage_form` | `Optional[str]` | Canonical form (`tablet`, `capsule`, etc.) | `"capsule"` (or `None`) |
| `quantity` | `Optional[int]` | Total units to dispense | `30` (or `None`) |
| `frequency` | `Optional[str]` | Directions for use / Sig | `"1 cap 3 times daily"` |
| `original_text` | `str` | Exact OCR line(s) parsed | `"Amoxicillin 500mg Capsule"` |
| `confidence` | `float` | Extraction completeness score (0.0 to 1.0) | `1.0` |
| `extraction_status` | `str` | Qualitative status | `"success"`, `"partial"` |

### `ExtractedPrescription`
- `medicines`: `List[ExtractedMedicineItem]`
- `raw_ocr_text`: Complete input text
- `total_medicines_detected`: Count of detected medicine items
- `metadata`: Optional processing metadata (image path, OCR engine name, etc.)

---

## 4. Supported Extraction Patterns

The extraction engine uses configurable regular expressions ([`patterns.py`](patterns.py)) supporting diverse formats:

- **Single-line formats**:
  - `Paracetamol 500 mg Tablet`
  - `Amoxicillin 500mg Capsule`
  - `Azithromycin 250 mg - 6 Tablets`
  - `Cetirizine 10mg Tab Qty 10`
  - `Metformin 500 mg Tablet 30`
  - `Ibuprofen 400 mg Tab #60`
- **Multi-line blocks**:
  ```text
  1. Amoxicillin 500mg Capsule
     Sig: 1 capsule by mouth three times daily for 10 days
     Disp: 30
  ```
- **Administrative line filtering**:
  Automatically filters non-medicine lines such as prescriber details (`Dr. Emily Clark, MD`), patient headers (`Patient: John Doe`), dates (`Date: 2026-02-20`), clinic headings, and refill markers.

---

## 5. Usage & CLI Execution

### Running via Command Line
```powershell
# On a text file containing OCR text
python prescription_processing/extraction/cli.py path/to/ocr_output.txt

# Directly on an image (runs through existing OCR service first)
python prescription_processing/extraction/cli.py path/to/prescription.png

# Output as JSON
python prescription_processing/extraction/cli.py path/to/prescription.png --json
```

### Python API Integration
```python
from prescription_processing.extraction import PrescriptionExtractionService

service = PrescriptionExtractionService()

# 1. From text
result = service.extract_from_text("Amoxicillin 500mg Capsule Qty 30")
for med in result.medicines:
    print(med.normalized_name, med.strength_value, med.strength_unit, med.quantity)

# 2. From prescription image
result_from_img = service.extract_from_image("data/prescriptions/sample.png")
```

---

## 6. Example Input & Output

### Example Input
```text
City Health Clinic - Rx Department
Prescriber: Dr. Emily Clark, MD (Lic #MD-12345)
Patient: Anonymous Test Subject

1. Amoxicillin 500mg Capsule
   Sig: 1 capsule by mouth three times daily
   Disp: 30

2. Cetirizine 10mg Tab Qty 10
   Sig: 1 tab daily at bedtime
```

### Example Structured Output (`--json`)
```json
{
  "total_medicines_detected": 2,
  "medicines": [
    {
      "medicine_name": "Amoxicillin",
      "normalized_name": "amoxicillin",
      "strength_value": 500.0,
      "strength_unit": "mg",
      "dosage_form": "capsule",
      "quantity": 30,
      "frequency": "1 capsule by mouth three times daily",
      "original_text": "1. Amoxicillin 500mg Capsule | Sig: 1 capsule by mouth three times daily | Disp: 30",
      "confidence": 1.0,
      "extraction_status": "success"
    },
    {
      "medicine_name": "Cetirizine",
      "normalized_name": "cetirizine",
      "strength_value": 10.0,
      "strength_unit": "mg",
      "dosage_form": "tablet",
      "quantity": 10,
      "frequency": "1 tab daily at bedtime",
      "original_text": "2. Cetirizine 10mg Tab Qty 10 | Sig: 1 tab daily at bedtime",
      "confidence": 1.0,
      "extraction_status": "success"
    }
  ],
  "metadata": {}
}
```

---

## 7. Limitations & Edge Cases

- **Missing Values**: If strength, dosage form, or quantity are absent from the OCR line, they are set strictly to `None` without guessing or hallucinating.
- **Complex Compound Formulations**: Multi-ingredient drugs with multiple strengths (e.g. `Amoxicillin / Clavulanate 500/125mg`) will parse the primary numerical strength.
- **Unstructured Cursive Notes**: Free-form handwritten sig notes without standard keywords (`Sig:`, `Take`, `daily`) may only extract the primary medication line.
