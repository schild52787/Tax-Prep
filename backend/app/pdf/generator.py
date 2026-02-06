"""PDF Generator - fills IRS form templates with calculated tax data."""

import io
from pathlib import Path

from PyPDFForm import PdfWrapper
from pypdf import PdfWriter

from app.pdf.field_mappings import get_field_map


class PDFGenerator:
    """Generates IRS-compliant filled PDFs from tax calculation results."""

    def __init__(self, template_dir: str | Path | None = None):
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        self.template_dir = Path(template_dir)

    def generate_form(
        self,
        form_id: str,
        form_data: dict,
        taxpayer_data: dict,
    ) -> bytes:
        """Fill a single IRS form template with calculated data.

        Args:
            form_id: e.g. "form_1040", "schedule_a"
            form_data: Calculated line values {line_id: value}
            taxpayer_data: Personal info for header fields

        Returns:
            Filled PDF as bytes.
        """
        template_path = self.template_dir / f"{form_id}.pdf"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        field_map = get_field_map(form_id)
        if not field_map:
            raise ValueError(f"No field mapping defined for {form_id}")

        fill_data = {}
        for data_key, pdf_field in field_map.items():
            value = self._resolve_value(data_key, form_data, taxpayer_data)
            if value is not None and value != "" and value != 0:
                if isinstance(value, bool):
                    fill_data[pdf_field] = value
                elif isinstance(value, (int, float)):
                    fill_data[pdf_field] = self._format_currency(value)
                else:
                    fill_data[pdf_field] = str(value)

        filled_pdf = PdfWrapper(str(template_path)).fill(fill_data)
        buf = io.BytesIO()
        filled_pdf.stream.seek(0)
        buf.write(filled_pdf.stream.read())
        return buf.getvalue()

    def generate_all_forms(
        self,
        calculation_result: dict,
        taxpayer_data: dict,
        return_data: dict,
    ) -> bytes:
        """Generate all required forms and merge into a single PDF.

        Args:
            calculation_result: Full output from TaxEngine.calculate()
            taxpayer_data: Personal info dict
            return_data: Raw return data (for Schedule B payer details, etc.)

        Returns:
            Merged PDF containing all forms, as bytes.
        """
        required_forms = calculation_result.get("required_forms", ["form_1040"])
        form_results = calculation_result.get("form_results", {})

        writer = PdfWriter()

        for form_id in required_forms:
            form_data = form_results.get(form_id, {})

            # Enrich form data with context-specific details
            enriched = self._enrich_form_data(form_id, form_data, return_data, taxpayer_data)

            try:
                pdf_bytes = self.generate_form(form_id, enriched, taxpayer_data)
                reader_stream = io.BytesIO(pdf_bytes)
                writer.append(reader_stream)
            except (FileNotFoundError, ValueError):
                # Skip forms we don't have templates/mappings for yet
                continue

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

    def _resolve_value(self, data_key: str, form_data: dict, taxpayer_data: dict):
        """Resolve a data key to its value from form_data or taxpayer_data."""
        # Handle taxpayer/spouse/address fields
        if data_key.startswith("taxpayer."):
            field = data_key.split(".", 1)[1]
            primary = taxpayer_data.get("primary", {})
            if field == "name":
                first = primary.get("first_name", "")
                last = primary.get("last_name", "")
                return f"{first} {last}".strip()
            if field == "first_name_mi":
                first = primary.get("first_name", "")
                mi = primary.get("middle_initial", "")
                return f"{first} {mi}".strip()
            if field == "ssn":
                return primary.get("ssn", "")
            return primary.get(field, "")

        if data_key.startswith("spouse."):
            field = data_key.split(".", 1)[1]
            spouse = taxpayer_data.get("spouse", {})
            if field == "first_name_mi":
                first = spouse.get("first_name", "")
                mi = spouse.get("middle_initial", "")
                return f"{first} {mi}".strip()
            return spouse.get(field, "")

        if data_key.startswith("address."):
            field = data_key.split(".", 1)[1]
            primary = taxpayer_data.get("primary", {})
            if field == "street":
                return primary.get("street_address", "")
            if field == "apt":
                return primary.get("apt_number", "")
            if field == "city_state_zip":
                city = primary.get("city", "")
                state = primary.get("state", "")
                zip_code = primary.get("zip_code", "")
                return f"{city}, {state} {zip_code}".strip(", ")
            return ""

        if data_key.startswith("filing_status."):
            status = data_key.split(".", 1)[1]
            actual_status = taxpayer_data.get("filing_status", "single")
            if status == "single":
                return actual_status == "single"
            if status == "mfj":
                return actual_status == "married_filing_jointly"
            return False

        # Regular form line data
        return form_data.get(data_key, "")

    def _format_currency(self, value: float) -> str:
        """Format numbers for IRS forms: whole dollars, no symbols."""
        if value == 0:
            return ""
        rounded = round(value)
        if rounded < 0:
            return f"({abs(rounded)})"
        return str(rounded)

    def _enrich_form_data(
        self, form_id: str, form_data: dict, return_data: dict, taxpayer_data: dict
    ) -> dict:
        """Add context-specific data like payer names for Schedule B."""
        enriched = dict(form_data)

        if form_id == "schedule_b":
            # Add individual payer names and amounts
            for i, item in enumerate(return_data.get("interest_1099s", []), start=1):
                if i > 14:
                    break
                enriched[f"interest_payer_{i}"] = item.get("payer_name", "")
                enriched[f"interest_amount_{i}"] = float(item.get("box_1_interest", 0))

            for i, item in enumerate(return_data.get("dividend_1099s", []), start=1):
                if i > 16:
                    break
                enriched[f"dividend_payer_{i}"] = item.get("payer_name", "")
                enriched[f"dividend_amount_{i}"] = float(
                    item.get("box_1a_ordinary_dividends", 0)
                )

        return enriched
