from datetime import date
from typing import Optional

from .models import ValidationIssue


# Example restricted medicine schedules.
# This is a project-level rule list and is not a complete regulatory database.
RESTRICTED_MEDICINES = {
    "alprazolam",
    "diazepam",
    "clonazepam",
    "tramadol",
}


def check_expiry(
    medicine_name: str,
    expiry_date: Optional[date],
    today: Optional[date] = None,
) -> Optional[ValidationIssue]:
    """Check whether a medicine has expired."""

    if expiry_date is None:
        return None

    if today is None:
        today = date.today()

    if expiry_date < today:
        return ValidationIssue(
            medicine_name=medicine_name,
            rule="expiry",
            status="FAIL",
            message=f"Medicine expired on {expiry_date.isoformat()}",
        )

    return None


def check_restricted_medicine(
    medicine_name: str,
) -> Optional[ValidationIssue]:
    """Check whether a medicine is in the project's restricted list."""

    normalized_name = medicine_name.strip().lower()

    if normalized_name in RESTRICTED_MEDICINES:
        return ValidationIssue(
            medicine_name=medicine_name,
            rule="restricted_medicine",
            status="WARNING",
            message="Medicine requires restricted-drug handling verification",
        )

    return None


def check_dosage_threshold(
    medicine_name: str,
    quantity: Optional[int],
    maximum_quantity: Optional[int],
) -> Optional[ValidationIssue]:
    """Check whether the supplied quantity exceeds a configured threshold."""

    if quantity is None or maximum_quantity is None:
        return None

    if quantity > maximum_quantity:
        return ValidationIssue(
            medicine_name=medicine_name,
            rule="dosage_threshold",
            status="FAIL",
            message=(
                f"Quantity {quantity} exceeds configured maximum "
                f"of {maximum_quantity}"
            ),
        )

    return None


def check_quantity_mismatch(
    medicine_name: str,
    prescription_quantity: Optional[int],
    sale_quantity: Optional[int],
) -> Optional[ValidationIssue]:
    """Check whether prescription and sale quantities are different."""

    if prescription_quantity is None or sale_quantity is None:
        return None

    if prescription_quantity != sale_quantity:
        return ValidationIssue(
            medicine_name=medicine_name,
            rule="quantity_mismatch",
            status="FAIL",
            message=(
                f"Prescription quantity is {prescription_quantity} "
                f"but sale quantity is {sale_quantity}"
            ),
        )

    return None