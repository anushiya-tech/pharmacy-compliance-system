"""
Service integration connecting OCR output to entity extraction and normalization.
"""

from pathlib import Path
from typing import Optional, Union

from prescription_processing.ocr import OCRResult, PrescriptionOCRService
from .extractor import PrescriptionEntityExtractor
from .models import ExtractedPrescription


class PrescriptionExtractionService:
    """
    Coordinates the end-to-end pipeline:
    Image / OCR Text -> OCR Extraction -> Entity Parsing -> Normalization -> Structured Items.
    """

    def __init__(
        self,
        extractor: Optional[PrescriptionEntityExtractor] = None,
        ocr_service: Optional[PrescriptionOCRService] = None,
    ):
        """
        Initialize extraction service.

        Args:
            extractor: Optional custom entity extractor instance.
            ocr_service: Optional OCR service instance (defaults to PrescriptionOCRService).
        """
        self.extractor = extractor or PrescriptionEntityExtractor()
        self._ocr_service = ocr_service

    @property
    def ocr_service(self) -> PrescriptionOCRService:
        """Lazy-initialize default OCR service if not explicitly injected."""
        if self._ocr_service is None:
            self._ocr_service = PrescriptionOCRService()
        return self._ocr_service

    def extract_from_text(self, ocr_text: str) -> ExtractedPrescription:
        """
        Parse raw OCR text into structured prescription records.

        Args:
            ocr_text: Cleaned text string from OCR.

        Returns:
            ExtractedPrescription containing normalized items.
        """
        return self.extractor.extract(ocr_text)

    def extract_from_ocr_result(self, ocr_result: OCRResult) -> ExtractedPrescription:
        """
        Parse an OCRResult object from the OCR module.

        Args:
            ocr_result: OCRResult object produced by PrescriptionOCRService.

        Returns:
            ExtractedPrescription with populated metadata.
        """
        prescription = self.extractor.extract(ocr_result.raw_text)
        prescription.metadata.update(
            {
                "engine": ocr_result.engine_name,
                "image_path": str(ocr_result.image_path),
                "line_count": ocr_result.line_count,
            }
        )
        return prescription

    def extract_from_image(self, image_path: Union[str, Path]) -> ExtractedPrescription:
        """
        Run the complete pipeline from prescription image to structured data.

        Pipeline:
        Prescription Image
        → Existing OCR Service
        → Raw OCR Text
        → Entity Extraction
        → Normalization
        → Structured Prescription Items

        Args:
            image_path: Path to the input prescription image file (.png, .jpg, .jpeg).

        Returns:
            ExtractedPrescription containing structured medicine records.
        """
        ocr_result = self.ocr_service.process_image(image_path)
        return self.extract_from_ocr_result(ocr_result)
