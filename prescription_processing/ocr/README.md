# Prescription Processing - OCR Module

This folder is responsible for image preprocessing (contrast enhancement, noise reduction, deskewing) and extracting raw text from prescription scans or photos using OCR engines.

It serves as the first stage of the **Pharmacy Compliance System** pipeline, converting digitized prescription images into raw text while strictly preserving clinical line and tabular structures.

---

## 1. Selected OCR Library & Rationale

We selected **Google Tesseract OCR** via the Python interface **`pytesseract`** (paired with **`Pillow`** for image I/O):

- **Reliable Local Execution on Windows**: Runs completely on-device without cloud API dependencies or recurring external costs.
- **Open-Source & Battle-Tested**: Highly optimized for structured printed document text and tabular clinical layouts.
- **Modular & Decoupled Architecture**: Wrapped inside a clean `OCREngine` abstract interface (`base.py`), enabling seamless future replacement or pairing with other engines (e.g. EasyOCR, PaddleOCR) without breaking upstream consumers.
- **No Sensitive Data Leaks**: Processing is strictly local, complying with healthcare privacy standards (e.g., HIPAA / patient data protection).

---

## 2. Required Packages & System Dependencies

### Python Packages (`prescription_processing/ocr/requirements.txt`)
- `pytesseract>=0.3.10`: Python wrapper for Google's Tesseract-OCR engine.
- `Pillow>=10.0.0`: Image processing and validation library.

### Windows System Dependency
- **Tesseract-OCR Binary**: The underlying C++ OCR engine for Windows.

---

## 3. Setup Instructions (Windows)

### Step 1: Install Python Requirements
From the project root:
```powershell
pip install -r prescription_processing/ocr/requirements.txt
```

### Step 2: Install Tesseract-OCR on Windows
1. Download the Windows 64-bit installer from the official UB-Mannheim repository:
   [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (default installation path is typically `C:\Program Files\Tesseract-OCR`).
3. Add `C:\Program Files\Tesseract-OCR` to your Windows system `PATH` environment variable, **or** set the `TESSERACT_CMD` environment variable:
   ```powershell
   $env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

*(Note: The module automatically checks default Windows paths such as `C:\Program Files\Tesseract-OCR\tesseract.exe` and `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe` even if not added to PATH).*

---

## 4. Input & Output Format

### Input Format
- **Supported File Types**: `.png`, `.jpg`, `.jpeg`.
- **Validation**: Verifies file existence, non-empty size, valid file extension, and image decode integrity before OCR execution.

### Output Format
- Clean raw text string (`str`) with normalized newlines (`\n`).
- Preserves prescription line structure (e.g., Doctor, Patient, Rx, Sig, Refills).
- Trims trailing line whitespace and collapses redundant 3+ consecutive newlines into single blank lines.

---

## 5. Usage & Commands

### Running OCR via CLI
Run the module CLI by passing an image path:
```powershell
python prescription_processing/ocr/cli.py path/to/prescription.png
```
Or as a Python module from the project root:
```powershell
python -m prescription_processing.ocr.cli path/to/prescription.png
```

To view verbose processing metadata (engine name, line counts):
```powershell
python prescription_processing/ocr/cli.py path/to/prescription.png --verbose
```

If you wish to specify an explicit path to your Tesseract binary:
```powershell
python prescription_processing/ocr/cli.py path/to/prescription.png --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### Running Self-Test & Example Verification
A self-contained synthetic test script is included. It generates a synthetic, non-sensitive prescription image dynamically in memory, verifies image validation rules, tests edge cases (e.g. non-existent files, invalid extensions), and tests the OCR pipeline without requiring real prescription images:

```powershell
python prescription_processing/ocr/example_test.py
```

---

## 6. Module Structure

```
prescription_processing/ocr/
├── __init__.py           # Package exports (PrescriptionOCRService, OCREngine, exceptions)
├── base.py               # Abstract OCREngine base class, OCRResult, and custom exceptions
├── cli.py                # Command-line entry point
├── example_test.py       # Self-contained synthetic test runner (zero committed patient data)
├── mock_engine.py        # Mock OCR engine for offline testing and decoupled development
├── requirements.txt      # Required Python package dependencies
├── service.py            # PrescriptionOCRService and text-cleaning coordinator
├── tesseract_engine.py   # Windows-compatible Tesseract OCR implementation
├── validator.py          # Image format & integrity validation
└── README.md             # Module documentation
```

---

## 7. Limitations & Assumptions
- **Handwritten Prescriptions**: Standard Tesseract is optimized for printed text. Doctor handwriting or cursive notes may have lower recognition accuracy without specialized fine-tuning or secondary handwriting models.
- **Image Quality**: Skewed, blurry, or low-contrast photos may require preprocessing (deskewing, binarization) in future stages.
- **Scope**: This module focuses strictly on raw optical character extraction. Extraction of entities (medication names, dosage, prescriber) is handled in the downstream `prescription_processing/extraction/` module.
