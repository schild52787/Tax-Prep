"""Validation data models shared across the validation engine and all rule modules."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class ValidationIssue:
    """A single validation error or warning discovered during review."""

    severity: str  # "error" or "warning"
    code: str  # e.g. "MISSING_SSN", "EXCESSIVE_CHARITABLE"
    message: str
    field: str | None = None
    section: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ValidationResult:
    """Aggregated result of running all validation rules."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def is_valid(self) -> bool:
        """Return True if there are no errors (warnings are acceptable)."""
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [i.to_dict() for i in self.issues],
        }
