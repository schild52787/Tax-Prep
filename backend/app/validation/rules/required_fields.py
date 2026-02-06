"""Validation rules for required fields on a tax return.

Checks that all mandatory taxpayer information, filing status, and
income sources are present before the return can be filed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from app.validation.models import ValidationIssue


def validate_required_fields(
    return_data: dict,
    calculation_result: dict,
    taxpayer_data: dict,
) -> list[ValidationIssue]:
    """Check that all required fields are populated."""
    issues: list[ValidationIssue] = []

    _check_filing_status(return_data, issues)
    _check_primary_taxpayer(taxpayer_data, issues)
    _check_spouse_if_mfj(return_data, taxpayer_data, issues)
    _check_income_sources(return_data, issues)

    return issues


# ------------------------------------------------------------------
# Filing status
# ------------------------------------------------------------------

def _check_filing_status(return_data: dict, issues: list[ValidationIssue]) -> None:
    filing_status = return_data.get("filing_status")
    if not filing_status:
        issues.append(
            ValidationIssue(
                severity="error",
                code="MISSING_FILING_STATUS",
                message="Filing status is required.",
                field="filing_status",
                section="required_fields",
            )
        )


# ------------------------------------------------------------------
# Primary taxpayer
# ------------------------------------------------------------------

_REQUIRED_PRIMARY_FIELDS = {
    "first_name": "Primary taxpayer first name is required.",
    "last_name": "Primary taxpayer last name is required.",
    "ssn": "Primary taxpayer Social Security Number is required.",
}


def _check_primary_taxpayer(
    taxpayer_data: dict,
    issues: list[ValidationIssue],
) -> None:
    primary = taxpayer_data.get("primary", {})
    if not primary:
        issues.append(
            ValidationIssue(
                severity="error",
                code="MISSING_PRIMARY_TAXPAYER",
                message="Primary taxpayer information is required.",
                field="primary",
                section="required_fields",
            )
        )
        return

    for field_name, message in _REQUIRED_PRIMARY_FIELDS.items():
        value = primary.get(field_name)
        if not value or (isinstance(value, str) and not value.strip()):
            issues.append(
                ValidationIssue(
                    severity="error",
                    code=f"MISSING_{field_name.upper()}",
                    message=message,
                    field=f"primary.{field_name}",
                    section="required_fields",
                )
            )


# ------------------------------------------------------------------
# Spouse info required when filing MFJ
# ------------------------------------------------------------------

_REQUIRED_SPOUSE_FIELDS = {
    "first_name": "Spouse first name is required when filing jointly.",
    "last_name": "Spouse last name is required when filing jointly.",
    "ssn": "Spouse Social Security Number is required when filing jointly.",
}


def _check_spouse_if_mfj(
    return_data: dict,
    taxpayer_data: dict,
    issues: list[ValidationIssue],
) -> None:
    filing_status = return_data.get("filing_status", "")
    if filing_status != "married_filing_jointly":
        return

    spouse = taxpayer_data.get("spouse", {})
    if not spouse:
        issues.append(
            ValidationIssue(
                severity="error",
                code="MISSING_SPOUSE_INFO",
                message="Spouse information is required when filing Married Filing Jointly.",
                field="spouse",
                section="required_fields",
            )
        )
        return

    for field_name, message in _REQUIRED_SPOUSE_FIELDS.items():
        value = spouse.get(field_name)
        if not value or (isinstance(value, str) and not value.strip()):
            issues.append(
                ValidationIssue(
                    severity="error",
                    code=f"MISSING_SPOUSE_{field_name.upper()}",
                    message=message,
                    field=f"spouse.{field_name}",
                    section="required_fields",
                )
            )


# ------------------------------------------------------------------
# At least one income source
# ------------------------------------------------------------------

_INCOME_SOURCE_KEYS = [
    "w2_incomes",
    "interest_1099s",
    "dividend_1099s",
    "retirement_1099rs",
    "government_1099gs",
    "ssa_1099s",
    "capital_asset_sales",
]


def _check_income_sources(return_data: dict, issues: list[ValidationIssue]) -> None:
    has_any_income = any(
        len(return_data.get(key, [])) > 0 for key in _INCOME_SOURCE_KEYS
    )
    if not has_any_income:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="NO_INCOME_SOURCES",
                message=(
                    "No income sources have been entered. At least one income source "
                    "is typically required when filing a return."
                ),
                field=None,
                section="required_fields",
            )
        )
