"""Form 8949 - Sales and Other Dispositions of Capital Assets.

Organizes capital asset sales into the categories required by Schedule D.
"""

from app.tax_engine.forms.base import BaseTaxForm


class Form8949(BaseTaxForm):
    form_id = "form_8949"
    dependencies = []

    def calculate(self, return_data: dict, other_forms: dict) -> None:
        sales = return_data.get("capital_asset_sales", [])

        # Part I - Short-Term (held 1 year or less)
        st_proceeds = 0
        st_basis = 0
        st_adjustment = 0
        st_gain_loss = 0

        # Part II - Long-Term (held more than 1 year)
        lt_proceeds = 0
        lt_basis = 0
        lt_adjustment = 0
        lt_gain_loss = 0

        for sale in sales:
            proceeds = float(sale.get("proceeds", 0))
            basis = float(sale.get("cost_basis", 0))
            adjustment = float(sale.get("adjustment_amount", 0))
            gain_loss = proceeds - basis + adjustment
            holding = sale.get("holding_period", "short_term")

            if holding == "short_term":
                st_proceeds += proceeds
                st_basis += basis
                st_adjustment += adjustment
                st_gain_loss += gain_loss
            else:
                lt_proceeds += proceeds
                lt_basis += basis
                lt_adjustment += adjustment
                lt_gain_loss += gain_loss

        # Short-term totals
        self.set_line("st_proceeds", st_proceeds)
        self.set_line("st_basis", st_basis)
        self.set_line("st_adjustment", st_adjustment)
        self.set_line("st_gain_loss", st_gain_loss)

        # Long-term totals
        self.set_line("lt_proceeds", lt_proceeds)
        self.set_line("lt_basis", lt_basis)
        self.set_line("lt_adjustment", lt_adjustment)
        self.set_line("lt_gain_loss", lt_gain_loss)

        # Transaction count for determining if form is needed
        self.set_line("transaction_count", len(sales))
