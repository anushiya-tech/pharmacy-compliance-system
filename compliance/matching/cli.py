import json
import sys

from .models import SaleItem
from .service import MatchingService


def load_sale_items(path: str) -> list[SaleItem]:
    """Load pharmacy sale items from a JSON file."""

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return [
        SaleItem(
            medicine_name=item["medicine_name"],
            normalized_name=item["normalized_name"],
            strength_value=item.get("strength_value"),
            strength_unit=item.get("strength_unit"),
            dosage_form=item.get("dosage_form"),
            quantity=item.get("quantity"),
        )
        for item in data
    ]


def print_report(report):
    print("=" * 60)
    print("PRESCRIPTION - SALE MATCHING REPORT")
    print("=" * 60)

    print(f"Total prescription items : {report.total_prescription_items}")
    print(f"Matched items             : {len(report.matched_items)}")
    print(f"Missing items             : {len(report.missing_items)}")
    print(f"Quantity mismatches       : {len(report.quantity_mismatches)}")
    print(f"Extra sale items          : {len(report.extra_items)}")
    print()

    if report.matched_items:
        print("MATCHED ITEMS")
        print("-" * 60)

        for item in report.matched_items:
            print(
                f"{item.prescription_medicine} -> "
                f"{item.sale_medicine} | MATCHED"
            )

    if report.missing_items:
        print()
        print("MISSING ITEMS")
        print("-" * 60)

        for item in report.missing_items:
            print(
                f"{item.prescription_medicine} | "
                f"MISSING"
            )

    if report.quantity_mismatches:
        print()
        print("QUANTITY MISMATCHES")
        print("-" * 60)

        for item in report.quantity_mismatches:
            print(
                f"{item.prescription_medicine} -> "
                f"{item.sale_medicine} | "
                f"Prescription: {item.prescription_quantity} | "
                f"Sale: {item.sale_quantity}"
            )

    if report.extra_items:
        print()
        print("EXTRA SALE ITEMS")
        print("-" * 60)

        for item in report.extra_items:
            print(
                f"{item.medicine_name} | "
                f"Quantity: {item.quantity}"
            )

    print()
    print("=" * 60)

    if report.is_compliant:
        print("RESULT: COMPLIANT")
    else:
        print("RESULT: NON-COMPLIANT")

    print("=" * 60)


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m compliance.matching.cli <sale_items.json>")
        sys.exit(1)

    sale_items_path = sys.argv[1]

    sale_items = load_sale_items(sale_items_path)

    # CLI currently accepts sale data.
    # Prescription items will be connected through
    # the extraction service during integration.

    print(f"Loaded {len(sale_items)} sale items successfully.")


if __name__ == "__main__":
    main()