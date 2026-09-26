from datetime import date
from typing import Optional

from .models import ValidationReport
from .validator import ComplianceValidator


class ComplianceValidationService:
    """High-level service for validating medicine compliance."""

    def __init__(self) -> None:
        self.validator = ComplianceValidator()

    def validate_medicine(
        self,
        medicine_name: str,
        expiry_date: Optional[date] = None,
        quantity: Optional[int] = None,
        maximum_quantity: Optional[int] = None,
        prescription_quantity: Optional[int] = None,
        sale_quantity: Optional[int] = None,
    ) -> ValidationReport:
        issues = self.validator.validate_item(
            medicine_name=medicine_name,
            expiry_date=expiry_date,
            quantity=quantity,
            maximum_quantity=maximum_quantity,
            prescription_quantity=prescription_quantity,
            sale_quantity=sale_quantity,
        )

        return ValidationReport(issues=issues)