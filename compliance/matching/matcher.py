from prescription_processing.extraction.models import ExtractedMedicineItem

from .models import SaleItem, MatchResult, MatchingReport


class PrescriptionSaleMatcher:
    """Match prescription medicines against pharmacy sale items."""

    def match(
        self,
        prescription_items: list[ExtractedMedicineItem],
        sale_items: list[SaleItem],
    ) -> MatchingReport:

        matched_items = []
        missing_items = []
        quantity_mismatches = []
        extra_items = []

        used_sale_indexes = set()

        for prescription in prescription_items:

            matched_index = None

            for index, sale in enumerate(sale_items):

                if index in used_sale_indexes:
                    continue

                if self._medicine_matches(prescription, sale):
                    matched_index = index
                    break

            if matched_index is None:
                missing_items.append(
                    MatchResult(
                        prescription_medicine=prescription.medicine_name,
                        sale_medicine=None,
                        status="MISSING",
                        prescription_quantity=prescription.quantity,
                        sale_quantity=None,
                        quantity_difference=None,
                        reason="Prescription medicine was not found in sale items.",
                    )
                )
                continue

            used_sale_indexes.add(matched_index)

            sale = sale_items[matched_index]

            prescription_qty = prescription.quantity
            sale_qty = sale.quantity

            if (
                prescription_qty is not None
                and sale_qty is not None
                and prescription_qty != sale_qty
            ):
                quantity_mismatches.append(
                    MatchResult(
                        prescription_medicine=prescription.medicine_name,
                        sale_medicine=sale.medicine_name,
                        status="QUANTITY_MISMATCH",
                        prescription_quantity=prescription_qty,
                        sale_quantity=sale_qty,
                        quantity_difference=sale_qty - prescription_qty,
                        reason="Medicine matched but quantity is different.",
                    )
                )
            else:
                matched_items.append(
                    MatchResult(
                        prescription_medicine=prescription.medicine_name,
                        sale_medicine=sale.medicine_name,
                        status="MATCHED",
                        prescription_quantity=prescription_qty,
                        sale_quantity=sale_qty,
                        quantity_difference=0,
                        reason="Medicine and available quantity matched.",
                    )
                )

        for index, sale in enumerate(sale_items):
            if index not in used_sale_indexes:
                extra_items.append(sale)

        return MatchingReport(
            matched_items=matched_items,
            missing_items=missing_items,
            quantity_mismatches=quantity_mismatches,
            extra_items=extra_items,
        )

    def _medicine_matches(
        self,
        prescription: ExtractedMedicineItem,
        sale: SaleItem,
    ) -> bool:

        if prescription.normalized_name.lower() != sale.normalized_name.lower():
            return False

        if (
            prescription.strength_value is not None
            and sale.strength_value is not None
        ):
            if prescription.strength_value != sale.strength_value:
                return False

        if prescription.strength_unit and sale.strength_unit:
            if prescription.strength_unit.lower() != sale.strength_unit.lower():
                return False

        if prescription.dosage_form and sale.dosage_form:
            if prescription.dosage_form.lower() != sale.dosage_form.lower():
                return False

        return True