"""Validation rules for mathematical consistency across the return.

Compares the raw input data against the computed calculation result to ensure
that totals, subtotals, and balances reconcile correctly.
"""

from __future__ import annotations

from app.validation.models import ValidationIssue

# Tolerance for floating-point comparison (one cent).
_TOLERANCE = 0.01


def validate_math_consistency(
    return_data: dict,
    calculation_result: dict,
    taxpayer_data: dict,
) -> list[ValidationIssue]:
    """Check that calculated values are internally consistent."""
    issues: list[ValidationIssue] = []

    if not calculation_result:
        # Nothing to cross-check without a calculation result.
        return issues

    _check_total_income(return_data, calculation_result, issues)
    _check_agi(calculation_result, issues)
    _check_taxable_income(calculation_result, issues)
    _check_withholding_totals(return_data, calculation_result, issues)
    _check_refund_or_owed(calculation_result, issues)

    return issues


# ------------------------------------------------------------------
# Total income = sum of all income sources
# ------------------------------------------------------------------

def _check_total_income(
    return_data: dict,
    calculation_result: dict,
    issues: list[ValidationIssue],
) -> None:
    reported_total = float(calculation_result.get("total_income", 0))

    # Sum up all income sources from input data, mirroring Form1040 logic.
    w2s = return_data.get("w2_incomes", [])
    wages = sum(float(w.get("box_1_wages", 0)) for w in w2s)

    interest_1099s = return_data.get("interest_1099s", [])
    taxable_interest = sum(float(i.get("box_1_interest", 0)) for i in interest_1099s)

    dividend_1099s = return_data.get("dividend_1099s", [])
    ordinary_dividends = sum(
        float(d.get("box_1a_ordinary_dividends", 0)) for d in dividend_1099s
    )

    retirement_1099rs = return_data.get("retirement_1099rs", [])
    retirement_taxable = sum(
        float(r.get("box_2a_taxable_amount", 0)) for r in retirement_1099rs
    )

    ssa_1099s = return_data.get("ssa_1099s", [])
    ss_benefits = sum(float(s.get("box_5_net_benefits", 0)) for s in ssa_1099s)
    # Social Security taxable portion is up to 85% -- use calculation result
    # form data if available, otherwise estimate.
    form_results = calculation_result.get("form_results", {})
    form_1040_lines = form_results.get("form_1040", {})
    ss_taxable = float(form_1040_lines.get("line_6b", ss_benefits * 0.85))

    # Capital gains come from Schedule D -- use the engine's computed value.
    capital_gain_loss = float(form_1040_lines.get("line_7", 0))

    gov_1099gs = return_data.get("government_1099gs", [])
    unemployment = sum(float(g.get("box_1_unemployment", 0)) for g in gov_1099gs)

    computed_total = (
        wages
        + taxable_interest
        + ordinary_dividends
        + retirement_taxable
        + ss_taxable
        + capital_gain_loss
        + unemployment
    )

    if abs(reported_total - computed_total) > _TOLERANCE:
        issues.append(
            ValidationIssue(
                severity="error",
                code="TOTAL_INCOME_MISMATCH",
                message=(
                    f"Total income (${reported_total:,.2f}) does not equal "
                    f"the sum of all income sources (${computed_total:,.2f})."
                ),
                field="total_income",
                section="math_consistency",
            )
        )


# ------------------------------------------------------------------
# AGI = total_income - adjustments
# ------------------------------------------------------------------

def _check_agi(
    calculation_result: dict,
    issues: list[ValidationIssue],
) -> None:
    total_income = float(calculation_result.get("total_income", 0))
    agi = float(calculation_result.get("agi", 0))

    form_results = calculation_result.get("form_results", {})
    form_1040_lines = form_results.get("form_1040", {})
    adjustments = float(form_1040_lines.get("line_10", 0))

    expected_agi = total_income - adjustments
    if abs(agi - expected_agi) > _TOLERANCE:
        issues.append(
            ValidationIssue(
                severity="error",
                code="AGI_MISMATCH",
                message=(
                    f"AGI (${agi:,.2f}) does not equal total income "
                    f"(${total_income:,.2f}) minus adjustments (${adjustments:,.2f}). "
                    f"Expected ${expected_agi:,.2f}."
                ),
                field="agi",
                section="math_consistency",
            )
        )


# ------------------------------------------------------------------
# Taxable income = AGI - deductions
# ------------------------------------------------------------------

def _check_taxable_income(
    calculation_result: dict,
    issues: list[ValidationIssue],
) -> None:
    agi = float(calculation_result.get("agi", 0))
    taxable_income = float(calculation_result.get("taxable_income", 0))

    deduction_method = calculation_result.get("deduction_method", "standard")
    if deduction_method == "itemized":
        deduction_amount = float(calculation_result.get("itemized_deduction_amount", 0))
    else:
        deduction_amount = float(calculation_result.get("standard_deduction_amount", 0))

    expected_taxable = max(0, agi - deduction_amount)
    if abs(taxable_income - expected_taxable) > _TOLERANCE:
        issues.append(
            ValidationIssue(
                severity="error",
                code="TAXABLE_INCOME_MISMATCH",
                message=(
                    f"Taxable income (${taxable_income:,.2f}) does not equal "
                    f"AGI (${agi:,.2f}) minus {deduction_method} deduction "
                    f"(${deduction_amount:,.2f}). Expected ${expected_taxable:,.2f}."
                ),
                field="taxable_income",
                section="math_consistency",
            )
        )


# ------------------------------------------------------------------
# Withholding totals across all forms
# ------------------------------------------------------------------

def _check_withholding_totals(
    return_data: dict,
    calculation_result: dict,
    issues: list[ValidationIssue],
) -> None:
    form_results = calculation_result.get("form_results", {})
    form_1040_lines = form_results.get("form_1040", {})
    reported_withheld = float(form_1040_lines.get("line_25d", 0))

    # Compute expected withholding from all input forms.
    w2s = return_data.get("w2_incomes", [])
    w2_withheld = sum(float(w.get("box_2_fed_tax_withheld", 0)) for w in w2s)

    interest_1099s = return_data.get("interest_1099s", [])
    interest_withheld = sum(float(i.get("box_4_fed_tax_withheld", 0)) for i in interest_1099s)

    dividend_1099s = return_data.get("dividend_1099s", [])
    dividend_withheld = sum(float(d.get("box_4_fed_tax_withheld", 0)) for d in dividend_1099s)

    retirement_1099rs = return_data.get("retirement_1099rs", [])
    retirement_withheld = sum(
        float(r.get("box_4_fed_tax_withheld", 0)) for r in retirement_1099rs
    )

    gov_1099gs = return_data.get("government_1099gs", [])
    gov_withheld = sum(float(g.get("box_4_fed_tax_withheld", 0)) for g in gov_1099gs)

    ssa_1099s = return_data.get("ssa_1099s", [])
    ss_withheld = sum(float(s.get("box_6_voluntary_withholding", 0)) for s in ssa_1099s)

    computed_withheld = (
        w2_withheld
        + interest_withheld
        + dividend_withheld
        + retirement_withheld
        + gov_withheld
        + ss_withheld
    )

    if abs(reported_withheld - computed_withheld) > _TOLERANCE:
        issues.append(
            ValidationIssue(
                severity="error",
                code="WITHHOLDING_MISMATCH",
                message=(
                    f"Total federal tax withheld on Form 1040 line 25d "
                    f"(${reported_withheld:,.2f}) does not match the sum of "
                    f"withholding from all input forms (${computed_withheld:,.2f})."
                ),
                field="total_payments",
                section="math_consistency",
            )
        )


# ------------------------------------------------------------------
# Refund / amount owed = total_payments - total_tax
# ------------------------------------------------------------------

def _check_refund_or_owed(
    calculation_result: dict,
    issues: list[ValidationIssue],
) -> None:
    total_payments = float(calculation_result.get("total_payments", 0))
    total_tax = float(calculation_result.get("total_tax", 0))
    refund = float(calculation_result.get("refund_amount", 0))
    owed = float(calculation_result.get("amount_owed", 0))

    if total_payments >= total_tax:
        expected_refund = total_payments - total_tax
        if abs(refund - expected_refund) > _TOLERANCE:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="REFUND_MISMATCH",
                    message=(
                        f"Refund amount (${refund:,.2f}) does not equal "
                        f"total payments (${total_payments:,.2f}) minus "
                        f"total tax (${total_tax:,.2f}). "
                        f"Expected ${expected_refund:,.2f}."
                    ),
                    field="refund_amount",
                    section="math_consistency",
                )
            )
        if owed > _TOLERANCE:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="REFUND_AND_OWED_CONFLICT",
                    message=(
                        "Both a refund and amount owed are present. "
                        "Only one should be non-zero."
                    ),
                    field="amount_owed",
                    section="math_consistency",
                )
            )
    else:
        expected_owed = total_tax - total_payments
        if abs(owed - expected_owed) > _TOLERANCE:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="AMOUNT_OWED_MISMATCH",
                    message=(
                        f"Amount owed (${owed:,.2f}) does not equal "
                        f"total tax (${total_tax:,.2f}) minus "
                        f"total payments (${total_payments:,.2f}). "
                        f"Expected ${expected_owed:,.2f}."
                    ),
                    field="amount_owed",
                    section="math_consistency",
                )
            )
        if refund > _TOLERANCE:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="REFUND_AND_OWED_CONFLICT",
                    message=(
                        "Both a refund and amount owed are present. "
                        "Only one should be non-zero."
                    ),
                    field="refund_amount",
                    section="math_consistency",
                )
            )
