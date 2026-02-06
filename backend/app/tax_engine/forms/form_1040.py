"""Form 1040 - U.S. Individual Income Tax Return.

This is the main tax form that aggregates data from all schedules.
"""

from app.tax_engine.forms.base import BaseTaxForm
from app.tax_engine.parameters import (
    ORDINARY_TAX_BRACKETS,
    STANDARD_DEDUCTION,
)
from app.tax_engine.worksheets.qualified_dividends import calculate_tax_with_qdcg


class Form1040(BaseTaxForm):
    form_id = "form_1040"
    dependencies = ["schedule_b", "schedule_d", "schedule_a"]

    def calculate(self, return_data: dict, other_forms: dict) -> None:
        filing_status = return_data.get("filing_status", "single")
        w2s = return_data.get("w2_incomes", [])
        schedule_b = other_forms.get("schedule_b")
        schedule_d = other_forms.get("schedule_d")
        schedule_a = other_forms.get("schedule_a")

        # ========================================
        # PAGE 1 - INCOME
        # ========================================

        # Line 1a: Wages, salaries, tips (from W-2 Box 1)
        total_wages = sum(float(w.get("box_1_wages", 0)) for w in w2s)
        self.set_line("line_1a", total_wages)
        self.set_line("line_1z", total_wages)

        # Line 2a: Tax-exempt interest
        tax_exempt_interest = schedule_b.get_line("tax_exempt_interest") if schedule_b else 0
        self.set_line("line_2a", tax_exempt_interest)

        # Line 2b: Taxable interest (from Schedule B)
        taxable_interest = schedule_b.get_line("line_4") if schedule_b else 0
        self.set_line("line_2b", taxable_interest)

        # Line 3a: Qualified dividends
        qualified_dividends = schedule_b.get_line("qualified_dividends") if schedule_b else 0
        self.set_line("line_3a", qualified_dividends)

        # Line 3b: Ordinary dividends (from Schedule B)
        ordinary_dividends = schedule_b.get_line("line_6") if schedule_b else 0
        self.set_line("line_3b", ordinary_dividends)

        # Line 4a/4b: IRA distributions
        retirement_1099rs = return_data.get("retirement_1099rs", [])
        ira_total = sum(float(r.get("box_1_gross_distribution", 0)) for r in retirement_1099rs)
        ira_taxable = sum(float(r.get("box_2a_taxable_amount", 0)) for r in retirement_1099rs)
        self.set_line("line_4a", ira_total)
        self.set_line("line_4b", ira_taxable)

        # Line 5a/5b: Pensions and annuities (included in 1099-R)
        # For simplicity, we combine with line 4
        self.set_line("line_5a", 0)
        self.set_line("line_5b", 0)

        # Line 6a/6b: Social Security benefits
        ssa_1099s = return_data.get("ssa_1099s", [])
        ss_total = sum(float(s.get("box_5_net_benefits", 0)) for s in ssa_1099s)
        ss_taxable = self._calculate_taxable_ss(ss_total, return_data)
        self.set_line("line_6a", ss_total)
        self.set_line("line_6b", ss_taxable)

        # Line 7: Capital gain or loss (from Schedule D)
        capital_gain_loss = schedule_d.get_line("line_21") if schedule_d else 0
        self.set_line("line_7", capital_gain_loss)

        # Line 8: Other income from Schedule 1
        # (Unemployment, state tax refunds, etc.)
        gov_1099gs = return_data.get("government_1099gs", [])
        unemployment = sum(float(g.get("box_1_unemployment", 0)) for g in gov_1099gs)
        self.set_line("line_8", unemployment)

        # Line 9: Total income
        total_income = (
            total_wages
            + taxable_interest
            + ordinary_dividends
            + ira_taxable
            + ss_taxable
            + capital_gain_loss
            + unemployment
        )
        self.set_line("line_9", total_income)

        # ========================================
        # ADJUSTMENTS TO INCOME
        # ========================================

        # Line 10: Adjustments from Schedule 1 Part II
        adjustments = 0  # Will be populated by Schedule 1
        self.set_line("line_10", adjustments)

        # Line 11: Adjusted Gross Income (AGI)
        agi = total_income - adjustments
        self.set_line("line_11", agi)

        # Store AGI in return_data for Schedule A's use
        return_data["agi"] = agi

        # ========================================
        # PAGE 2 - DEDUCTIONS & TAX
        # ========================================

        # Line 12: Standard deduction OR Itemized deductions
        standard = STANDARD_DEDUCTION.get(filing_status, 15_750)
        itemized = schedule_a.get_line("line_17") if schedule_a else 0

        if itemized > standard and return_data.get("itemized_deduction"):
            deduction = itemized
            deduction_method = "itemized"
        else:
            deduction = standard
            deduction_method = "standard"

        self.set_line("line_12", deduction)
        self.set_line("standard_deduction", standard)
        self.set_line("itemized_deduction", itemized)
        self.lines["deduction_method"] = deduction_method

        # Line 13: Qualified Business Income deduction (not in scope)
        self.set_line("line_13", 0)

        # Line 14: Total deductions
        total_deductions = deduction
        self.set_line("line_14", total_deductions)

        # Line 15: Taxable income
        taxable_income = max(0, agi - total_deductions)
        self.set_line("line_15", taxable_income)

        # ========================================
        # TAX CALCULATION
        # ========================================

        # Line 16: Tax
        net_lt_gain = schedule_d.get_line("net_lt_gain") if schedule_d else 0
        use_qdcg = qualified_dividends > 0 or net_lt_gain > 0

        if use_qdcg:
            tax = calculate_tax_with_qdcg(
                taxable_income, qualified_dividends, net_lt_gain, filing_status
            )
        else:
            tax = self._calculate_ordinary_tax(taxable_income, filing_status)

        self.set_line("line_16", tax)

        # Line 17: Additional taxes from Schedule 2 Part I (AMT, etc.)
        self.set_line("line_17", 0)

        # Line 18: Lines 16 + 17
        self.set_line("line_18", tax)

        # Line 19: Child tax credit (from Schedule 8812)
        ctc = 0
        schedule_8812 = other_forms.get("schedule_8812")
        if schedule_8812:
            ctc = schedule_8812.get_line("nonrefundable_ctc")
        self.set_line("line_19", ctc)

        # Line 20: Schedule 3 credits + line 19
        schedule_3_credits = 0
        schedule_3 = other_forms.get("schedule_3")
        if schedule_3:
            schedule_3_credits = schedule_3.get_line("line_8")
        total_credits = ctc + schedule_3_credits
        self.set_line("line_20", total_credits)

        # Line 21: Tax minus credits (not below zero)
        tax_after_credits = max(0, tax - total_credits)
        self.set_line("line_21", tax_after_credits)

        # Line 22: Other taxes from Schedule 2 Part II
        self.set_line("line_22", 0)

        # Line 23: Total tax
        # Line 24: Total tax
        total_tax = tax_after_credits
        self.set_line("line_23", total_tax)
        self.set_line("line_24", total_tax)

        # ========================================
        # PAYMENTS
        # ========================================

        # Line 25: Federal tax withheld
        w2_withheld = sum(float(w.get("box_2_fed_tax_withheld", 0)) for w in w2s)
        interest_div_withheld = schedule_b.get_line("fed_tax_withheld") if schedule_b else 0
        retirement_withheld = sum(
            float(r.get("box_4_fed_tax_withheld", 0)) for r in retirement_1099rs
        )
        gov_withheld = sum(
            float(g.get("box_4_fed_tax_withheld", 0)) for g in gov_1099gs
        )
        ss_withheld = sum(
            float(s.get("box_6_voluntary_withholding", 0)) for s in ssa_1099s
        )
        total_withheld = (
            w2_withheld + interest_div_withheld + retirement_withheld + gov_withheld + ss_withheld
        )
        self.set_line("line_25a", w2_withheld)
        self.set_line("line_25d", total_withheld)

        # Line 26: Estimated tax payments
        self.set_line("line_26", 0)

        # Line 27: Earned Income Credit
        self.set_line("line_27", 0)

        # Line 28: Additional child tax credit (refundable)
        actc = 0
        if schedule_8812:
            actc = schedule_8812.get_line("refundable_ctc")
        self.set_line("line_28", actc)

        # Line 29: American Opportunity Credit (refundable portion)
        refundable_aotc = 0
        schedule_3 = other_forms.get("schedule_3")
        if schedule_3:
            refundable_aotc = schedule_3.get_line("refundable_aotc")
        self.set_line("line_29", refundable_aotc)

        # Line 33: Total payments
        total_payments = total_withheld + actc + refundable_aotc
        self.set_line("line_33", total_payments)

        # ========================================
        # REFUND OR AMOUNT OWED
        # ========================================

        if total_payments > total_tax:
            refund = total_payments - total_tax
            self.set_line("line_34", refund)
            self.set_line("line_35a", refund)
            self.set_line("line_37", 0)
        else:
            owed = total_tax - total_payments
            self.set_line("line_34", 0)
            self.set_line("line_35a", 0)
            self.set_line("line_37", owed)

        # Effective tax rate
        if agi > 0:
            self.set_line("effective_rate", total_tax / agi)
        else:
            self.set_line("effective_rate", 0)

        # Marginal tax rate
        self.set_line("marginal_rate", self._get_marginal_rate(taxable_income, filing_status))

    def _calculate_ordinary_tax(self, taxable_income: float, filing_status: str) -> float:
        """Calculate tax using ordinary income brackets only."""
        brackets = ORDINARY_TAX_BRACKETS[filing_status]
        tax = 0
        prev_limit = 0
        for bracket in brackets:
            if taxable_income <= prev_limit:
                break
            taxable_in_bracket = min(taxable_income, bracket.upper_limit) - prev_limit
            if taxable_in_bracket > 0:
                tax += taxable_in_bracket * bracket.rate
            prev_limit = bracket.upper_limit
        return round(tax, 2)

    def _get_marginal_rate(self, taxable_income: float, filing_status: str) -> float:
        """Determine the marginal tax rate for the given taxable income."""
        brackets = ORDINARY_TAX_BRACKETS[filing_status]
        prev_limit = 0
        for bracket in brackets:
            if taxable_income <= bracket.upper_limit:
                return bracket.rate
            prev_limit = bracket.upper_limit
        return brackets[-1].rate

    def _calculate_taxable_ss(self, total_benefits: float, return_data: dict) -> float:
        """Calculate the taxable portion of Social Security benefits.

        Uses the provisional income method: up to 85% of benefits may be taxable.
        """
        if total_benefits <= 0:
            return 0

        # Simplified calculation - would need full provisional income calc
        # For now, use 85% as a conservative estimate
        # TODO: Implement full Social Security benefits worksheet
        return round(total_benefits * 0.85, 2)
