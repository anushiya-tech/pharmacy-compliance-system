"""
Prescription Processing - Local OCR Module.

Provides modular optical character recognition for digitized prescription images.
"""

from .base import (
    InvalidImageError,
    OCREngine,
    OCREngineUnavailableError,
    OCRError,
    OCRExecutionError,
    OCRResult,
    UnsupportedFormatError,
)
from .mock_engine import MockOCREngine
from .service import PrescriptionOCRService, clean_extracted_text
from .tesseract_engine import TesseractEngine
from .validator import SUPPORTED_EXTENSIONS, validate_image_path

__all__ = [
    "OCREngine",
    "OCRResult",
    "OCRError",
    "InvalidImageError",
    "UnsupportedFormatError",
    "OCREngineUnavailableError",
    "OCRExecutionError",
    "TesseractEngine",
    "MockOCREngine",
    "PrescriptionOCRService",
    "clean_extracted_text",
    "validate_image_path",
    "SUPPORTED_EXTENSIONS",
]
