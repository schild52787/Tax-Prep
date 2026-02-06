"""Qualified Dividends and Capital Gain Tax Worksheet.

Used when the taxpayer has qualified dividends or net capital gain,
to apply the lower LTCG tax rates instead of ordinary rates.
"""

from app.tax_engine.parameters import LTCG_TAX_BRACKETS, ORDINARY_TAX_BRACKETS


def calculate_tax_with_qdcg(
    taxable_income: float,
    qualified_dividends: float,
    net_lt_capital_gain: float,
    filing_status: str,
) -> float:
    """Calculate tax using the Qualified Dividends and Capital Gain worksheet.

    This applies preferential rates (0%/15%/20%) to qualified dividends
    and net long-term capital gains, with the remainder taxed at ordinary rates.

    Returns the total tax amount.
    """
    if taxable_income <= 0:
        return 0

    # Line 1: Taxable income
    # Line 2: Qualified dividends
    # Line 3: Net capital gain from Schedule D line 15 (if positive)
    # Line 4: Add lines 2 and 3
    preferential_income = qualified_dividends + net_lt_capital_gain
    # Line 5: Cannot exceed taxable income
    preferential_income = min(preferential_income, taxable_income)

    # Line 6: Ordinary income (taxed at regular rates)
    ordinary_income = taxable_income - preferential_income

    # Calculate tax on ordinary income portion
    ordinary_tax = _calculate_bracket_tax(ordinary_income, filing_status, "ordinary")

    # Calculate tax on preferential income
    # The preferential income is "stacked" on top of ordinary income
    # for purposes of determining which LTCG bracket applies
    preferential_tax = _calculate_stacked_ltcg_tax(
        ordinary_income, preferential_income, filing_status
    )

    total = ordinary_tax + preferential_tax

    # Compare with tax computed entirely at ordinary rates
    # Use the LOWER of the two methods
    all_ordinary_tax = _calculate_bracket_tax(taxable_income, filing_status, "ordinary")

    return min(total, all_ordinary_tax)


def _calculate_bracket_tax(income: float, filing_status: str, bracket_type: str) -> float:
    """Calculate tax by applying progressive brackets."""
    if bracket_type == "ordinary":
        brackets = ORDINARY_TAX_BRACKETS[filing_status]
    else:
        brackets = LTCG_TAX_BRACKETS[filing_status]

    tax = 0
    prev_limit = 0
    for bracket in brackets:
        if income <= prev_limit:
            break
        taxable_in_bracket = min(income, bracket.upper_limit) - prev_limit
        if taxable_in_bracket > 0:
            tax += taxable_in_bracket * bracket.rate
        prev_limit = bracket.upper_limit

    return round(tax, 2)


def _calculate_stacked_ltcg_tax(
    ordinary_income: float, preferential_income: float, filing_status: str
) -> float:
    """Calculate LTCG tax on preferential income stacked above ordinary income."""
    brackets = LTCG_TAX_BRACKETS[filing_status]

    tax = 0
    # The preferential income starts at the top of ordinary income
    income_floor = ordinary_income
    remaining = preferential_income

    for bracket in brackets:
        if remaining <= 0:
            break
        if income_floor >= bracket.upper_limit:
            continue

        # How much room is left in this bracket
        room = bracket.upper_limit - income_floor
        taxable_in_bracket = min(remaining, room)
        tax += taxable_in_bracket * bracket.rate
        remaining -= taxable_in_bracket
        income_floor += taxable_in_bracket

    return round(tax, 2)
