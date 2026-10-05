import unittest
from datetime import date

from compliance.validation.service import ComplianceValidationService


class TestComplianceValidation(unittest.TestCase):

    def setUp(self):
        self.service = ComplianceValidationService()

    def test_valid_medicine(self):
        report = self.service.validate_medicine(
            medicine_name="Paracetamol",
            expiry_date=date(2027, 12, 31),
            quantity=10,
            maximum_quantity=20,
            prescription_quantity=10,
            sale_quantity=10,
        )

        self.assertTrue(report.is_valid)
        self.assertEqual(report.issue_count, 0)

    def test_expired_medicine(self):
        report = self.service.validate_medicine(
            medicine_name="Paracetamol",
            expiry_date=date(2025, 1, 1),
        )

        self.assertFalse(report.is_valid)
        self.assertEqual(report.issue_count, 1)
        self.assertEqual(report.issues[0].rule, "expiry")
        self.assertEqual(report.issues[0].status, "FAIL")

    def test_restricted_medicine(self):
        report = self.service.validate_medicine(
            medicine_name="Alprazolam",
        )

        self.assertFalse(report.is_valid)
        self.assertEqual(report.issue_count, 1)
        self.assertEqual(
            report.issues[0].rule,
            "restricted_medicine",
        )
        self.assertEqual(
            report.issues[0].status,
            "WARNING",
        )

    def test_dosage_threshold(self):
        report = self.service.validate_medicine(
            medicine_name="Paracetamol",
            quantity=30,
            maximum_quantity=20,
        )

        self.assertFalse(report.is_valid)
        self.assertEqual(report.issue_count, 1)
        self.assertEqual(
            report.issues[0].rule,
            "dosage_threshold",
        )

    def test_quantity_mismatch(self):
        report = self.service.validate_medicine(
            medicine_name="Paracetamol",
            prescription_quantity=10,
            sale_quantity=15,
        )

        self.assertFalse(report.is_valid)
        self.assertEqual(report.issue_count, 1)
        self.assertEqual(
            report.issues[0].rule,
            "quantity_mismatch",
        )

    def test_multiple_validation_issues(self):
        report = self.service.validate_medicine(
            medicine_name="Alprazolam",
            expiry_date=date(2025, 1, 1),
            quantity=30,
            maximum_quantity=20,
            prescription_quantity=10,
            sale_quantity=15,
        )

        self.assertFalse(report.is_valid)
        self.assertEqual(report.issue_count, 4)


if __name__ == "__main__":
    unittest.main()