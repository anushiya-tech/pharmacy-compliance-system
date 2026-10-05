"""
Base interfaces and exceptions for the prescription OCR module.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class OCRError(Exception):
    """Base exception for all OCR-related errors."""
    pass


class InvalidImageError(OCRError):
    """Raised when an input image file is missing, empty, or unreadable."""
    pass


class UnsupportedFormatError(OCRError):
    """Raised when an input file is not a supported image format."""
    pass


class OCREngineUnavailableError(OCRError):
    """Raised when the selected OCR engine or its required binary is not installed."""
    pass


class OCRExecutionError(OCRError):
    """Raised when an OCR engine fails during image processing."""
    pass


@dataclass(frozen=True)
class OCRResult:
    """Structured container holding extracted OCR text and metadata."""
    raw_text: str
    line_count: int
    engine_name: str
    image_path: Path
    confidence: Optional[float] = None


class OCREngine(ABC):
    """Abstract base class for pluggable OCR engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name identifier of the OCR engine."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the OCR engine and its underlying binaries/models are ready for use."""
        pass

    @abstractmethod
    def extract_text(self, image_path: Path) -> str:
        """
        Extract raw text from an image file.

        Args:
            image_path: Validated filesystem path to the target image.

        Returns:
            Extracted text content as a string.

        Raises:
            OCREngineUnavailableError: If engine dependencies are missing.
            OCRExecutionError: If text extraction fails during execution.
        """
        pass
