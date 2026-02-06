"""Tests for the summary report PDF builder."""

import pytest

from app.pdf.summary_report import SummaryReportBuilder


class TestSummaryReportBuilder:
    def setup_method(self):
        self.builder = SummaryReportBuilder()
        self.taxpayer_data = {
            "filing_status": "single",
            "primary": {
                "first_name": "John",
                "last_name": "Doe",
            },
        }

    def test_build_returns_pdf_bytes(self):
        calc_result = {
            "total_income": 75000,
            "agi": 75000,
            "taxable_income": 59250,
            "total_tax": 8522,
            "total_credits": 0,
            "total_payments": 10000,
            "refund_amount": 1478,
            "amount_owed": 0,
            "effective_tax_rate": 0.1136,
            "marginal_tax_rate": 0.22,
            "standard_deduction_amount": 15750,
            "itemized_deduction_amount": 0,
            "deduction_method": "standard",
            "form_results": {
                "form_1040": {
                    "line_1a": 75000,
                    "line_2b": 0,
                    "line_3b": 0,
                    "line_7": 0,
                    "line_16": 8522,
                    "line_25d": 10000,
                },
            },
            "required_forms": ["form_1040"],
        }

        pdf_bytes = self.builder.build(calc_result, self.taxpayer_data)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # PDF files start with %PDF
        assert pdf_bytes[:4] == b"%PDF"

    def test_build_with_refund(self):
        calc_result = {
            "total_income": 50000,
            "agi": 50000,
            "taxable_income": 34250,
            "total_tax": 3920,
            "total_credits": 0,
            "total_payments": 6000,
            "refund_amount": 2080,
            "amount_owed": 0,
            "effective_tax_rate": 0.0784,
            "marginal_tax_rate": 0.12,
            "standard_deduction_amount": 15750,
            "itemized_deduction_amount": 0,
            "deduction_method": "standard",
            "form_results": {"form_1040": {}},
            "required_forms": ["form_1040"],
        }

        pdf_bytes = self.builder.build(calc_result, self.taxpayer_data)
        assert pdf_bytes[:4] == b"%PDF"

    def test_build_with_amount_owed(self):
        calc_result = {
            "total_income": 150000,
            "agi": 150000,
            "taxable_income": 134250,
            "total_tax": 24000,
            "total_credits": 0,
            "total_payments": 20000,
            "refund_amount": 0,
            "amount_owed": 4000,
            "effective_tax_rate": 0.16,
            "marginal_tax_rate": 0.24,
            "standard_deduction_amount": 15750,
            "itemized_deduction_amount": 0,
            "deduction_method": "standard",
            "form_results": {"form_1040": {}},
            "required_forms": ["form_1040"],
        }

        pdf_bytes = self.builder.build(calc_result, self.taxpayer_data)
        assert pdf_bytes[:4] == b"%PDF"

    def test_build_with_multiple_forms(self):
        calc_result = {
            "total_income": 100000,
            "agi": 100000,
            "taxable_income": 84250,
            "total_tax": 14000,
            "total_credits": 0,
            "total_payments": 15000,
            "refund_amount": 1000,
            "amount_owed": 0,
            "effective_tax_rate": 0.14,
            "marginal_tax_rate": 0.22,
            "standard_deduction_amount": 15750,
            "itemized_deduction_amount": 12000,
            "deduction_method": "standard",
            "form_results": {"form_1040": {}},
            "required_forms": [
                "form_1040",
                "schedule_b",
                "schedule_d",
                "form_8949",
            ],
        }

        pdf_bytes = self.builder.build(calc_result, self.taxpayer_data)
        assert pdf_bytes[:4] == b"%PDF"

    def test_format_currency(self):
        assert self.builder._fmt(0) == "$0"
        assert self.builder._fmt(1234.56) == "$1,234.56"
        assert self.builder._fmt(-500) == "($500.00)"
        assert self.builder._fmt("not a number") == "not a number"

    def test_build_with_mfj(self):
        taxpayer_data = {
            "filing_status": "married_filing_jointly",
            "primary": {
                "first_name": "John",
                "last_name": "Doe",
            },
            "spouse": {
                "first_name": "Jane",
                "last_name": "Doe",
            },
        }
        calc_result = {
            "total_income": 150000,
            "agi": 150000,
            "taxable_income": 118500,
            "total_tax": 15000,
            "total_credits": 0,
            "total_payments": 18000,
            "refund_amount": 3000,
            "amount_owed": 0,
            "effective_tax_rate": 0.10,
            "marginal_tax_rate": 0.22,
            "standard_deduction_amount": 31500,
            "itemized_deduction_amount": 0,
            "deduction_method": "standard",
            "form_results": {"form_1040": {}},
            "required_forms": ["form_1040"],
        }

        pdf_bytes = self.builder.build(calc_result, taxpayer_data)
        assert pdf_bytes[:4] == b"%PDF"
