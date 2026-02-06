"""Validation rules for tax credits.

Checks eligibility requirements and AGI limits for the Child Tax Credit,
education credits (AOTC / LLC), and the Retirement Savings Credit.
"""

from __future__ import annotations

from datetime import date, datetime

from app.tax_engine.parameters import (
    AOTC_PHASE_OUT,
    LLC_PHASE_OUT,
    SAVERS_CREDIT_RATES,
)
from app.validation.models import ValidationIssue

# Child Tax Credit age limit: child must be under 17 at end of tax year.
_CTC_AGE_LIMIT = 17

# Tax year used for age calculations (default to current year).
_DEFAULT_TAX_YEAR = 2025


def validate_credits(
    return_data: dict,
    calculation_result: dict,
    taxpayer_data: dict,
) -> list[ValidationIssue]:
    """Validate eligibility for claimed tax credits."""
    issues: list[ValidationIssue] = []

    agi = float(calculation_result.get("agi", 0)) if calculation_result else 0
    filing_status = return_data.get("filing_status", "single")

    _check_child_tax_credit(return_data, agi, filing_status, issues)
    _check_education_credits(return_data, agi, filing_status, issues)
    _check_retirement_savings_credit(return_data, agi, filing_status, issues)

    return issues


# ------------------------------------------------------------------
# Child Tax Credit
# ------------------------------------------------------------------

def _parse_date(date_str: str | None) -> date | None:
    """Parse a date string in common formats, returning None on failure."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(str(date_str), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _age_at_end_of_year(dob: date, tax_year: int) -> int:
    """Calculate the age at the end of the given tax year (Dec 31)."""
    end_of_year = date(tax_year, 12, 31)
    age = end_of_year.year - dob.year
    if (end_of_year.month, end_of_year.day) < (dob.month, dob.day):
        age -= 1
    return age


def _check_child_tax_credit(
    return_data: dict,
    agi: float,
    filing_status: str,
    issues: list[ValidationIssue],
) -> None:
    dependents = return_data.get("dependents", [])
    if not dependents:
        return

    for idx, dep in enumerate(dependents):
        dob_str = dep.get("date_of_birth", "")
        dob = _parse_date(dob_str)
        prefix = f"dependents[{idx}]"

        if not dob:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="DEPENDENT_MISSING_DOB",
                    message=(
                        f"Dependent #{idx + 1} ({dep.get('first_name', 'Unknown')} "
                        f"{dep.get('last_name', '')}): Date of birth is missing. "
                        "Cannot determine Child Tax Credit eligibility."
                    ),
                    field=f"{prefix}.date_of_birth",
                    section="credits",
                )
            )
            continue

        age = _age_at_end_of_year(dob, _DEFAULT_TAX_YEAR)

        if age >= _CTC_AGE_LIMIT:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="CTC_CHILD_TOO_OLD",
                    message=(
                        f"Dependent #{idx + 1} ({dep.get('first_name', 'Unknown')} "
                        f"{dep.get('last_name', '')}): Age {age} at end of tax year. "
                        f"Child Tax Credit requires the child to be under {_CTC_AGE_LIMIT}. "
                        "They may still qualify for the $500 Other Dependents Credit."
                    ),
                    field=f"{prefix}.date_of_birth",
                    section="credits",
                )
            )


# ------------------------------------------------------------------
# Education credits (AOTC and LLC)
# ------------------------------------------------------------------

def _check_education_credits(
    return_data: dict,
    agi: float,
    filing_status: str,
    issues: list[ValidationIssue],
) -> None:
    # Education expenses are not part of the standard _build_return_data dict;
    # they may be present if the endpoint enriches return_data.
    education_expenses = return_data.get("education_expenses", [])
    if not education_expenses:
        return

    for idx, exp in enumerate(education_expenses):
        credit_type = exp.get("credit_type", "aotc")
        prefix = f"education_expenses[{idx}]"
        student_name = exp.get("student_name", f"Student #{idx + 1}")

        # Student must be at least half-time.
        is_half_time = exp.get("is_at_least_half_time", True)
        if not is_half_time:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="EDUCATION_NOT_HALF_TIME",
                    message=(
                        f"{student_name}: Student must be enrolled at least half-time "
                        "to claim education credits."
                    ),
                    field=f"{prefix}.is_at_least_half_time",
                    section="credits",
                )
            )

        # AOTC-specific checks.
        if credit_type == "aotc":
            is_first_four_years = exp.get("is_first_four_years", True)
            if not is_first_four_years:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="AOTC_BEYOND_FOUR_YEARS",
                        message=(
                            f"{student_name}: The American Opportunity Tax Credit is only "
                            "available for the first 4 years of post-secondary education."
                        ),
                        field=f"{prefix}.is_first_four_years",
                        section="credits",
                    )
                )

            has_felony = exp.get("has_felony_drug_conviction", False)
            if has_felony:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="AOTC_FELONY_DRUG_CONVICTION",
                        message=(
                            f"{student_name}: Students with a felony drug conviction "
                            "are not eligible for the AOTC."
                        ),
                        field=f"{prefix}.has_felony_drug_conviction",
                        section="credits",
                    )
                )

            # AGI phase-out check for AOTC.
            phase_out = AOTC_PHASE_OUT.get(filing_status, AOTC_PHASE_OUT["single"])
            if agi > phase_out[1]:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="AOTC_AGI_EXCEEDS_LIMIT",
                        message=(
                            f"{student_name}: AGI (${agi:,.2f}) exceeds the AOTC "
                            f"phase-out limit (${phase_out[1]:,}). No credit is available."
                        ),
                        field=f"{prefix}.credit_type",
                        section="credits",
                    )
                )
            elif agi > phase_out[0]:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="AOTC_AGI_PHASE_OUT",
                        message=(
                            f"{student_name}: AGI (${agi:,.2f}) is in the AOTC phase-out "
                            f"range (${phase_out[0]:,}-${phase_out[1]:,}). "
                            "The credit will be reduced."
                        ),
                        field=f"{prefix}.credit_type",
                        section="credits",
                    )
                )

        # LLC AGI phase-out check.
        if credit_type == "llc":
            phase_out = LLC_PHASE_OUT.get(filing_status, LLC_PHASE_OUT["single"])
            if agi > phase_out[1]:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="LLC_AGI_EXCEEDS_LIMIT",
                        message=(
                            f"{student_name}: AGI (${agi:,.2f}) exceeds the Lifetime "
                            f"Learning Credit phase-out limit (${phase_out[1]:,}). "
                            "No credit is available."
                        ),
                        field=f"{prefix}.credit_type",
                        section="credits",
                    )
                )
            elif agi > phase_out[0]:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="LLC_AGI_PHASE_OUT",
                        message=(
                            f"{student_name}: AGI (${agi:,.2f}) is in the LLC phase-out "
                            f"range (${phase_out[0]:,}-${phase_out[1]:,}). "
                            "The credit will be reduced."
                        ),
                        field=f"{prefix}.credit_type",
                        section="credits",
                    )
                )

        # Qualified expenses should be positive.
        expenses = float(exp.get("qualified_expenses", 0))
        if expenses <= 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="EDUCATION_NO_EXPENSES",
                    message=(
                        f"{student_name}: Qualified education expenses must be greater "
                        "than zero to claim an education credit."
                    ),
                    field=f"{prefix}.qualified_expenses",
                    section="credits",
                )
            )


# ------------------------------------------------------------------
# Retirement Savings Credit (Saver's Credit)
# ------------------------------------------------------------------

def _check_retirement_savings_credit(
    return_data: dict,
    agi: float,
    filing_status: str,
    issues: list[ValidationIssue],
) -> None:
    contributions = return_data.get("retirement_contributions", [])
    if not contributions:
        return

    # Determine the AGI limit for any credit at all.
    rates = SAVERS_CREDIT_RATES.get(filing_status, SAVERS_CREDIT_RATES["single"])
    # The last entry's upper limit is the AGI cutoff (credit rate drops to 0 above it).
    max_agi = rates[-1][1] if rates else 0

    total_contributions = 0.0
    for contrib in contributions:
        total_contributions += sum(
            float(contrib.get(field, 0))
            for field in [
                "traditional_ira",
                "roth_ira",
                "employer_401k",
                "employer_403b",
                "employer_457",
                "employer_tsp",
                "simple_ira",
            ]
        )

    if total_contributions <= 0:
        return

    if agi > max_agi:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="SAVERS_CREDIT_AGI_EXCEEDS_LIMIT",
                message=(
                    f"AGI (${agi:,.2f}) exceeds the Retirement Savings Credit limit "
                    f"(${max_agi:,} for {filing_status.replace('_', ' ')}). "
                    "No Saver's Credit is available."
                ),
                field="retirement_contributions",
                section="credits",
            )
        )
    else:
        # Determine which rate tier they fall into.
        credit_rate = 0.0
        for rate, limit in rates:
            if agi <= limit:
                credit_rate = rate
                break

        if credit_rate > 0:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="SAVERS_CREDIT_ELIGIBLE",
                    message=(
                        f"Eligible for the Retirement Savings Credit at a "
                        f"{credit_rate:.0%} rate based on AGI of ${agi:,.2f}."
                    ),
                    field="retirement_contributions",
                    section="credits",
                )
            )
