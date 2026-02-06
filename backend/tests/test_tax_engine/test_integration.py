"""Integration tests for the tax calculation engine.

Tests complete tax return scenarios against known expected results.
"""

from app.tax_engine.engine import TaxEngine


def test_simple_single_w2_standard_deduction():
    """Single filer, one W-2 with $75,000 wages, standard deduction."""
    engine = TaxEngine()
    return_data = {
        "filing_status": "single",
        "w2_incomes": [
            {
                "box_1_wages": 75000,
                "box_2_fed_tax_withheld": 9500,
            }
        ],
        "interest_1099s": [],
        "dividend_1099s": [],
        "retirement_1099rs": [],
        "government_1099gs": [],
        "ssa_1099s": [],
        "capital_asset_sales": [],
        "itemized_deduction": None,
        "dependents": [],
    }

    result = engine.calculate(return_data)

    assert result["total_income"] == 75000
    assert result["agi"] == 75000
    assert result["deduction_method"] == "standard"

    # Standard deduction for single: $15,750
    # Taxable income: $75,000 - $15,750 = $59,250
    assert result["taxable_income"] == 59250

    # Tax calculation:
    # 10% on first $11,925 = $1,192.50
    # 12% on $11,926-$48,475 = $36,550 * 0.12 = $4,386.00
    # 22% on $48,476-$59,250 = $10,775 * 0.22 = $2,370.50
    # Total = $7,949.00
    expected_tax = 1192.50 + 4386.00 + 2370.50
    assert result["total_tax"] == expected_tax

    # Refund: $9,500 withheld - $7,949 tax = $1,551
    expected_refund = 9500 - expected_tax
    assert result["refund_amount"] == expected_refund
    assert result["amount_owed"] == 0


def test_mfj_two_w2s_standard_deduction():
    """MFJ filers, two W-2s totaling $150,000, standard deduction."""
    engine = TaxEngine()
    return_data = {
        "filing_status": "married_filing_jointly",
        "w2_incomes": [
            {"box_1_wages": 90000, "box_2_fed_tax_withheld": 12000},
            {"box_1_wages": 60000, "box_2_fed_tax_withheld": 7000},
        ],
        "interest_1099s": [],
        "dividend_1099s": [],
        "retirement_1099rs": [],
        "government_1099gs": [],
        "ssa_1099s": [],
        "capital_asset_sales": [],
        "itemized_deduction": None,
        "dependents": [],
    }

    result = engine.calculate(return_data)

    assert result["total_income"] == 150000
    assert result["agi"] == 150000

    # Standard deduction for MFJ: $31,500
    # Taxable income: $150,000 - $31,500 = $118,500
    assert result["taxable_income"] == 118500

    # Tax calculation for MFJ:
    # 10% on first $23,850 = $2,385.00
    # 12% on $23,851-$96,950 = $73,100 * 0.12 = $8,772.00
    # 22% on $96,951-$118,500 = $21,550 * 0.22 = $4,741.00
    # Total = $15,898.00
    expected_tax = 2385.00 + 8772.00 + 4741.00
    assert result["total_tax"] == expected_tax

    # Total withheld: $12,000 + $7,000 = $19,000
    # Refund: $19,000 - $15,898 = $3,102
    expected_refund = 19000 - expected_tax
    assert result["refund_amount"] == expected_refund


def test_single_w2_with_interest_and_dividends():
    """Single filer with W-2, interest income, and qualified dividends."""
    engine = TaxEngine()
    return_data = {
        "filing_status": "single",
        "w2_incomes": [
            {"box_1_wages": 60000, "box_2_fed_tax_withheld": 7500},
        ],
        "interest_1099s": [
            {"payer_name": "Bank A", "box_1_interest": 2000, "box_4_fed_tax_withheld": 0},
        ],
        "dividend_1099s": [
            {
                "payer_name": "Vanguard",
                "box_1a_ordinary_dividends": 3000,
                "box_1b_qualified_dividends": 2500,
                "box_4_fed_tax_withheld": 0,
            },
        ],
        "retirement_1099rs": [],
        "government_1099gs": [],
        "ssa_1099s": [],
        "capital_asset_sales": [],
        "itemized_deduction": None,
        "dependents": [],
    }

    result = engine.calculate(return_data)

    # Total income: $60,000 + $2,000 + $3,000 = $65,000
    assert result["total_income"] == 65000
    assert result["agi"] == 65000

    # Standard deduction: $15,750
    # Taxable income: $65,000 - $15,750 = $49,250
    assert result["taxable_income"] == 49250

    # With qualified dividends, the QDCG worksheet should produce lower tax
    # than ordinary rates alone
    assert result["total_tax"] > 0
    assert result["deduction_method"] == "standard"
    assert "schedule_b" in result["required_forms"]


def test_single_with_capital_gains():
    """Single filer with W-2 and capital gains."""
    engine = TaxEngine()
    return_data = {
        "filing_status": "single",
        "w2_incomes": [
            {"box_1_wages": 50000, "box_2_fed_tax_withheld": 6000},
        ],
        "interest_1099s": [],
        "dividend_1099s": [],
        "retirement_1099rs": [],
        "government_1099gs": [],
        "ssa_1099s": [],
        "capital_asset_sales": [
            {
                "description": "100 sh AAPL",
                "proceeds": 15000,
                "cost_basis": 10000,
                "holding_period": "long_term",
                "basis_reported_to_irs": True,
            },
            {
                "description": "50 sh TSLA",
                "proceeds": 5000,
                "cost_basis": 7000,
                "holding_period": "short_term",
                "basis_reported_to_irs": True,
            },
        ],
        "itemized_deduction": None,
        "dependents": [],
    }

    result = engine.calculate(return_data)

    # Capital gains: AAPL +$5,000 LT, TSLA -$2,000 ST
    # Net: $5,000 - $2,000 = $3,000
    # Total income: $50,000 + $3,000 = $53,000
    assert result["total_income"] == 53000

    # Should require Form 8949 and Schedule D
    assert "form_8949" in result["required_forms"]
    assert "schedule_d" in result["required_forms"]


def test_single_with_itemized_deductions():
    """Single filer where itemizing exceeds standard deduction."""
    engine = TaxEngine()
    return_data = {
        "filing_status": "single",
        "w2_incomes": [
            {"box_1_wages": 100000, "box_2_fed_tax_withheld": 15000},
        ],
        "interest_1099s": [],
        "dividend_1099s": [],
        "retirement_1099rs": [],
        "government_1099gs": [],
        "ssa_1099s": [],
        "capital_asset_sales": [],
        "itemized_deduction": {
            "medical_expenses": 0,
            "state_income_tax_paid": 8000,
            "real_estate_tax_paid": 6000,
            "personal_property_tax": 0,
            "mortgage_interest_1098": 12000,
            "mortgage_interest_not_1098": 0,
            "mortgage_points": 0,
            "investment_interest": 0,
            "cash_charitable": 5000,
            "noncash_charitable": 0,
            "carryover_charitable": 0,
            "casualty_loss": 0,
            "other_deductions": 0,
        },
        "dependents": [],
    }

    result = engine.calculate(return_data)

    # SALT: $8,000 + $6,000 = $14,000 (under $40,000 cap)
    # Mortgage interest: $12,000
    # Charitable: $5,000
    # Total itemized: $14,000 + $12,000 + $5,000 = $31,000
    # Standard deduction (single): $15,750
    # Itemized > Standard, so should use itemized
    assert result["deduction_method"] == "itemized"
    assert result["itemized_deduction_amount"] == 31000
    assert result["taxable_income"] == 100000 - 31000  # $69,000
    assert "schedule_a" in result["required_forms"]


def test_amount_owed_scenario():
    """Scenario where taxpayer owes money (insufficient withholding)."""
    engine = TaxEngine()
    return_data = {
        "filing_status": "single",
        "w2_incomes": [
            {"box_1_wages": 100000, "box_2_fed_tax_withheld": 5000},
        ],
        "interest_1099s": [],
        "dividend_1099s": [],
        "retirement_1099rs": [],
        "government_1099gs": [],
        "ssa_1099s": [],
        "capital_asset_sales": [],
        "itemized_deduction": None,
        "dependents": [],
    }

    result = engine.calculate(return_data)

    # With only $5,000 withheld on $100K income, should owe money
    assert result["amount_owed"] > 0
    assert result["refund_amount"] == 0
