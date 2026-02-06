"""Tax Engine - Orchestrates the full tax calculation for a return."""

from app.tax_engine.forms.form_1040 import Form1040
from app.tax_engine.forms.form_8949 import Form8949
from app.tax_engine.forms.schedule_a import ScheduleA
from app.tax_engine.forms.schedule_b import ScheduleB
from app.tax_engine.forms.schedule_d import ScheduleD
from app.tax_engine.solver import TaxFormSolver


class TaxEngine:
    """Computes all tax forms for a given return and produces a result summary."""

    def calculate(self, return_data: dict) -> dict:
        """Run the full tax calculation.

        Args:
            return_data: Dict containing all raw data for the return, structured as:
                {
                    "filing_status": "single" | "married_filing_jointly",
                    "w2_incomes": [{"box_1_wages": ..., "box_2_fed_tax_withheld": ...}, ...],
                    "interest_1099s": [...],
                    "dividend_1099s": [...],
                    "retirement_1099rs": [...],
                    "government_1099gs": [...],
                    "ssa_1099s": [...],
                    "capital_asset_sales": [...],
                    "itemized_deduction": {...} or None,
                    "dependents": [...],
                }

        Returns:
            Dict with calculation results including form line items, summary, and
            list of required forms.
        """
        solver = TaxFormSolver()

        # Register all forms
        solver.register(ScheduleB())
        solver.register(Form8949())
        solver.register(ScheduleD())
        solver.register(ScheduleA())
        solver.register(Form1040())

        # Compute all forms in dependency order
        computed = solver.solve(return_data)

        # Build result
        form_1040 = computed["form_1040"]

        # Determine which forms are required
        required_forms = ["form_1040"]
        schedule_b = computed.get("schedule_b")
        if schedule_b:
            interest = schedule_b.get_line("line_4")
            dividends = schedule_b.get_line("line_6")
            if interest > 1500 or dividends > 1500:
                required_forms.append("schedule_b")

        form_8949 = computed.get("form_8949")
        if form_8949 and form_8949.get_line("transaction_count") > 0:
            required_forms.append("form_8949")
            required_forms.append("schedule_d")

        schedule_a = computed.get("schedule_a")
        if form_1040.lines.get("deduction_method") == "itemized":
            required_forms.append("schedule_a")

        # Collect all form results
        form_results = {}
        for form_id, form in computed.items():
            form_results[form_id] = form.get_all_lines()

        return {
            "total_income": form_1040.get_line("line_9"),
            "agi": form_1040.get_line("line_11"),
            "taxable_income": form_1040.get_line("line_15"),
            "total_tax": form_1040.get_line("line_24"),
            "total_credits": form_1040.get_line("line_20"),
            "total_payments": form_1040.get_line("line_33"),
            "refund_amount": form_1040.get_line("line_35a"),
            "amount_owed": form_1040.get_line("line_37"),
            "effective_tax_rate": form_1040.get_line("effective_rate"),
            "marginal_tax_rate": form_1040.get_line("marginal_rate"),
            "standard_deduction_amount": form_1040.get_line("standard_deduction"),
            "itemized_deduction_amount": form_1040.get_line("itemized_deduction"),
            "deduction_method": form_1040.lines.get("deduction_method", "standard"),
            "form_results": form_results,
            "required_forms": required_forms,
            "errors": [],
            "warnings": [],
        }
