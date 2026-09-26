"""
Configurable regular expression patterns for prescription entity extraction.
"""

import re
from typing import Pattern

# Strength pattern: captures numeric value and unit
# e.g., '500 mg', '500mg', '250 mcg', '0.5 g', '10 ml', '100 mg/5ml'
STRENGTH_PATTERN: Pattern[str] = re.compile(
    r"\b(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mg(?:/5ml|/ml)?|ml|g|gm|mcg|ug|iu|%)\b",
    re.IGNORECASE,
)

# Dosage form pattern: captures common dosage forms and their abbreviations
DOSAGE_FORM_PATTERN: Pattern[str] = re.compile(
    r"\b(?P<form>tablets?|tabs?|capsules?|caps?|caplets?|syrups?|syrs?|suspensions?|susp?|"
    r"injections?|injs?|vials?|ampoules?|creams?|crms?|ointments?|oints?|gels?|lotions?|"
    r"solutions?|solns?|sol?|drops?|sprays?|inhalers?|puffs?|patches?|suppositor(?:y|ies)|supps?)\b",
    re.IGNORECASE,
)

# Quantity pattern: explicit quantity indicators
# e.g. 'Qty: 10', 'Qty 10', 'Quantity: 30', 'Disp: 30', 'Count: 60', '#30', 'x 30'
EXPLICIT_QUANTITY_PATTERN: Pattern[str] = re.compile(
    r"(?:\b(?:qty|quantity|disp(?:ense)?|count|pack|no\.?)\b|[#x])\s*[:.-]?\s*(?P<qty>\d+)\b",
    re.IGNORECASE,
)

# Quantity pattern when written as '- 6 Tablets' or '30 Tablets'
QUANTITY_WITH_FORM_PATTERN: Pattern[str] = re.compile(
    r"(?:^|[\s\-])(?P<qty>\d+)\s*(?:tablets?|tabs?|capsules?|caps?|pills?|bottles?|vials?)\b",
    re.IGNORECASE,
)

# Standalone count trailing at line end after a dosage form: e.g. 'Tablet 30'
TRAILING_COUNT_PATTERN: Pattern[str] = re.compile(
    r"(?:tablets?|tabs?|capsules?|caps?|pills?|syrup|injection|cream)\s+(?P<qty>\d+)\s*$",
    re.IGNORECASE,
)

# Frequency / administration instructions (Sig)
# e.g. 'Sig: 1 capsule by mouth three times daily', 'Take 1 tablet daily', 'twice daily'
FREQUENCY_EXPLICIT_PATTERN: Pattern[str] = re.compile(
    r"(?:sig|directions?|instructions?|use|take)\s*[:.-]?\s*(?P<freq>[^\n]+)",
    re.IGNORECASE,
)

FREQUENCY_INLINE_PATTERN: Pattern[str] = re.compile(
    r"\b(?P<freq>(?:take\s+)?(?:\d+\s+(?:tab|cap|tablet|capsule|pill)?s?\s+)?(?:by\s+mouth\s+)?"
    r"(?:once|twice|thrice|\d+\s+times|every\s+\d+\s+hours?|at\s+bedtime|as\s+needed)"
    r"(?:\s+(?:daily|a\s+day|per\s+day|with\s+meals?|before\s+meals?|after\s+meals?))?[^\n,;]*)",
    re.IGNORECASE,
)

# Header or administrative line indicators that should never be classified as medicines
NON_MEDICINE_PREFIX_PATTERN: Pattern[str] = re.compile(
    r"^(?:dr\.?|doctor|physician|prescriber|patient|name|dob|d\.o\.b|age|sex|gender|date|"
    r"clinic|hospital|pharmacy|address|phone|tel|fax|lic(?:ense)?|dea|npi|signature|refills?)\s*[:.-]",
    re.IGNORECASE,
)
