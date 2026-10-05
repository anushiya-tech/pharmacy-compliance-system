"""
Compliance adapter bridging SQLAlchemy ORM models with Member 2's OCR,
Extraction, Normalization, Matching, and Validation services.
"""

import re
import os
import json
from typing import List, Optional, Tuple, Dict, Any

from compliance.matching.models import SaleItem, MatchingReport, MatchResult
from compliance.matching.service import MatchingService
from compliance.validation.models import ValidationReport, ValidationIssue
from compliance.validation.service import ComplianceValidationService
from prescription_processing.extraction.models import ExtractedMedicineItem, ExtractedPrescription
from prescription_processing.extraction.service import PrescriptionExtractionService
from prescription_processing.normalization.normalizer import MedicineNormalizer
from backend.models import Transaction, Prescription, TransactionItem, Medicine
from backend.schemas import (
    ComplianceCheckResponse,
    MatchedItemResponse,
    MissingItemResponse,
    QuantityMismatchResponse,
    ExtraItemResponse,
    ValidationIssueResponse,
)


class ComplianceAdapter:
    """
    Adapter orchestrating compliance analysis between backend database records
    and Member 2's core matching and validation engines.
    """

    def __init__(self):
        self.matching_service = MatchingService()
        self.validation_service = ComplianceValidationService()
        self.extraction_service = PrescriptionExtractionService()
        self.normalizer = MedicineNormalizer()

    def parse_strength(self, strength_str: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
        """
        Parse strength string such as '500 mg' or '10ml' into (numeric_value, unit).
        """
        if not strength_str:
            return None, None
        
        match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)", strength_str.strip())
        if match:
            val = float(match.group(1))
            unit = self.normalizer.normalize_strength_unit(match.group(2))
            return val, unit
        return None, None

    def transaction_item_to_sale_item(self, item: TransactionItem) -> SaleItem:
        """
        Convert a database TransactionItem entity into Member 2's SaleItem dataclass.
        """
        norm_name = self.normalizer.normalize_name(item.medicine_name)
        val, unit = self.parse_strength(item.strength)
        
        dosage_form = None
        if hasattr(item, "medicine") and item.medicine and item.medicine.dosage_form:
            dosage_form = self.normalizer.normalize_dosage_form(item.medicine.dosage_form)

        return SaleItem(
            medicine_name=item.medicine_name,
            normalized_name=norm_name,
            strength_value=val,
            strength_unit=unit,
            dosage_form=dosage_form,
            quantity=item.quantity,
        )

    def extract_prescription_items(self, prescription: Optional[Prescription]) -> List[ExtractedMedicineItem]:
        """
        Extract structured prescription items from the database Prescription record.
        Uses OCR text if present, otherwise attempts image processing if file exists.
        """
        if prescription is None:
            return []

        # 1. If prescription already has extracted_text, parse directly
        if prescription.extracted_text and prescription.extracted_text.strip():
            extracted_rx = self.extraction_service.extract_from_text(prescription.extracted_text)
            return extracted_rx.medicines

        # 2. If image_path exists and file is available, run OCR + extraction pipeline
        if prescription.image_path and os.path.isfile(prescription.image_path):
            try:
                extracted_rx = self.extraction_service.extract_from_image(prescription.image_path)
                return extracted_rx.medicines
            except Exception:
                pass

        return []

    def evaluate_compliance(
        self,
        transaction: Transaction,
        prescription: Optional[Prescription] = None,
    ) -> ComplianceCheckResponse:
        """
        Run full compliance verification for a given Transaction and optional Prescription.
        """
        sale_items = [self.transaction_item_to_sale_item(item) for item in transaction.items]
        prescription_items = self.extract_prescription_items(prescription)

        # 1. Run Prescription-Sale Matching
        matching_report = self.matching_service.match_prescription(
            prescription_items=prescription_items,
            sale_items=sale_items,
        )

        # 2. Run Regulatory & Clinical Validation for each sold item
        all_validation_issues: List[ValidationIssue] = []
        for item in transaction.items:
            med_expiry = None
            if hasattr(item, "medicine") and item.medicine:
                med_expiry = item.medicine.expiry_date

            # Find matching prescribed qty if available
            prescribed_qty = None
            for p_item in prescription_items:
                if self.normalizer.normalize_name(p_item.medicine_name) == self.normalizer.normalize_name(item.medicine_name):
                    prescribed_qty = p_item.quantity
                    break

            val_report = self.validation_service.validate_medicine(
                medicine_name=item.medicine_name,
                expiry_date=med_expiry,
                quantity=item.quantity,
                maximum_quantity=100,  # default dosage ceiling
                prescription_quantity=prescribed_qty,
                sale_quantity=item.quantity,
            )
            if not val_report.is_valid:
                all_validation_issues.extend(val_report.issues)

        # 3. Structure matched items
        matched_responses: List[MatchedItemResponse] = []
        for m in matching_report.matched_items:
            matched_responses.append(
                MatchedItemResponse(
                    medicine=m.prescription_medicine,
                    prescribed_quantity=m.prescription_quantity,
                    sold_quantity=m.sale_quantity,
                    status="COVERED",
                    reason=m.reason,
                )
            )

        # 4. Structure missing items (on prescription but not sold)
        missing_responses: List[MissingItemResponse] = []
        for m in matching_report.missing_items:
            missing_responses.append(
                MissingItemResponse(
                    medicine=m.prescription_medicine,
                    prescribed_quantity=m.prescription_quantity,
                    status="MISSING",
                    reason=m.reason,
                )
            )

        # 5. Structure quantity mismatches
        mismatch_responses: List[QuantityMismatchResponse] = []
        for m in matching_report.quantity_mismatches:
            mismatch_responses.append(
                QuantityMismatchResponse(
                    medicine=m.prescription_medicine,
                    prescribed_quantity=m.prescription_quantity,
                    sold_quantity=m.sale_quantity,
                    quantity_difference=m.quantity_difference,
                    status="QUANTITY_MISMATCH",
                    reason=m.reason,
                )
            )

        # 6. Structure extra / uncovered items (sold without prescription coverage)
        uncovered_responses: List[ExtraItemResponse] = []
        for extra in matching_report.extra_items:
            str_display = f"{extra.strength_value} {extra.strength_unit}".strip() if extra.strength_value else None
            uncovered_responses.append(
                ExtraItemResponse(
                    medicine=extra.medicine_name,
                    strength=str_display,
                    quantity=extra.quantity,
                    status="NOT_COVERED",
                    reason="Medicine sold without matching prescription coverage.",
                )
            )

        # 7. Structure validation issues
        issue_responses: List[ValidationIssueResponse] = []
        has_fail_issue = False
        for issue in all_validation_issues:
            if issue.status == "FAIL":
                has_fail_issue = True
            issue_responses.append(
                ValidationIssueResponse(
                    medicine_name=issue.medicine_name,
                    rule=issue.rule,
                    status=issue.status,
                    message=issue.message,
                )
            )

        # 8. Determine Overall Status & Compliance
        is_compliant = matching_report.is_compliant and not has_fail_issue
        if not prescription_items and sale_items:
            # Over-the-counter or transaction without prescription
            if has_fail_issue:
                overall_status = "FLAGGED"
            elif any(issue.status == "WARNING" for issue in all_validation_issues):
                overall_status = "REVIEW_REQUIRED"
            else:
                overall_status = "RECORDED"
        else:
            if has_fail_issue:
                overall_status = "FLAGGED"
            elif not matching_report.is_compliant or issue_responses:
                overall_status = "REVIEW_REQUIRED"
            else:
                overall_status = "COMPLIANT"

        # 9. Summary text
        summary_parts = []
        if is_compliant:
            summary_parts.append("All sale items match prescription requirements and pass compliance validation.")
        else:
            if uncovered_responses:
                summary_parts.append(f"{len(uncovered_responses)} item(s) sold without prescription coverage.")
            if missing_responses:
                summary_parts.append(f"{len(missing_responses)} prescribed item(s) not dispensed.")
            if mismatch_responses:
                summary_parts.append(f"{len(mismatch_responses)} item(s) have quantity mismatches.")
            if issue_responses:
                summary_parts.append(f"{len(issue_responses)} clinical/regulatory validation rule issue(s) detected.")

        summary = " ".join(summary_parts) if summary_parts else "Compliance analysis complete."

        return ComplianceCheckResponse(
            transaction_id=transaction.transaction_id,
            prescription_id=transaction.prescription_id,
            is_compliant=is_compliant,
            status=overall_status,
            matched_items=matched_responses,
            missing_items=missing_responses,
            quantity_mismatches=mismatch_responses,
            uncovered_items=uncovered_responses,
            validation_issues=issue_responses,
            summary=summary,
        )


compliance_adapter = ComplianceAdapter()
