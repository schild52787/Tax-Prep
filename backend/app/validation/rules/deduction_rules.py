"""Validation rules for itemized deductions.

Enforces IRS limits and reasonableness checks for SALT, mortgage interest,
medical expenses, and charitable contributions.
"""

from __future__ import annotations

from app.tax_engine.parameters import (
    CHARITABLE_CASH_AGI_LIMIT,
    MEDICAL_EXPENSE_AGI_FLOOR,
    SALT_CAP_BASE,
)
from app.validation.models import ValidationIssue

# Threshold above which charitable giving triggers a warning (50% of AGI).
_CHARITABLE_WARNING_THRESHOLD = 0.50

# Maximum mortgage principal eligible for interest deduction (post-2017 loans).
_MORTGAGE_LOAN_LIMIT = 750_000


def validate_deductions(
    return_data: dict,
    calculation_result: dict,
    taxpayer_data: dict,
) -> list[ValidationIssue]:
    """Validate itemized deduction entries for limits and reasonableness."""
    issues: list[ValidationIssue] = []

    itemized = return_data.get("itemized_deduction")
    if not itemized:
        # No itemized deductions to validate.
        return issues

    agi = float(calculation_result.get("agi", 0)) if calculation_result else 0

    _check_salt_cap(itemized, issues)
    _check_mortgage_interest(itemized, issues)
    _check_medical_expenses(itemized, agi, issues)
    _check_charitable_contributions(itemized, agi, issues)

    return issues


# ------------------------------------------------------------------
# SALT deduction cap
# ------------------------------------------------------------------

def _check_salt_cap(itemized: dict, issues: list[ValidationIssue]) -> None:
    state_income_tax = float(itemized.get("state_income_tax_paid", 0))
    real_estate_tax = float(itemized.get("real_estate_tax_paid", 0))
    personal_property_tax = float(itemized.get("personal_property_tax", 0))

    total_salt = state_income_tax + real_estate_tax + personal_property_tax

    if total_salt > SALT_CAP_BASE:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="SALT_EXCEEDS_CAP",
                message=(
                    f"Total state and local tax deduction (${total_salt:,.2f}) exceeds "
                    f"the ${SALT_CAP_BASE:,} cap. The deduction will be limited to "
                    f"${SALT_CAP_BASE:,} (subject to phase-down rules)."
                ),
                field="itemized_deduction.salt_total",
                section="deductions",
            )
        )

    # Individual SALT components should not be negative.
    for field_name, label in [
        ("state_income_tax_paid", "State income tax"),
        ("real_estate_tax_paid", "Real estate tax"),
        ("personal_property_tax", "Personal property tax"),
    ]:
        value = float(itemized.get(field_name, 0))
        if value < 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code=f"NEGATIVE_{field_name.upper()}",
                    message=f"{label} cannot be negative (${value:,.2f}).",
                    field=f"itemized_deduction.{field_name}",
                    section="deductions",
                )
            )


# ------------------------------------------------------------------
# Mortgage interest
# ------------------------------------------------------------------

def _check_mortgage_interest(itemized: dict, issues: list[ValidationIssue]) -> None:
    mortgage_1098 = float(itemized.get("mortgage_interest_1098", 0))
    mortgage_not_1098 = float(itemized.get("mortgage_interest_not_1098", 0))
    mortgage_points = float(itemized.get("mortgage_points", 0))
    loan_amount = float(itemized.get("mortgage_loan_amount", 0))

    total_mortgage_interest = mortgage_1098 + mortgage_not_1098 + mortgage_points

    if total_mortgage_interest > 0 and loan_amount <= 0:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="MORTGAGE_INTEREST_NO_LOAN",
                message=(
                    "Mortgage interest deduction claimed but no loan amount provided. "
                    "The loan amount is needed to verify eligibility for the full deduction."
                ),
                field="itemized_deduction.mortgage_loan_amount",
                section="deductions",
            )
        )

    if loan_amount > _MORTGAGE_LOAN_LIMIT:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="MORTGAGE_LOAN_EXCEEDS_LIMIT",
                message=(
                    f"Mortgage loan amount (${loan_amount:,.2f}) exceeds the "
                    f"${_MORTGAGE_LOAN_LIMIT:,} limit for post-2017 loans. "
                    "Interest deduction may be limited."
                ),
                field="itemized_deduction.mortgage_loan_amount",
                section="deductions",
            )
        )

    # Interest should not be negative.
    if mortgage_1098 < 0:
        issues.append(
            ValidationIssue(
                severity="error",
                code="NEGATIVE_MORTGAGE_INTEREST",
                message=(
                    f"Mortgage interest (Form 1098) cannot be negative "
                    f"(${mortgage_1098:,.2f})."
                ),
                field="itemized_deduction.mortgage_interest_1098",
                section="deductions",
            )
        )

    # Reasonableness: interest should not exceed a high percentage of the loan.
    if loan_amount > 0 and mortgage_1098 > loan_amount * 0.15:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="MORTGAGE_INTEREST_HIGH_RATIO",
                message=(
                    f"Mortgage interest (${mortgage_1098:,.2f}) appears high relative "
                    f"to the loan amount (${loan_amount:,.2f}). Please verify."
                ),
                field="itemized_deduction.mortgage_interest_1098",
                section="deductions",
            )
        )


# ------------------------------------------------------------------
# Medical expenses (7.5% AGI floor)
# ------------------------------------------------------------------

def _check_medical_expenses(
    itemized: dict,
    agi: float,
    issues: list[ValidationIssue],
) -> None:
    medical = float(itemized.get("medical_expenses", 0))

    if medical < 0:
        issues.append(
            ValidationIssue(
                severity="error",
                code="NEGATIVE_MEDICAL_EXPENSES",
                message=f"Medical expenses cannot be negative (${medical:,.2f}).",
                field="itemized_deduction.medical_expenses",
                section="deductions",
            )
        )
        return

    if medical > 0 and agi > 0:
        floor = agi * MEDICAL_EXPENSE_AGI_FLOOR
        if medical <= floor:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="MEDICAL_BELOW_AGI_FLOOR",
                    message=(
                        f"Medical expenses (${medical:,.2f}) do not exceed the 7.5% "
                        f"AGI floor (${floor:,.2f}). No medical deduction will be allowed."
                    ),
                    field="itemized_deduction.medical_expenses",
                    section="deductions",
                )
            )


# ------------------------------------------------------------------
# Charitable contributions
# ------------------------------------------------------------------

def _check_charitable_contributions(
    itemized: dict,
    agi: float,
    issues: list[ValidationIssue],
) -> None:
    cash = float(itemized.get("cash_charitable", 0))
    noncash = float(itemized.get("noncash_charitable", 0))
    carryover = float(itemized.get("carryover_charitable", 0))
    total_charitable = cash + noncash + carryover

    # Negative values.
    for field_name, label, value in [
        ("cash_charitable", "Cash charitable contributions", cash),
        ("noncash_charitable", "Non-cash charitable contributions", noncash),
        ("carryover_charitable", "Charitable carryover", carryover),
    ]:
        if value < 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code=f"NEGATIVE_{field_name.upper()}",
                    message=f"{label} cannot be negative (${value:,.2f}).",
                    field=f"itemized_deduction.{field_name}",
                    section="deductions",
                )
            )

    if agi <= 0 or total_charitable <= 0:
        return

    # Reasonableness warning: charitable giving > 50% of AGI.
    charitable_pct = total_charitable / agi
    if charitable_pct > _CHARITABLE_WARNING_THRESHOLD:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="EXCESSIVE_CHARITABLE",
                message=(
                    f"Total charitable contributions (${total_charitable:,.2f}) exceed "
                    f"50% of AGI (${agi:,.2f}). This may trigger additional IRS scrutiny. "
                    "Ensure adequate documentation is available."
                ),
                field="itemized_deduction.charitable_total",
                section="deductions",
            )
        )

    # Cash charitable limited to 60% of AGI.
    if cash > agi * CHARITABLE_CASH_AGI_LIMIT:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="CASH_CHARITABLE_EXCEEDS_LIMIT",
                message=(
                    f"Cash charitable contributions (${cash:,.2f}) exceed the 60% of "
                    f"AGI limit (${agi * CHARITABLE_CASH_AGI_LIMIT:,.2f}). "
                    "The excess may need to be carried forward."
                ),
                field="itemized_deduction.cash_charitable",
                section="deductions",
            )
        )
