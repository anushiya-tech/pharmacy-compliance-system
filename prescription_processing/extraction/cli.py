"""
Command-line interface for prescription entity extraction and normalization.

Usage:
    python prescription_processing/extraction/cli.py <image_path_or_text_file>
    python -m prescription_processing.extraction.cli <image_path_or_text_file>
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure the parent package can be imported even when running directly
CURRENT_FILE = Path(__file__).resolve()
WORKSPACE_ROOT = CURRENT_FILE.parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from prescription_processing.extraction.service import PrescriptionExtractionService
from prescription_processing.ocr.validator import SUPPORTED_EXTENSIONS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract and normalize structured medicine entities from prescription image or text."
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to prescription image (PNG, JPG, JPEG) or a plain text file containing OCR text.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as formatted JSON.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input_path).resolve()
    if not input_path.exists():
        print(f"Error: Input path not found: '{input_path}'", file=sys.stderr)
        return 1

    service = PrescriptionExtractionService()

    try:
        suffix = input_path.suffix.lower()
        if suffix in SUPPORTED_EXTENSIONS:
            # Process as image through OCR
            result = service.extract_from_image(input_path)
        else:
            # Read as text file
            text_content = input_path.read_text(encoding="utf-8")
            result = service.extract_from_text(text_content)

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print("=" * 70)
            print(f"Prescription Extraction Summary (Total Detected: {result.total_medicines_detected})")
            print("=" * 70)
            if not result.medicines:
                print("No medicine records detected.")
            for idx, item in enumerate(result.medicines, 1):
                print(f"[{idx}] {item.medicine_name}")
                print(f"    Normalized:   {item.normalized_name}")
                strength_str = f"{item.strength_value} {item.strength_unit}" if item.strength_value is not None else "None"
                print(f"    Strength:     {strength_str}")
                print(f"    Dosage Form:  {item.dosage_form or 'None'}")
                print(f"    Quantity:     {item.quantity if item.quantity is not None else 'None'}")
                print(f"    Frequency:    {item.frequency or 'None'}")
                print(f"    Confidence:   {item.confidence} ({item.extraction_status})")
                print(f"    Source:       '{item.original_text}'")
                print("-" * 70)
        return 0

    except Exception as exc:
        print(f"Extraction error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
