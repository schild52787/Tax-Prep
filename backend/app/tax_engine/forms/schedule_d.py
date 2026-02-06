"""Schedule D - Capital Gains and Losses.

Summarizes capital gains/losses from Form 8949 and 1099-DIV distributions.
"""

from app.tax_engine.forms.base import BaseTaxForm
from app.tax_engine.parameters import CAPITAL_LOSS_LIMIT


class ScheduleD(BaseTaxForm):
    form_id = "schedule_d"
    dependencies = ["form_8949"]

    def calculate(self, return_data: dict, other_forms: dict) -> None:
        f8949 = other_forms.get("form_8949")
        dividend_1099s = return_data.get("dividend_1099s", [])

        # Part I - Short-Term Capital Gains and Losses
        # Line 1: Short-term from Form 8949 (basis reported to IRS)
        st_gain_loss = f8949.get_line("st_gain_loss") if f8949 else 0
        self.set_line("line_7", st_gain_loss)  # Net short-term

        # Part II - Long-Term Capital Gains and Losses
        lt_gain_loss = f8949.get_line("lt_gain_loss") if f8949 else 0

        # Add capital gain distributions from 1099-DIV box 2a
        cap_gain_distributions = sum(
            float(d.get("box_2a_total_capital_gain", 0)) for d in dividend_1099s
        )
        self.set_line("line_13", cap_gain_distributions)

        total_lt = lt_gain_loss + cap_gain_distributions
        self.set_line("line_15", total_lt)  # Net long-term

        # Part III - Summary
        net_st = self.get_line("line_7")
        net_lt = self.get_line("line_15")

        # Line 16: Combine net short-term and net long-term
        net_capital = net_st + net_lt
        self.set_line("line_16", net_capital)

        # If net capital is a gain
        if net_capital > 0:
            self.set_line("line_21", net_capital)
            self.set_line("has_gain", 1)
        else:
            # Capital loss is limited to $3,000
            allowed_loss = max(net_capital, -CAPITAL_LOSS_LIMIT)
            self.set_line("line_21", allowed_loss)
            self.set_line("carryforward_loss", net_capital - allowed_loss)
            self.set_line("has_gain", 0)

        # Track whether we need the QDCG worksheet
        # (net capital gain > 0 OR qualified dividends > 0)
        self.set_line("net_lt_gain", max(0, net_lt))
