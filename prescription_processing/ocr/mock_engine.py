"""
Mock OCR engine for offline testing, CI verification, and modular decoupling.
"""

from pathlib import Path
from typing import Optional

from .base import OCREngine


class MockOCREngine(OCREngine):
    """
    Simulated OCR engine used for automated tests and pipeline validation
    without external OCR binary dependencies.
    """

    def __init__(self, simulated_text: Optional[str] = None):
        self._simulated_text = simulated_text

    @property
    def name(self) -> str:
        return "mock"

    def is_available(self) -> bool:
        return True

    def extract_text(self, image_path: Path) -> str:
        """
        Return predefined mock text or standard synthetic prescription text.
        """
        if self._simulated_text is not None:
            return self._simulated_text

        return (
            "Rx Prescription\n"
            f"Source: {image_path.name}\n"
            "Prescriber: Dr. Sarah Connor, MD (Lic #MD-99482)\n"
            "Patient: John Doe (DOB: 1985-04-12)\n"
            "Medication: Amoxicillin 500mg Capsule\n"
            "Dispense: 30 (thirty) capsules\n"
            "Sig: 1 capsule by mouth three times daily for 10 days\n"
            "Refills: 0\n"
            "Date: 2026-03-15"
        )
