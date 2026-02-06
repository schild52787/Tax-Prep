"""Validation rules for income entries.

Checks reasonableness and consistency of W-2 wages, 1099-INT interest,
1099-DIV dividends, capital gains, and Social Security benefits.
"""

from __future__ import annotations

from app.validation.models import ValidationIssue

# Reasonableness thresholds.
_MAX_REASONABLE_WAGES = 10_000_000  # $10M -- flag for manual review
_MAX_REASONABLE_SS_BENEFITS = 60_000  # Annual max SS benefit (approx.)


def validate_income(
    return_data: dict,
    calculation_result: dict,
    taxpayer_data: dict,
) -> list[ValidationIssue]:
    """Validate all income entries for reasonableness and internal consistency."""
    issues: list[ValidationIssue] = []

    _check_w2_incomes(return_data, issues)
    _check_interest_1099s(return_data, issues)
    _check_dividend_1099s(return_data, issues)
    _check_capital_gains(return_data, issues)
    _check_ssa_benefits(return_data, issues)

    return issues


# ------------------------------------------------------------------
# W-2 wages
# ------------------------------------------------------------------

def _check_w2_incomes(return_data: dict, issues: list[ValidationIssue]) -> None:
    w2s = return_data.get("w2_incomes", [])
    for idx, w2 in enumerate(w2s):
        wages = float(w2.get("box_1_wages", 0))
        withheld = float(w2.get("box_2_fed_tax_withheld", 0))
        prefix = f"w2_incomes[{idx}]"

        # Wages should be positive if present.
        if wages < 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="W2_NEGATIVE_WAGES",
                    message=f"W-2 #{idx + 1}: Wages cannot be negative (${wages:,.2f}).",
                    field=f"{prefix}.box_1_wages",
                    section="income",
                )
            )
        elif wages == 0:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="W2_ZERO_WAGES",
                    message=(
                        f"W-2 #{idx + 1}: Wages are $0. Verify this is correct "
                        "or remove the W-2 if not needed."
                    ),
                    field=f"{prefix}.box_1_wages",
                    section="income",
                )
            )

        # Wages reasonableness check.
        if wages > _MAX_REASONABLE_WAGES:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="W2_EXCESSIVE_WAGES",
                    message=(
                        f"W-2 #{idx + 1}: Wages of ${wages:,.2f} are unusually high. "
                        "Please verify this amount."
                    ),
                    field=f"{prefix}.box_1_wages",
                    section="income",
                )
            )

        # Withholding should not exceed wages.
        if withheld < 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="W2_NEGATIVE_WITHHOLDING",
                    message=(
                        f"W-2 #{idx + 1}: Federal tax withheld cannot be negative "
                        f"(${withheld:,.2f})."
                    ),
                    field=f"{prefix}.box_2_fed_tax_withheld",
                    section="income",
                )
            )
        elif wages > 0 and withheld > wages:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="W2_WITHHOLDING_EXCEEDS_WAGES",
                    message=(
                        f"W-2 #{idx + 1}: Federal tax withheld (${withheld:,.2f}) "
                        f"exceeds wages (${wages:,.2f}). This is not possible."
                    ),
                    field=f"{prefix}.box_2_fed_tax_withheld",
                    section="income",
                )
            )


# ------------------------------------------------------------------
# 1099-INT interest
# ------------------------------------------------------------------

def _check_interest_1099s(return_data: dict, issues: list[ValidationIssue]) -> None:
    interest_forms = return_data.get("interest_1099s", [])
    for idx, form in enumerate(interest_forms):
        interest = float(form.get("box_1_interest", 0))
        prefix = f"interest_1099s[{idx}]"

        if interest < 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="INTEREST_NEGATIVE",
                    message=(
                        f"1099-INT #{idx + 1}: Interest amount cannot be negative "
                        f"(${interest:,.2f})."
                    ),
                    field=f"{prefix}.box_1_interest",
                    section="income",
                )
            )


# ------------------------------------------------------------------
# 1099-DIV dividends
# ------------------------------------------------------------------

def _check_dividend_1099s(return_data: dict, issues: list[ValidationIssue]) -> None:
    dividend_forms = return_data.get("dividend_1099s", [])
    for idx, form in enumerate(dividend_forms):
        ordinary = float(form.get("box_1a_ordinary_dividends", 0))
        qualified = float(form.get("box_1b_qualified_dividends", 0))
        prefix = f"dividend_1099s[{idx}]"

        if ordinary < 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="DIVIDEND_NEGATIVE_ORDINARY",
                    message=(
                        f"1099-DIV #{idx + 1}: Ordinary dividends cannot be negative "
                        f"(${ordinary:,.2f})."
                    ),
                    field=f"{prefix}.box_1a_ordinary_dividends",
                    section="income",
                )
            )

        if qualified < 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="DIVIDEND_NEGATIVE_QUALIFIED",
                    message=(
                        f"1099-DIV #{idx + 1}: Qualified dividends cannot be negative "
                        f"(${qualified:,.2f})."
                    ),
                    field=f"{prefix}.box_1b_qualified_dividends",
                    section="income",
                )
            )

        # Qualified dividends cannot exceed ordinary dividends.
        if qualified > ordinary and ordinary > 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="DIVIDEND_QUALIFIED_EXCEEDS_ORDINARY",
                    message=(
                        f"1099-DIV #{idx + 1}: Qualified dividends (${qualified:,.2f}) "
                        f"cannot exceed ordinary dividends (${ordinary:,.2f})."
                    ),
                    field=f"{prefix}.box_1b_qualified_dividends",
                    section="income",
                )
            )


# ------------------------------------------------------------------
# Capital gains (asset sales)
# ------------------------------------------------------------------

def _check_capital_gains(return_data: dict, issues: list[ValidationIssue]) -> None:
    sales = return_data.get("capital_asset_sales", [])
    for idx, sale in enumerate(sales):
        proceeds = float(sale.get("proceeds", 0))
        cost_basis = float(sale.get("cost_basis", 0))
        prefix = f"capital_asset_sales[{idx}]"

        if proceeds < 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="CAPITAL_GAIN_NEGATIVE_PROCEEDS",
                    message=(
                        f"Capital sale #{idx + 1}: Proceeds cannot be negative "
                        f"(${proceeds:,.2f})."
                    ),
                    field=f"{prefix}.proceeds",
                    section="income",
                )
            )

        if cost_basis < 0:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="CAPITAL_GAIN_NEGATIVE_BASIS",
                    message=(
                        f"Capital sale #{idx + 1}: Cost basis cannot be negative "
                        f"(${cost_basis:,.2f})."
                    ),
                    field=f"{prefix}.cost_basis",
                    section="income",
                )
            )

        # Proceeds of exactly $0 is unusual but possible (worthless securities).
        if proceeds == 0 and cost_basis > 0:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="CAPITAL_GAIN_ZERO_PROCEEDS",
                    message=(
                        f"Capital sale #{idx + 1}: Proceeds are $0 with a cost basis of "
                        f"${cost_basis:,.2f}. Verify this is a worthless security."
                    ),
                    field=f"{prefix}.proceeds",
                    section="income",
                )
            )


# ------------------------------------------------------------------
# Social Security benefits (SSA-1099)
# ------------------------------------------------------------------

def _check_ssa_benefits(return_data: dict, issues: list[ValidationIssue]) -> None:
    ssa_forms = return_data.get("ssa_1099s", [])
    for idx, form in enumerate(ssa_forms):
        net_benefits = float(form.get("box_5_net_benefits", 0))
        prefix = f"ssa_1099s[{idx}]"

        if net_benefits < 0:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="SSA_NEGATIVE_BENEFITS",
                    message=(
                        f"SSA-1099 #{idx + 1}: Net benefits are negative "
                        f"(${net_benefits:,.2f}). This may occur if benefits were "
                        "repaid but should be verified."
                    ),
                    field=f"{prefix}.box_5_net_benefits",
                    section="income",
                )
            )

        if net_benefits > _MAX_REASONABLE_SS_BENEFITS:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="SSA_EXCESSIVE_BENEFITS",
                    message=(
                        f"SSA-1099 #{idx + 1}: Net benefits of ${net_benefits:,.2f} "
                        f"exceed the typical annual maximum. Please verify."
                    ),
                    field=f"{prefix}.box_5_net_benefits",
                    section="income",
                )
            )
