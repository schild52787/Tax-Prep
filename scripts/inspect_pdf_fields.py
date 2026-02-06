#!/usr/bin/env python3
"""Inspect fillable PDF field names in IRS form templates.

Usage:
    python scripts/inspect_pdf_fields.py [form_name]

Examples:
    python scripts/inspect_pdf_fields.py              # All forms
    python scripts/inspect_pdf_fields.py f1040         # Just Form 1040

Prints field names, types, and default values for each PDF template.
Use this to build/update the field mappings in backend/app/pdf/field_mappings/.
"""

import sys
from pathlib import Path

from PyPDFForm import PdfWrapper

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "backend" / "app" / "pdf" / "templates"


def inspect_form(pdf_path: Path) -> None:
    print(f"\n{'=' * 70}")
    print(f"Form: {pdf_path.name}")
    print(f"{'=' * 70}")

    wrapper = PdfWrapper(str(pdf_path))
    schema = wrapper.schema

    if not schema:
        print("  (no fillable fields found)")
        return

    for field_name, field_info in sorted(schema.items()):
        field_type = field_info.get("type", "unknown")
        print(f"  {field_name}")
        print(f"    type: {field_type}")
        if "options" in field_info:
            print(f"    options: {field_info['options']}")


def main() -> None:
    if not TEMPLATE_DIR.exists():
        print(f"Template dir not found: {TEMPLATE_DIR}")
        print("Run scripts/download_irs_templates.py first.")
        sys.exit(1)

    filter_name = sys.argv[1] if len(sys.argv) > 1 else None

    pdfs = sorted(TEMPLATE_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDF templates found. Run scripts/download_irs_templates.py first.")
        sys.exit(1)

    for pdf_path in pdfs:
        if filter_name and filter_name not in pdf_path.stem:
            continue
        inspect_form(pdf_path)


if __name__ == "__main__":
    main()
