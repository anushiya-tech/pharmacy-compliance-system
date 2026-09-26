"""
Unit and integration tests for prescription entity extraction and normalization.
Uses synthetic clinical data exclusively (zero real patient information).
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prescription_processing.extraction import (
    ExtractedMedicineItem,
    PrescriptionEntityExtractor,
    PrescriptionExtractionService,
)
from prescription_processing.normalization import (
    clean_ocr_noise,
    normalize_dosage_form,
    normalize_medicine_name,
    normalize_strength_unit,
)


class TestPrescriptionNormalization(unittest.TestCase):
    """Tests for the normalization layer (rules and normalizers)."""

    def test_clean_ocr_noise_glued_units(self):
        self.assertEqual(clean_ocr_noise("500MG"), "500 mg")
        self.assertEqual(clean_ocr_noise("10ML"), "10 ml")
        self.assertEqual(clean_ocr_noise("0.5G"), "0.5 g")

    def test_clean_ocr_noise_repeated_whitespace(self):
        text = "Amoxicillin    500 mg \t\t Capsule   "
        self.assertEqual(clean_ocr_noise(text), "Amoxicillin 500 mg Capsule")

    def test_normalize_dosage_forms(self):
        self.assertEqual(normalize_dosage_form("tab"), "tablet")
        self.assertEqual(normalize_dosage_form("Tabs"), "tablet")
        self.assertEqual(normalize_dosage_form("tablet"), "tablet")
        self.assertEqual(normalize_dosage_form("cap"), "capsule")
        self.assertEqual(normalize_dosage_form("CAPS"), "capsule")
        self.assertEqual(normalize_dosage_form("syr"), "syrup")
        self.assertEqual(normalize_dosage_form("inj"), "injection")
        self.assertEqual(normalize_dosage_form("crm"), "cream")
        self.assertIsNone(normalize_dosage_form(None))

    def test_normalize_strength_units(self):
        self.assertEqual(normalize_strength_unit("MG"), "mg")
        self.assertEqual(normalize_strength_unit("milligram"), "mg")
        self.assertEqual(normalize_strength_unit("mcg"), "mcg")
        self.assertEqual(normalize_strength_unit("UG"), "mcg")
        self.assertEqual(normalize_strength_unit("ml"), "ml")
        self.assertIsNone(normalize_strength_unit(None))

    def test_normalize_medicine_name(self):
        self.assertEqual(normalize_medicine_name("Amoxicillin 500MG Capsule"), "amoxicillin")
        self.assertEqual(normalize_medicine_name("  Rx: Cetirizine 10mg Tab. "), "cetirizine")
        self.assertEqual(normalize_medicine_name("1. Metformin 500 mg Tablet 30"), "metformin")
        self.assertEqual(normalize_medicine_name("Azithromycin 250 mg - 6 Tablets"), "azithromycin")


class TestPrescriptionEntityExtraction(unittest.TestCase):
    """Tests for entity extraction from prescription lines and blocks."""

    def setUp(self):
        self.extractor = PrescriptionEntityExtractor()

    def test_one_medicine_line(self):
        line = "Paracetamol 500 mg Tablet"
        result = self.extractor.extract(line)
        self.assertEqual(result.total_medicines_detected, 1)
        med = result.medicines[0]
        self.assertEqual(med.normalized_name, "paracetamol")
        self.assertEqual(med.strength_value, 500.0)
        self.assertEqual(med.strength_unit, "mg")
        self.assertEqual(med.dosage_form, "tablet")
        self.assertIsNone(med.quantity)

    def test_multiple_medicine_lines(self):
        text = (
            "Paracetamol 500 mg Tablet\n"
            "Amoxicillin 500mg Capsule\n"
            "Azithromycin 250 mg - 6 Tablets\n"
        )
        result = self.extractor.extract(text)
        self.assertEqual(result.total_medicines_detected, 3)
        names = [m.normalized_name for m in result.medicines]
        self.assertEqual(names, ["paracetamol", "amoxicillin", "azithromycin"])

    def test_strength_extraction_variations(self):
        cases = [
            ("DrugA 500 mg Tablet", 500.0, "mg"),
            ("DrugB 500mg Capsule", 500.0, "mg"),
            ("DrugC 500MG Tab", 500.0, "mg"),
            ("DrugD 250 mcg Tablet", 250.0, "mcg"),
            ("DrugE 0.5 g Tablet", 0.5, "g"),
            ("DrugF 10 ml Syrup", 10.0, "ml"),
        ]
        for line, exp_val, exp_unit in cases:
            res = self.extractor.extract(line)
            self.assertEqual(len(res.medicines), 1, f"Failed on: {line}")
            med = res.medicines[0]
            self.assertEqual(med.strength_value, exp_val, f"Strength val mismatch on: {line}")
            self.assertEqual(med.strength_unit, exp_unit, f"Strength unit mismatch on: {line}")

    def test_quantity_extraction(self):
        cases = [
            ("Azithromycin 250 mg - 6 Tablets", 6),
            ("Cetirizine 10mg Tab Qty 10", 10),
            ("Cetirizine 10mg Tab Qty: 20", 20),
            ("Metformin 500 mg Tablet 30", 30),
            ("Ibuprofen 400 mg Tab #60", 60),
            ("Amoxicillin 500mg Cap Disp: 15", 15),
        ]
        for line, expected_qty in cases:
            res = self.extractor.extract(line)
            self.assertEqual(len(res.medicines), 1, f"Failed on {line}")
            self.assertEqual(res.medicines[0].quantity, expected_qty, f"Qty mismatch on {line}")

    def test_dosage_form_extraction_and_abbreviations(self):
        cases = [
            ("Medicine Tab 10mg", "tablet"),
            ("Medicine Tabs 10mg", "tablet"),
            ("Medicine Cap 500mg", "capsule"),
            ("Medicine Caps 500mg", "capsule"),
            ("Medicine Syr 100ml", "syrup"),
            ("Medicine Inj 10ml", "injection"),
            ("Medicine Crm 30g", "cream"),
        ]
        for line, expected_form in cases:
            res = self.extractor.extract(line)
            self.assertEqual(len(res.medicines), 1, f"Failed for {line}")
            self.assertEqual(res.medicines[0].dosage_form, expected_form)

    def test_missing_quantity(self):
        line = "Amoxicillin 500mg Capsule"
        res = self.extractor.extract(line)
        self.assertEqual(len(res.medicines), 1)
        self.assertIsNone(res.medicines[0].quantity)

    def test_missing_strength(self):
        line = "Ibuprofen Tablet Qty 20"
        res = self.extractor.extract(line)
        self.assertEqual(len(res.medicines), 1)
        med = res.medicines[0]
        self.assertEqual(med.normalized_name, "ibuprofen")
        self.assertIsNone(med.strength_value)
        self.assertIsNone(med.strength_unit)
        self.assertEqual(med.dosage_form, "tablet")
        self.assertEqual(med.quantity, 20)

    def test_normalization_capitalization_and_spacing(self):
        line = "   AMOXICILLIN   500MG   CAPSULE   "
        res = self.extractor.extract(line)
        self.assertEqual(len(res.medicines), 1)
        med = res.medicines[0]
        self.assertEqual(med.normalized_name, "amoxicillin")
        self.assertEqual(med.strength_value, 500.0)
        self.assertEqual(med.strength_unit, "mg")
        self.assertEqual(med.dosage_form, "capsule")

    def test_noisy_ocr_spacing(self):
        line = "Cetirizine    10mg   Tab   Qty   10"
        res = self.extractor.extract(line)
        self.assertEqual(len(res.medicines), 1)
        med = res.medicines[0]
        self.assertEqual(med.normalized_name, "cetirizine")
        self.assertEqual(med.strength_value, 10.0)
        self.assertEqual(med.dosage_form, "tablet")
        self.assertEqual(med.quantity, 10)

    def test_lines_clearly_not_medicine_entries(self):
        administrative_text = (
            "City Health Clinic - Rx Department\n"
            "Prescriber: Dr. Emily Clark, MD (Lic #MD-12345)\n"
            "Patient: Anonymous Test Subject\n"
            "DOB: 1985-04-12\n"
            "Date: 2026-01-15\n"
            "Refills: 0\n"
            "Signature: Dr. E. Clark\n"
        )
        res = self.extractor.extract(administrative_text)
        self.assertEqual(res.total_medicines_detected, 0)
        self.assertEqual(len(res.medicines), 0)

    def test_multiple_medicines_in_one_prescription_with_headers(self):
        prescription_doc = (
            "Metro Health Clinic - Outpatient Rx\n"
            "Prescriber: Dr. Robert Davis, MD (Lic #MD-88123)\n"
            "Patient: Jane Smith (DOB: 1992-08-14)\n"
            "Date: 2026-02-20\n"
            "\n"
            "1. Amoxicillin 500mg Capsule\n"
            "   Sig: 1 capsule by mouth three times daily for 10 days\n"
            "   Disp: 30\n"
            "\n"
            "2. Paracetamol 500 mg Tablet\n"
            "   Sig: Take 1 tablet every 6 hours as needed for fever\n"
            "   Disp: 20\n"
            "\n"
            "3. Cetirizine 10mg Tab Qty 10\n"
            "   Sig: 1 tab daily at bedtime\n"
            "\n"
            "Refills: 0\n"
            "Signature: Dr. R. Davis\n"
        )
        service = PrescriptionExtractionService(extractor=self.extractor)
        result = service.extract_from_text(prescription_doc)

        self.assertEqual(result.total_medicines_detected, 3)

        # 1. Amoxicillin
        m1 = result.medicines[0]
        self.assertEqual(m1.normalized_name, "amoxicillin")
        self.assertEqual(m1.strength_value, 500.0)
        self.assertEqual(m1.strength_unit, "mg")
        self.assertEqual(m1.dosage_form, "capsule")
        self.assertEqual(m1.quantity, 30)
        self.assertIn("three times daily", m1.frequency)

        # 2. Paracetamol
        m2 = result.medicines[1]
        self.assertEqual(m2.normalized_name, "paracetamol")
        self.assertEqual(m2.strength_value, 500.0)
        self.assertEqual(m2.strength_unit, "mg")
        self.assertEqual(m2.dosage_form, "tablet")
        self.assertEqual(m2.quantity, 20)

        # 3. Cetirizine
        m3 = result.medicines[2]
        self.assertEqual(m3.normalized_name, "cetirizine")
        self.assertEqual(m3.strength_value, 10.0)
        self.assertEqual(m3.strength_unit, "mg")
        self.assertEqual(m3.dosage_form, "tablet")
        self.assertEqual(m3.quantity, 10)


if __name__ == "__main__":
    unittest.main()
