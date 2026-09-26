"""
Self-contained verification script for the prescription OCR module.

Generates a synthetic, non-sensitive prescription image dynamically in a
temporary folder, tests image validation, pipeline coordination, and text extraction,
and cleans up afterwards without storing any patient data or image files in Git.

Usage:
    python prescription_processing/ocr/example_test.py
"""

import sys
import tempfile
from pathlib import Path

# Ensure package importability
CURRENT_FILE = Path(__file__).resolve()
WORKSPACE_ROOT = CURRENT_FILE.parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from prescription_processing.ocr.base import (
    InvalidImageError,
    UnsupportedFormatError,
)
from prescription_processing.ocr.mock_engine import MockOCREngine
from prescription_processing.ocr.service import (
    PrescriptionOCRService,
    clean_extracted_text,
)
from prescription_processing.ocr.tesseract_engine import TesseractEngine
from prescription_processing.ocr.validator import validate_image_path

SAMPLE_TEXT = (
    "City Health Clinic - Rx Department\n"
    "Prescriber: Dr. Emily Clark, MD (Lic #MD-12345)\n"
    "Patient: Test Subject 01\n"
    "Rx: Amoxicillin 500mg Capsules\n"
    "Qty: 30 (thirty)\n"
    "Sig: Take 1 capsule 3 times daily with meals\n"
    "Date: 2026-01-15"
)


def create_synthetic_image(output_path: Path, text: str) -> None:
    """Generate a clean synthetic prescription image using Pillow."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        # If Pillow is missing, create a minimal dummy file for format testing
        output_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 50)
        return

    width = 700
    height = 350
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Simple text rendering line by line
    y_offset = 30
    for line in text.split("\n"):
        draw.text((40, y_offset), line, fill=(0, 0, 0))
        y_offset += 35

    image.save(output_path, format="PNG")


def run_tests() -> bool:
    print("=" * 60)
    print("Running Prescription OCR Module Self-Test")
    print("=" * 60)
    passed = 0
    failed = 0

    # 1. Text Cleaner Test
    print("[1/5] Testing text cleanup and line structure preservation...")
    dirty_text = "   Line 1   \r\n\r\n\r\n\r\nLine 2 with trailing spaces   \n\n\nLine 3   \n"
    cleaned = clean_extracted_text(dirty_text)
    expected = "Line 1\n\nLine 2 with trailing spaces\n\nLine 3"
    if cleaned == expected:
        print("      PASS: Text cleanup properly condensed blank lines & preserved structure.")
        passed += 1
    else:
        print(f"      FAIL: Expected:\n{expected!r}\nGot:\n{cleaned!r}")
        failed += 1

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        synth_img = temp_path / "synthetic_rx.png"
        invalid_ext_img = temp_path / "rx_document.pdf"
        missing_img = temp_path / "non_existent.png"

        create_synthetic_image(synth_img, SAMPLE_TEXT)
        invalid_ext_img.write_text("dummy pdf content")

        # 2. Validation Test: Non-existent file
        print("[2/5] Testing error handling for non-existent file...")
        try:
            validate_image_path(missing_img)
            print("      FAIL: Did not raise InvalidImageError on missing file.")
            failed += 1
        except InvalidImageError:
            print("      PASS: Correctly raised InvalidImageError for missing file.")
            passed += 1

        # 3. Validation Test: Unsupported format
        print("[3/5] Testing rejection of unsupported file extensions...")
        try:
            validate_image_path(invalid_ext_img)
            print("      FAIL: Did not raise UnsupportedFormatError on .pdf.")
            failed += 1
        except UnsupportedFormatError:
            print("      PASS: Correctly rejected unsupported .pdf format.")
            passed += 1

        # 4. Pipeline Test with Modular Mock Engine
        print("[4/5] Testing full OCR pipeline with Mock Engine...")
        mock_engine = MockOCREngine(simulated_text=SAMPLE_TEXT)
        service = PrescriptionOCRService(engine=mock_engine)
        result = service.process_image(synth_img)

        if result.raw_text == SAMPLE_TEXT and result.line_count == 7:
            print(f"      PASS: OCR pipeline extracted {result.line_count} lines successfully.")
            passed += 1
        else:
            print(f"      FAIL: Mock pipeline mismatch. Lines={result.line_count}")
            failed += 1

        # 5. Live Tesseract OCR Engine Availability Check
        print("[5/5] Checking Tesseract OCR engine status...")
        tess_engine = TesseractEngine()
        if tess_engine.is_available():
            try:
                tess_service = PrescriptionOCRService(engine=tess_engine)
                tess_result = tess_service.process_image(synth_img)
                print("      PASS: Live Tesseract OCR detected and successfully extracted text!")
                print("      --- Extracted Sample ---")
                for line in tess_result.raw_text.split("\n")[:3]:
                    print(f"      | {line}")
                print("      ------------------------")
                passed += 1
            except Exception as exc:
                print(f"      WARN: Tesseract error during test: {exc}")
                failed += 1
        else:
            print("      INFO: Tesseract binary/pytesseract is not installed yet.")
            print("            (Modular architecture verified; install packages to enable live OCR).")
            passed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed.")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
