"""Core validation engine for tax returns.

Runs all registered validation rule sets against return data and
produces a structured list of errors and warnings.
"""

from __future__ import annotations

from app.validation.models import ValidationIssue, ValidationResult
from app.validation.rules.credit_rules import validate_credits
from app.validation.rules.deduction_rules import validate_deductions
from app.validation.rules.income_rules import validate_income
from app.validation.rules.math_consistency import validate_math_consistency
from app.validation.rules.required_fields import validate_required_fields

# Re-export for convenience so callers can do:
#   from app.validation.validator import ValidationIssue, ValidationResult
__all__ = ["ReturnValidator", "ValidationIssue", "ValidationResult"]

# Registry of section names to their validation functions.
# Each function takes (return_data, calculation_result, taxpayer_data) and
# returns list[ValidationIssue].
_SECTION_VALIDATORS: dict[str, callable] = {
    "required_fields": validate_required_fields,
    "income": validate_income,
    "deductions": validate_deductions,
    "credits": validate_credits,
    "math_consistency": validate_math_consistency,
}


class ReturnValidator:
    """Runs validation rules against a tax return's data.

    Args:
        return_data: Dict in the same format as TaxEngine.calculate() input.
        calculation_result: Optional dict of calculation results (from TaxEngine).
            If provided, enables math consistency checks against computed values.
        taxpayer_data: Optional dict with taxpayer details (names, SSNs, etc.)
            keyed by role (``primary``, ``spouse``).
    """

    def __init__(
        self,
        return_data: dict,
        calculation_result: dict | None = None,
        taxpayer_data: dict | None = None,
    ) -> None:
        self.return_data = return_data
        self.calculation_result = calculation_result or {}
        self.taxpayer_data = taxpayer_data or {}

    def validate_all(self) -> ValidationResult:
        """Run every registered validation rule set and return aggregated results."""
        result = ValidationResult()
        for section_name in _SECTION_VALIDATORS:
            section_issues = self._run_section(section_name)
            result.issues.extend(section_issues)
        return result

    def validate_section(self, section_name: str) -> ValidationResult:
        """Run validation rules for a single section only.

        Args:
            section_name: One of 'required_fields', 'income', 'deductions',
                'credits', or 'math_consistency'.

        Raises:
            ValueError: If the section_name is not recognized.
        """
        if section_name not in _SECTION_VALIDATORS:
            raise ValueError(
                f"Unknown validation section '{section_name}'. "
                f"Valid sections: {list(_SECTION_VALIDATORS.keys())}"
            )
        result = ValidationResult()
        result.issues = self._run_section(section_name)
        return result

    def _run_section(self, section_name: str) -> list[ValidationIssue]:
        """Execute a single section's validator and return its issues."""
        validator_fn = _SECTION_VALIDATORS[section_name]
        return validator_fn(self.return_data, self.calculation_result, self.taxpayer_data)
