"""
Service coordinator for prescription OCR processing and text cleanup.
"""

import re
from pathlib import Path
from typing import Optional, Union

from .base import OCREngine, OCRResult
from .tesseract_engine import TesseractEngine
from .validator import validate_image_path


def clean_extracted_text(raw_text: str) -> str:
    """
    Clean extracted OCR text while preserving meaningful line breaks and layout.

    - Replaces carriage returns with standard newlines.
    - Strips trailing whitespace on each line.
    - Consolidates 3+ consecutive newlines into a maximum of 2 newlines (single blank line).
    - Strips leading and trailing whitespace from the full document.
    """
    if not raw_text:
        return ""

    # Normalize line endings
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip trailing whitespace on each individual line
    cleaned_lines = [line.rstrip() for line in normalized.split("\n")]

    joined = "\n".join(cleaned_lines)

    # Condense multiple blank lines into at most one blank line
    condensed = re.sub(r"\n{3,}", "\n\n", joined)

    return condensed.strip()


class PrescriptionOCRService:
    """
    Coordinates prescription image validation, OCR execution, and text normalization.
    """

    def __init__(self, engine: Optional[OCREngine] = None):
        """
        Initialize OCR service with an engine.
        Defaults to TesseractEngine if none is provided.
        """
        self.engine: OCREngine = engine if engine is not None else TesseractEngine()

    def process_image(self, image_path: Union[str, Path]) -> OCRResult:
        """
        Validate an image file, run OCR, and return a structured OCRResult.

        Args:
            image_path: Path to the prescription image.

        Returns:
            OCRResult containing clean text and metadata.
        """
        validated_path = validate_image_path(image_path)
        extracted = self.engine.extract_text(validated_path)
        cleaned = clean_extracted_text(extracted)
        lines = [line for line in cleaned.split("\n") if line.strip()]

        return OCRResult(
            raw_text=cleaned,
            line_count=len(lines),
            engine_name=self.engine.name,
            image_path=validated_path,
        )

    def extract_text(self, image_path: Union[str, Path]) -> str:
        """
        Convenience method to validate an image and return clean extracted string.

        Args:
            image_path: Path to the prescription image.

        Returns:
            Clean string containing detected text preserving line structure.
        """
        result = self.process_image(image_path)
        return result.raw_text
