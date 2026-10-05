"""
Command-line interface for prescription OCR extraction.

Usage:
    python prescription_processing/ocr/cli.py <path_to_image>
    python -m prescription_processing.ocr.cli <path_to_image>
"""

import argparse
import sys
from pathlib import Path

# Ensure the parent package can be imported even when running the script directly
CURRENT_FILE = Path(__file__).resolve()
WORKSPACE_ROOT = CURRENT_FILE.parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from prescription_processing.ocr.base import OCRError, OCREngineUnavailableError
from prescription_processing.ocr.mock_engine import MockOCREngine
from prescription_processing.ocr.service import PrescriptionOCRService
from prescription_processing.ocr.tesseract_engine import TesseractEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract raw text from a prescription image (PNG, JPG, JPEG) using local OCR."
    )
    parser.add_argument(
        "image_path",
        type=str,
        help="Path to the prescription image file (PNG, JPG, or JPEG).",
    )
    parser.add_argument(
        "--engine",
        type=str,
        choices=["tesseract", "mock"],
        default="tesseract",
        help="OCR engine to use: 'tesseract' (default) or 'mock' (for offline testing).",
    )
    parser.add_argument(
        "--tesseract-cmd",
        type=str,
        default=None,
        help="Optional explicit path to the tesseract executable (e.g. 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe').",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Display metadata (engine name, detected line count) along with output.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Select engine
    if args.engine == "mock":
        engine = MockOCREngine()
    else:
        engine = TesseractEngine(tesseract_cmd=args.tesseract_cmd)

    service = PrescriptionOCRService(engine=engine)

    try:
        result = service.process_image(args.image_path)

        if args.verbose:
            print("=" * 60)
            print(f"File:       {result.image_path}")
            print(f"Engine:     {result.engine_name}")
            print(f"Lines:      {result.line_count}")
            print("=" * 60)
            print("Extracted Text:")
            print("-" * 60)

        print(result.raw_text)

        if args.verbose:
            print("-" * 60)

        return 0

    except OCREngineUnavailableError as exc:
        print(f"Error (Engine Unavailable): {exc}", file=sys.stderr)
        return 2
    except OCRError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error during OCR processing: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
