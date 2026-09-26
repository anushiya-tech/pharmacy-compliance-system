from datetime import date

import unittest

from compliance.matching.models import SaleItem
from compliance.matching.service import MatchingService
from compliance.validation.service import ComplianceValidationService
from prescription_processing.extraction.models import ExtractedMedicineItem


class TestComplianceIntegration(unittest.TestCase):

    def test_matching_and_validation_work_together(self):
        prescription_items = [
            ExtractedMedicineItem(
                medicine_name="Paracetamol",
                normalized_name="paracetamol",
                strength_value=500,
                strength_unit="mg",
                dosage_form="tablet",
                quantity=10,
            )
        ]

        sale_items = [
            SaleItem(
                medicine_name="Paracetamol",
                normalized_name="paracetamol",
                strength_value=500,
                strength_unit="mg",
                dosage_form="tablet",
                quantity=10,
            )
        ]

        matching_service = MatchingService()
        matching_report = matching_service.match_prescription(
            prescription_items=prescription_items,
            sale_items=sale_items,
        )

        self.assertTrue(matching_report.is_compliant)
        self.assertEqual(matching_report.total_prescription_items, 1)

        validation_service = ComplianceValidationService()
        validation_report = validation_service.validate_medicine(
            medicine_name="Paracetamol",
            expiry_date=date(2027, 12, 31),
            quantity=10,
            maximum_quantity=20,
            prescription_quantity=10,
            sale_quantity=10,
        )

        self.assertTrue(validation_report.is_valid)
        self.assertEqual(validation_report.issue_count, 0)


if __name__ == "__main__":
    unittest.main()