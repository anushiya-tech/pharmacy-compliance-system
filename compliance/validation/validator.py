from datetime import date
from typing import Optional

from .models import ValidationIssue
from .rules import (
    check_dosage_threshold,
    check_expiry,
    check_quantity_mismatch,
    check_restricted_medicine,
)


class ComplianceValidator:
    """Runs all configured compliance validation rules."""

    def validate_item(
        self,
        medicine_name: str,
        expiry_date: Optional[date] = None,
        quantity: Optional[int] = None,
        maximum_quantity: Optional[int] = None,
        prescription_quantity: Optional[int] = None,
        sale_quantity: Optional[int] = None,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        expiry_issue = check_expiry(
            medicine_name=medicine_name,
            expiry_date=expiry_date,
        )
        if expiry_issue is not None:
            issues.append(expiry_issue)

        restricted_issue = check_restricted_medicine(
            medicine_name=medicine_name,
        )
        if restricted_issue is not None:
            issues.append(restricted_issue)

        dosage_issue = check_dosage_threshold(
            medicine_name=medicine_name,
            quantity=quantity,
            maximum_quantity=maximum_quantity,
        )
        if dosage_issue is not None:
            issues.append(dosage_issue)

        mismatch_issue = check_quantity_mismatch(
            medicine_name=medicine_name,
            prescription_quantity=prescription_quantity,
            sale_quantity=sale_quantity,
        )
        if mismatch_issue is not None:
            issues.append(mismatch_issue)

        return issues