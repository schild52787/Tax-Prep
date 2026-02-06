"""Tax Year 2025 parameters - brackets, limits, rates, and thresholds.

All values sourced from IRS Revenue Procedure and Tax Foundation projections
for tax year 2025 (returns filed in 2026).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TaxBracket:
    rate: float
    upper_limit: float  # Use float('inf') for the top bracket


# ============================================================
# STANDARD DEDUCTIONS
# ============================================================

STANDARD_DEDUCTION = {
    "single": 15_750,
    "married_filing_jointly": 31_500,
}

# Additional standard deduction for age 65+ or blind
ADDITIONAL_STANDARD_DEDUCTION = {
    "single": 2_000,
    "married_filing_jointly": 1_600,
}

# ============================================================
# ORDINARY INCOME TAX BRACKETS
# ============================================================

ORDINARY_TAX_BRACKETS = {
    "single": [
        TaxBracket(0.10, 11_925),
        TaxBracket(0.12, 48_475),
        TaxBracket(0.22, 103_350),
        TaxBracket(0.24, 197_300),
        TaxBracket(0.32, 250_525),
        TaxBracket(0.35, 626_350),
        TaxBracket(0.37, float("inf")),
    ],
    "married_filing_jointly": [
        TaxBracket(0.10, 23_850),
        TaxBracket(0.12, 96_950),
        TaxBracket(0.22, 206_700),
        TaxBracket(0.24, 394_600),
        TaxBracket(0.32, 501_050),
        TaxBracket(0.35, 751_600),
        TaxBracket(0.37, float("inf")),
    ],
}

# ============================================================
# LONG-TERM CAPITAL GAINS / QUALIFIED DIVIDENDS BRACKETS
# ============================================================

LTCG_TAX_BRACKETS = {
    "single": [
        TaxBracket(0.00, 48_350),
        TaxBracket(0.15, 533_400),
        TaxBracket(0.20, float("inf")),
    ],
    "married_filing_jointly": [
        TaxBracket(0.00, 96_700),
        TaxBracket(0.15, 600_050),
        TaxBracket(0.20, float("inf")),
    ],
}

# ============================================================
# SALT DEDUCTION CAP (State and Local Tax)
# ============================================================

SALT_CAP_BASE = 40_000  # Base cap for 2025
SALT_CAP_FLOOR = 10_000  # Floor (minimum cap)
SALT_PHASE_DOWN_THRESHOLD = {
    "single": 500_000,
    "married_filing_jointly": 500_000,
}
SALT_PHASE_DOWN_RATE = 0.30  # Cap reduces by 30% of MAGI over threshold

# ============================================================
# CHILD TAX CREDIT
# ============================================================

CHILD_TAX_CREDIT_AMOUNT = 2_200  # Per qualifying child under 17
CHILD_TAX_CREDIT_OTHER_DEPENDENT = 500  # Credit for other dependents
CHILD_TAX_CREDIT_REFUNDABLE_MAX = 1_700  # Max refundable (ACTC) per child
CHILD_TAX_CREDIT_REFUNDABLE_RATE = 0.15  # 15% of earned income over threshold
CHILD_TAX_CREDIT_EARNED_INCOME_THRESHOLD = 2_500

CHILD_TAX_CREDIT_PHASE_OUT = {
    "single": 200_000,
    "married_filing_jointly": 400_000,
}
CHILD_TAX_CREDIT_PHASE_OUT_RATE = 0.05  # $50 reduction per $1,000 over threshold

# ============================================================
# EDUCATION CREDITS
# ============================================================

# American Opportunity Tax Credit (AOTC)
AOTC_MAX_CREDIT = 2_500
AOTC_FULL_RATE_LIMIT = 2_000  # 100% of first $2,000
AOTC_PARTIAL_RATE_LIMIT = 2_000  # 25% of next $2,000
AOTC_REFUNDABLE_RATE = 0.40  # 40% is refundable
AOTC_PHASE_OUT = {
    "single": (80_000, 90_000),
    "married_filing_jointly": (160_000, 180_000),
}

# Lifetime Learning Credit (LLC)
LLC_MAX_CREDIT = 2_000
LLC_EXPENSE_LIMIT = 10_000
LLC_RATE = 0.20
LLC_PHASE_OUT = {
    "single": (80_000, 90_000),
    "married_filing_jointly": (160_000, 180_000),
}

# ============================================================
# RETIREMENT SAVINGS CREDIT (Form 8880)
# ============================================================

SAVERS_CREDIT_MAX_CONTRIBUTION = 2_000  # Per person
SAVERS_CREDIT_RATES = {
    "single": [
        (0.50, 23_750),
        (0.20, 25_750),
        (0.10, 39_500),
    ],
    "married_filing_jointly": [
        (0.50, 47_500),
        (0.20, 51_500),
        (0.10, 79_000),
    ],
}

# ============================================================
# CAPITAL GAINS
# ============================================================

CAPITAL_LOSS_LIMIT = 3_000  # Max deductible capital loss per year

# ============================================================
# SCHEDULE B
# ============================================================

SCHEDULE_B_THRESHOLD = 1_500  # Interest/dividend threshold requiring Schedule B

# ============================================================
# MEDICAL EXPENSES
# ============================================================

MEDICAL_EXPENSE_AGI_FLOOR = 0.075  # 7.5% of AGI

# ============================================================
# CHARITABLE CONTRIBUTIONS
# ============================================================

CHARITABLE_CASH_AGI_LIMIT = 0.60  # 60% of AGI for cash
CHARITABLE_NONCASH_AGI_LIMIT = 0.30  # 30% of AGI for noncash

# ============================================================
# SOCIAL SECURITY
# ============================================================

SS_WAGE_BASE = 176_100  # Social Security wage base for 2025
SS_TAX_RATE = 0.062  # Employee share
MEDICARE_TAX_RATE = 0.0145  # Employee share
ADDITIONAL_MEDICARE_TAX_RATE = 0.009  # Additional Medicare Tax
ADDITIONAL_MEDICARE_THRESHOLD = {
    "single": 200_000,
    "married_filing_jointly": 250_000,
}

# ============================================================
# EARNED INCOME CREDIT (EIC)
# ============================================================

# Simplified EIC parameters (full table is complex)
EIC_MAX_INVESTMENT_INCOME = 11_950
