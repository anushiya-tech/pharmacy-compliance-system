from dataclasses import dataclass
from typing import Optional


@dataclass
class SaleItem:
    medicine_name: str
    normalized_name: str
    strength_value: Optional[float] = None
    strength_unit: Optional[str] = None
    dosage_form: Optional[str] = None
    quantity: Optional[int] = None


@dataclass
class MatchResult:
    prescription_medicine: str
    sale_medicine: Optional[str]
    status: str
    prescription_quantity: Optional[int]
    sale_quantity: Optional[int]
    quantity_difference: Optional[int]
    reason: str


@dataclass
class MatchingReport:
    matched_items: list[MatchResult]
    missing_items: list[MatchResult]
    quantity_mismatches: list[MatchResult]
    extra_items: list[SaleItem]

    @property
    def total_prescription_items(self) -> int:
        return (
            len(self.matched_items)
            + len(self.missing_items)
            + len(self.quantity_mismatches)
        )

    @property
    def is_compliant(self) -> bool:
        return (
            len(self.missing_items) == 0
            and len(self.quantity_mismatches) == 0
            and len(self.extra_items) == 0
        )