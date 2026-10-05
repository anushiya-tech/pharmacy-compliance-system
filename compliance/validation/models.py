from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationIssue:
    medicine_name: str
    rule: str
    status: str
    message: str


@dataclass
class ValidationReport:
    issues: list[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0

    @property
    def issue_count(self) -> int:
        return len(self.issues)