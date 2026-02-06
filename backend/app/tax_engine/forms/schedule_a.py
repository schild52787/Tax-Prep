"""Schedule A - Itemized Deductions."""

from app.tax_engine.forms.base import BaseTaxForm
from app.tax_engine.parameters import (
    MEDICAL_EXPENSE_AGI_FLOOR,
    SALT_CAP_BASE,
    SALT_CAP_FLOOR,
    SALT_PHASE_DOWN_RATE,
    SALT_PHASE_DOWN_THRESHOLD,
)


class ScheduleA(BaseTaxForm):
    form_id = "schedule_a"
    dependencies = []  # Needs AGI, but we handle this via 2-pass or pass AGI in return_data

    def calculate(self, return_data: dict, other_forms: dict) -> None:
        itemized = return_data.get("itemized_deduction", {})
        if not itemized:
            self.set_line("line_17", 0)
            return

        agi = float(return_data.get("agi", 0))
        filing_status = return_data.get("filing_status", "single")

        # Lines 1-4: Medical and Dental Expenses
        medical = float(itemized.get("medical_expenses", 0))
        medical_floor = agi * MEDICAL_EXPENSE_AGI_FLOOR
        medical_deduction = max(0, medical - medical_floor)
        self.set_line("line_1", medical)
        self.set_line("line_2", agi)
        self.set_line("line_3", medical_floor)
        self.set_line("line_4", medical_deduction)

        # Lines 5-7: State and Local Taxes (SALT)
        state_income_tax = float(itemized.get("state_income_tax_paid", 0))
        real_estate_tax = float(itemized.get("real_estate_tax_paid", 0))
        personal_property_tax = float(itemized.get("personal_property_tax", 0))
        total_salt = state_income_tax + real_estate_tax + personal_property_tax

        # Apply SALT cap with income-based phase-down
        salt_cap = self._calculate_salt_cap(agi, filing_status)
        salt_deduction = min(total_salt, salt_cap)
        self.set_line("line_5a", state_income_tax)
        self.set_line("line_5b", real_estate_tax)
        self.set_line("line_5c", personal_property_tax)
        self.set_line("line_5d", total_salt)
        self.set_line("line_5e", salt_deduction)
        self.set_line("line_7", salt_deduction)

        # Lines 8-10: Interest
        mortgage_1098 = float(itemized.get("mortgage_interest_1098", 0))
        mortgage_not_1098 = float(itemized.get("mortgage_interest_not_1098", 0))
        points = float(itemized.get("mortgage_points", 0))
        investment_interest = float(itemized.get("investment_interest", 0))
        total_interest = mortgage_1098 + mortgage_not_1098 + points + investment_interest
        self.set_line("line_8a", mortgage_1098)
        self.set_line("line_8b", mortgage_not_1098)
        self.set_line("line_8c", points)
        self.set_line("line_9", investment_interest)
        self.set_line("line_10", total_interest)

        # Lines 11-14: Charitable Contributions
        cash_charitable = float(itemized.get("cash_charitable", 0))
        noncash_charitable = float(itemized.get("noncash_charitable", 0))
        carryover = float(itemized.get("carryover_charitable", 0))
        total_charitable = cash_charitable + noncash_charitable + carryover
        self.set_line("line_11", cash_charitable)
        self.set_line("line_12", noncash_charitable)
        self.set_line("line_13", carryover)
        self.set_line("line_14", total_charitable)

        # Line 15: Casualty and Theft Losses
        casualty = float(itemized.get("casualty_loss", 0))
        self.set_line("line_15", casualty)

        # Line 16: Other Itemized Deductions
        other = float(itemized.get("other_deductions", 0))
        self.set_line("line_16", other)

        # Line 17: Total Itemized Deductions
        total = (
            medical_deduction
            + salt_deduction
            + total_interest
            + total_charitable
            + casualty
            + other
        )
        self.set_line("line_17", total)

    def _calculate_salt_cap(self, agi: float, filing_status: str) -> float:
        """Calculate the SALT deduction cap based on income phase-down."""
        threshold = SALT_PHASE_DOWN_THRESHOLD.get(filing_status, 500_000)
        if agi <= threshold:
            return SALT_CAP_BASE

        excess = agi - threshold
        reduction = excess * SALT_PHASE_DOWN_RATE
        cap = max(SALT_CAP_FLOOR, SALT_CAP_BASE - reduction)
        return cap
