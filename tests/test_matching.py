import unittest

from prescription_processing.extraction.models import ExtractedMedicineItem
from compliance.matching.models import SaleItem
from compliance.matching.service import MatchingService


class TestPrescriptionSaleMatching(unittest.TestCase):

    def setUp(self):
        self.service = MatchingService()

    def create_prescription(
        self,
        name,
        normalized_name,
        strength_value=None,
        strength_unit=None,
        dosage_form=None,
        quantity=None,
    ):
        return ExtractedMedicineItem(
            medicine_name=name,
            normalized_name=normalized_name,
            strength_value=strength_value,
            strength_unit=strength_unit,
            dosage_form=dosage_form,
            quantity=quantity,
            frequency=None,
            original_text=name,
            confidence=1.0,
            extraction_status="complete",
        )

    def test_exact_match(self):
        prescription = [
            self.create_prescription(
                "Amoxicillin",
                "amoxicillin",
                500,
                "mg",
                "capsule",
                30,
            )
        ]

        sale = [
            SaleItem(
                medicine_name="Amoxicillin",
                normalized_name="amoxicillin",
                strength_value=500,
                strength_unit="mg",
                dosage_form="capsule",
                quantity=30,
            )
        ]

        report = self.service.match_prescription(
            prescription,
            sale,
        )

        self.assertEqual(len(report.matched_items), 1)
        self.assertEqual(len(report.missing_items), 0)
        self.assertEqual(len(report.quantity_mismatches), 0)
        self.assertEqual(len(report.extra_items), 0)
        self.assertTrue(report.is_compliant)

    def test_missing_medicine(self):
        prescription = [
            self.create_prescription(
                "Amoxicillin",
                "amoxicillin",
                500,
                "mg",
                "capsule",
                30,
            )
        ]

        sale = []

        report = self.service.match_prescription(
            prescription,
            sale,
        )

        self.assertEqual(len(report.missing_items), 1)
        self.assertFalse(report.is_compliant)

    def test_quantity_mismatch(self):
        prescription = [
            self.create_prescription(
                "Amoxicillin",
                "amoxicillin",
                500,
                "mg",
                "capsule",
                30,
            )
        ]

        sale = [
            SaleItem(
                medicine_name="Amoxicillin",
                normalized_name="amoxicillin",
                strength_value=500,
                strength_unit="mg",
                dosage_form="capsule",
                quantity=20,
            )
        ]

        report = self.service.match_prescription(
            prescription,
            sale,
        )

        self.assertEqual(len(report.quantity_mismatches), 1)
        self.assertEqual(
            report.quantity_mismatches[0].quantity_difference,
            -10,
        )
        self.assertFalse(report.is_compliant)

    def test_extra_medicine(self):
        prescription = [
            self.create_prescription(
                "Amoxicillin",
                "amoxicillin",
                500,
                "mg",
                "capsule",
                30,
            )
        ]

        sale = [
            SaleItem(
                medicine_name="Amoxicillin",
                normalized_name="amoxicillin",
                strength_value=500,
                strength_unit="mg",
                dosage_form="capsule",
                quantity=30,
            ),
            SaleItem(
                medicine_name="Cetirizine",
                normalized_name="cetirizine",
                strength_value=10,
                strength_unit="mg",
                dosage_form="tablet",
                quantity=10,
            ),
        ]

        report = self.service.match_prescription(
            prescription,
            sale,
        )

        self.assertEqual(len(report.matched_items), 1)
        self.assertEqual(len(report.extra_items), 1)
        self.assertFalse(report.is_compliant)

    def test_multiple_medicines(self):
        prescription = [
            self.create_prescription(
                "Amoxicillin",
                "amoxicillin",
                500,
                "mg",
                "capsule",
                30,
            ),
            self.create_prescription(
                "Cetirizine",
                "cetirizine",
                10,
                "mg",
                "tablet",
                10,
            ),
        ]

        sale = [
            SaleItem(
                medicine_name="Amoxicillin",
                normalized_name="amoxicillin",
                strength_value=500,
                strength_unit="mg",
                dosage_form="capsule",
                quantity=30,
            ),
            SaleItem(
                medicine_name="Cetirizine",
                normalized_name="cetirizine",
                strength_value=10,
                strength_unit="mg",
                dosage_form="tablet",
                quantity=10,
            ),
        ]

        report = self.service.match_prescription(
            prescription,
            sale,
        )

        self.assertEqual(len(report.matched_items), 2)
        self.assertTrue(report.is_compliant)


if __name__ == "__main__":
    unittest.main()