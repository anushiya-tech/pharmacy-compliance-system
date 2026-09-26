"""
Normalization constants, mapping dictionaries, and regex rules for prescription text.
"""

import re
from typing import Dict, Pattern, Set

# Standardized dosage form canonical mappings
DOSAGE_FORM_MAPPINGS: Dict[str, str] = {
    # Tablets
    "tab": "tablet",
    "tabs": "tablet",
    "tablet": "tablet",
    "tablets": "tablet",
    "caplet": "tablet",
    "caplets": "tablet",
    "pill": "tablet",
    "pills": "tablet",
    # Capsules
    "cap": "capsule",
    "caps": "capsule",
    "capsule": "capsule",
    "capsules": "capsule",
    # Liquid / Oral solutions
    "syr": "syrup",
    "syrup": "syrup",
    "syrups": "syrup",
    "susp": "suspension",
    "suspension": "suspension",
    "sol": "solution",
    "soln": "solution",
    "solution": "solution",
    "elixir": "solution",
    # Injectables
    "inj": "injection",
    "injection": "injection",
    "injections": "injection",
    "vial": "injection",
    "vials": "injection",
    "ampoule": "injection",
    "ampoules": "injection",
    # Topicals
    "crm": "cream",
    "cream": "cream",
    "creams": "cream",
    "oint": "ointment",
    "ointment": "ointment",
    "gel": "gel",
    "lotion": "lotion",
    # Others
    "drop": "drops",
    "drops": "drops",
    "spray": "spray",
    "inhaler": "inhaler",
    "inhalers": "inhaler",
    "puff": "inhaler",
    "puffs": "inhaler",
    "patch": "patch",
    "patches": "patch",
    "supp": "suppository",
    "suppository": "suppository",
}

# Unit canonical mappings
STRENGTH_UNIT_MAPPINGS: Dict[str, str] = {
    "mg": "mg",
    "milligram": "mg",
    "milligrams": "mg",
    "g": "g",
    "gm": "g",
    "gram": "g",
    "grams": "g",
    "mcg": "mcg",
    "ug": "mcg",
    "microgram": "mcg",
    "micrograms": "mcg",
    "ml": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
    "l": "l",
    "liter": "l",
    "iu": "iu",
    "units": "iu",
    "unit": "iu",
    "%": "%",
}

# Prefixes that indicate prescription line items but are not part of medicine name
LINE_PREFIX_PATTERN: Pattern[str] = re.compile(
    r"^(?:rx\b|rx[:.\s]+|#\s*\d+[:.\s]+|\d+[\.\)]\s+|[-*•]\s+)",
    re.IGNORECASE,
)

# Pattern to normalize glued numbers and units: e.g. "500MG" -> "500 mg", "10ml" -> "10 ml"
GLUED_UNIT_PATTERN: Pattern[str] = re.compile(
    r"(\d+(?:\.\d+)?)\s*(mg|ml|g|gm|mcg|ug|iu|%)\b",
    re.IGNORECASE,
)

# Common non-medicine header / clinical administrative keywords
ADMINISTRATIVE_LINE_INDICATORS: Set[str] = {
    "doctor",
    "dr.",
    "dr ",
    "prescriber",
    "physician",
    "patient",
    "dob",
    "d.o.b",
    "age",
    "gender",
    "sex",
    "date",
    "clinic",
    "hospital",
    "pharmacy",
    "address",
    "phone",
    "tel",
    "fax",
    "license",
    "lic",
    "dea",
    "npi",
    "signature",
    "refills",
    "refill",
}
