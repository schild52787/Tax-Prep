"""Human-readable tax return summary report generator using ReportLab."""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class SummaryReportBuilder:
    """Builds a human-readable PDF summary of a tax return calculation."""

    def build(self, calculation_result: dict, taxpayer_data: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
        )
        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=6,
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#1a365d"),
        )
        normal = styles["Normal"]

        # Header
        primary = taxpayer_data.get("primary", {})
        name = f"{primary.get('first_name', '')} {primary.get('last_name', '')}".strip()
        filing_status = taxpayer_data.get("filing_status", "single").replace("_", " ").title()

        story.append(Paragraph("2025 Federal Tax Return Summary", title_style))
        story.append(Paragraph(f"Prepared for: {name or 'Taxpayer'}", normal))
        story.append(Paragraph(f"Filing Status: {filing_status}", normal))
        story.append(
            Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", normal)
        )
        story.append(Spacer(1, 20))

        # Key Results Box
        refund = calculation_result.get("refund_amount", 0)
        owed = calculation_result.get("amount_owed", 0)
        if refund > 0:
            result_text = f"Estimated Refund: ${refund:,.2f}"
            result_color = colors.HexColor("#22543d")
        elif owed > 0:
            result_text = f"Amount Owed: ${owed:,.2f}"
            result_color = colors.HexColor("#9b2c2c")
        else:
            result_text = "No Refund or Amount Owed"
            result_color = colors.black

        result_style = ParagraphStyle(
            "Result",
            parent=styles["Title"],
            fontSize=20,
            textColor=result_color,
            alignment=1,
        )
        story.append(Paragraph(result_text, result_style))
        story.append(Spacer(1, 20))

        # Income Summary
        story.append(Paragraph("Income Summary", heading_style))
        form_1040 = calculation_result.get("form_results", {}).get("form_1040", {})
        income_data = [
            ["Source", "Amount"],
            ["Wages (W-2)", self._fmt(form_1040.get("line_1a", 0))],
            ["Taxable Interest", self._fmt(form_1040.get("line_2b", 0))],
            ["Ordinary Dividends", self._fmt(form_1040.get("line_3b", 0))],
            ["IRA Distributions (taxable)", self._fmt(form_1040.get("line_4b", 0))],
            ["Social Security (taxable)", self._fmt(form_1040.get("line_6b", 0))],
            ["Capital Gain/Loss", self._fmt(form_1040.get("line_7", 0))],
            ["Other Income", self._fmt(form_1040.get("line_8", 0))],
            ["Total Income", self._fmt(calculation_result.get("total_income", 0))],
            ["Adjusted Gross Income (AGI)", self._fmt(calculation_result.get("agi", 0))],
        ]
        story.append(self._make_table(income_data))
        story.append(Spacer(1, 12))

        # Deductions
        story.append(Paragraph("Deductions", heading_style))
        method = calculation_result.get("deduction_method", "standard")
        std_amount = calculation_result.get("standard_deduction_amount", 0)
        item_amount = calculation_result.get("itemized_deduction_amount", 0)

        deduction_data = [
            ["Deduction", "Amount"],
            ["Standard Deduction", self._fmt(std_amount)],
            ["Itemized Deductions", self._fmt(item_amount)],
            [f"Method Used: {method.title()}", ""],
            ["Taxable Income", self._fmt(calculation_result.get("taxable_income", 0))],
        ]
        story.append(self._make_table(deduction_data))
        story.append(Spacer(1, 12))

        # Tax Calculation
        story.append(Paragraph("Tax Calculation", heading_style))
        tax_data = [
            ["Item", "Amount"],
            ["Tax (from brackets)", self._fmt(form_1040.get("line_16", 0))],
            ["Credits Applied", self._fmt(calculation_result.get("total_credits", 0))],
            ["Total Tax", self._fmt(calculation_result.get("total_tax", 0))],
        ]
        story.append(self._make_table(tax_data))
        story.append(Spacer(1, 12))

        # Payments & Result
        story.append(Paragraph("Payments & Result", heading_style))
        payments_data = [
            ["Item", "Amount"],
            [
                "Federal Tax Withheld",
                self._fmt(form_1040.get("line_25d", 0)),
            ],
            ["Total Payments", self._fmt(calculation_result.get("total_payments", 0))],
            ["Total Tax", self._fmt(calculation_result.get("total_tax", 0))],
        ]
        if refund > 0:
            payments_data.append(["REFUND", self._fmt(refund)])
        elif owed > 0:
            payments_data.append(["AMOUNT OWED", self._fmt(owed)])
        story.append(self._make_table(payments_data))
        story.append(Spacer(1, 12))

        # Tax Rates
        story.append(Paragraph("Tax Rate Summary", heading_style))
        eff_rate = calculation_result.get("effective_tax_rate", 0)
        marg_rate = calculation_result.get("marginal_tax_rate", 0)
        rate_data = [
            ["Rate", "Value"],
            ["Effective Tax Rate", f"{eff_rate * 100:.1f}%"],
            ["Marginal Tax Rate", f"{marg_rate * 100:.0f}%"],
        ]
        story.append(self._make_table(rate_data))
        story.append(Spacer(1, 20))

        # Forms included
        story.append(Paragraph("Forms Included", heading_style))
        required = calculation_result.get("required_forms", [])
        form_names = {
            "form_1040": "Form 1040 - U.S. Individual Income Tax Return",
            "schedule_a": "Schedule A - Itemized Deductions",
            "schedule_b": "Schedule B - Interest and Ordinary Dividends",
            "schedule_d": "Schedule D - Capital Gains and Losses",
            "form_8949": "Form 8949 - Sales and Dispositions of Capital Assets",
        }
        for form_id in required:
            display = form_names.get(form_id, form_id)
            story.append(Paragraph(f"  {display}", normal))

        # Disclaimer
        story.append(Spacer(1, 30))
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=normal,
            fontSize=8,
            textColor=colors.gray,
        )
        story.append(
            Paragraph(
                "This summary is for informational purposes only. Verify all figures "
                "against the attached IRS forms before filing. This software is not "
                "affiliated with or endorsed by the IRS.",
                disclaimer_style,
            )
        )

        doc.build(story)
        return buffer.getvalue()

    def _fmt(self, value) -> str:
        """Format a number as currency."""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return str(value)
        if v == 0:
            return "$0"
        if v < 0:
            return f"(${abs(v):,.2f})"
        return f"${v:,.2f}"

    def _make_table(self, data: list[list]) -> Table:
        """Create a styled table."""
        table = Table(data, colWidths=[4 * inch, 2.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d3748")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
                    # Bold the last row of each table (typically the total)
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        return table
