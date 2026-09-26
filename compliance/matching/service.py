from prescription_processing.extraction.models import ExtractedMedicineItem

from .models import SaleItem, MatchingReport
from .matcher import PrescriptionSaleMatcher


class MatchingService:
    """Service layer for prescription and pharmacy sale matching."""

    def __init__(self):
        self.matcher = PrescriptionSaleMatcher()

    def match_prescription(
        self,
        prescription_items: list[ExtractedMedicineItem],
        sale_items: list[SaleItem],
    ) -> MatchingReport:
        """
        Compare extracted prescription medicines
        against pharmacy sale items.
        """

        return self.matcher.match(
            prescription_items=prescription_items,
            sale_items=sale_items,
        )