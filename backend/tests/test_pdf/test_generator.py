"""Tests for PDF generator (unit tests that don't need actual IRS templates)."""

import pytest

from app.pdf.generator import PDFGenerator


class TestPDFGeneratorHelpers:
    def setup_method(self):
        self.gen = PDFGenerator()

    def test_format_currency_positive(self):
        assert self.gen._format_currency(1234.56) == "1235"

    def test_format_currency_negative(self):
        assert self.gen._format_currency(-500.00) == "(500)"

    def test_format_currency_zero(self):
        assert self.gen._format_currency(0) == ""

    def test_resolve_taxpayer_name(self):
        form_data = {}
        taxpayer_data = {
            "primary": {"first_name": "John", "last_name": "Doe"},
        }
        result = self.gen._resolve_value("taxpayer.name", form_data, taxpayer_data)
        assert result == "John Doe"

    def test_resolve_taxpayer_first_name_mi(self):
        form_data = {}
        taxpayer_data = {
            "primary": {"first_name": "John", "middle_initial": "Q"},
        }
        result = self.gen._resolve_value("taxpayer.first_name_mi", form_data, taxpayer_data)
        assert result == "John Q"

    def test_resolve_taxpayer_ssn(self):
        form_data = {}
        taxpayer_data = {
            "primary": {"ssn": "123-45-6789"},
        }
        result = self.gen._resolve_value("taxpayer.ssn", form_data, taxpayer_data)
        assert result == "123-45-6789"

    def test_resolve_spouse_fields(self):
        form_data = {}
        taxpayer_data = {
            "primary": {},
            "spouse": {"first_name": "Jane", "middle_initial": "A", "last_name": "Doe"},
        }
        result = self.gen._resolve_value("spouse.first_name_mi", form_data, taxpayer_data)
        assert result == "Jane A"
        result2 = self.gen._resolve_value("spouse.last_name", form_data, taxpayer_data)
        assert result2 == "Doe"

    def test_resolve_address(self):
        form_data = {}
        taxpayer_data = {
            "primary": {
                "street_address": "123 Main St",
                "apt_number": "4B",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62701",
            },
        }
        assert self.gen._resolve_value("address.street", form_data, taxpayer_data) == "123 Main St"
        assert self.gen._resolve_value("address.apt", form_data, taxpayer_data) == "4B"
        assert (
            self.gen._resolve_value("address.city_state_zip", form_data, taxpayer_data)
            == "Springfield, IL 62701"
        )

    def test_resolve_filing_status(self):
        form_data = {}
        taxpayer_data = {
            "primary": {},
            "filing_status": "single",
        }
        assert self.gen._resolve_value("filing_status.single", form_data, taxpayer_data) is True
        assert self.gen._resolve_value("filing_status.mfj", form_data, taxpayer_data) is False

    def test_resolve_filing_status_mfj(self):
        form_data = {}
        taxpayer_data = {
            "primary": {},
            "filing_status": "married_filing_jointly",
        }
        assert self.gen._resolve_value("filing_status.single", form_data, taxpayer_data) is False
        assert self.gen._resolve_value("filing_status.mfj", form_data, taxpayer_data) is True

    def test_resolve_form_data(self):
        form_data = {"line_1a": 75000, "line_16": 8522}
        taxpayer_data = {"primary": {}}
        assert self.gen._resolve_value("line_1a", form_data, taxpayer_data) == 75000
        assert self.gen._resolve_value("line_16", form_data, taxpayer_data) == 8522

    def test_enrich_schedule_b(self):
        form_data = {"line_4": 3000}
        return_data = {
            "interest_1099s": [
                {"payer_name": "Chase Bank", "box_1_interest": 1500},
                {"payer_name": "Ally Bank", "box_1_interest": 1500},
            ],
            "dividend_1099s": [
                {"payer_name": "Vanguard", "box_1a_ordinary_dividends": 2000},
            ],
        }
        taxpayer_data = {"primary": {}}

        enriched = self.gen._enrich_form_data("schedule_b", form_data, return_data, taxpayer_data)

        assert enriched["interest_payer_1"] == "Chase Bank"
        assert enriched["interest_amount_1"] == 1500
        assert enriched["interest_payer_2"] == "Ally Bank"
        assert enriched["interest_amount_2"] == 1500
        assert enriched["dividend_payer_1"] == "Vanguard"
        assert enriched["dividend_amount_1"] == 2000
        assert enriched["line_4"] == 3000  # Original data preserved

    def test_enrich_non_schedule_b_passthrough(self):
        form_data = {"line_1a": 75000}
        return_data = {}
        taxpayer_data = {"primary": {}}

        enriched = self.gen._enrich_form_data("form_1040", form_data, return_data, taxpayer_data)
        assert enriched == {"line_1a": 75000}

    def test_generate_form_missing_template(self):
        with pytest.raises(FileNotFoundError):
            self.gen.generate_form("nonexistent_form", {}, {"primary": {}})

    def test_generate_form_no_field_map(self):
        # Even with a valid-looking form_id, if no field map exists, it should raise
        with pytest.raises((FileNotFoundError, ValueError)):
            self.gen.generate_form("unknown_form", {}, {"primary": {}})
