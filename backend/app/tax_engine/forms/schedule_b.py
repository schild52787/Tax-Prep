"""Schedule B - Interest and Ordinary Dividends.

Required when total taxable interest or ordinary dividends exceed $1,500.
"""

from app.tax_engine.forms.base import BaseTaxForm


class ScheduleB(BaseTaxForm):
    form_id = "schedule_b"
    dependencies = []

    def calculate(self, return_data: dict, other_forms: dict) -> None:
        interest_1099s = return_data.get("interest_1099s", [])
        dividend_1099s = return_data.get("dividend_1099s", [])

        # Part I - Interest (Lines 1-4)
        total_interest = sum(
            float(i.get("box_1_interest", 0)) for i in interest_1099s
        )
        self.set_line("line_1", total_interest)
        self.set_line("line_4", total_interest)  # Total Part I

        # Part II - Ordinary Dividends (Lines 5-6)
        total_ordinary_dividends = sum(
            float(d.get("box_1a_ordinary_dividends", 0)) for d in dividend_1099s
        )
        self.set_line("line_5", total_ordinary_dividends)
        self.set_line("line_6", total_ordinary_dividends)  # Total Part II

        # Track qualified dividends (not on Schedule B but needed by Form 1040)
        total_qualified_dividends = sum(
            float(d.get("box_1b_qualified_dividends", 0)) for d in dividend_1099s
        )
        self.set_line("qualified_dividends", total_qualified_dividends)

        # Track tax-exempt interest
        total_tax_exempt = sum(
            float(i.get("box_8_tax_exempt_interest", 0)) for i in interest_1099s
        )
        self.set_line("tax_exempt_interest", total_tax_exempt)

        # Track federal tax withheld from interest and dividends
        fed_withheld = sum(
            float(i.get("box_4_fed_tax_withheld", 0)) for i in interest_1099s
        ) + sum(
            float(d.get("box_4_fed_tax_withheld", 0)) for d in dividend_1099s
        )
        self.set_line("fed_tax_withheld", fed_withheld)
