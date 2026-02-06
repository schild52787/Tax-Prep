"""Inspect IRS PDF templates to discover fillable field names.

Usage:
    python scripts/inspect_pdf_fields.py [form_name]

Example:
    python scripts/inspect_pdf_fields.py form_1040
"""

import sys
from pathlib import Path

from PyPDFForm import PdfWrapper


def inspect_fields(pdf_path: str) -> None:
    print(f"\nFields in {pdf_path}:")
    print("-" * 80)
    wrapper = PdfWrapper(pdf_path)
    for field_name, field_info in sorted(wrapper.schema.items()):
        print(f"  {field_name}: {field_info}")
    print(f"\nTotal fields: {len(wrapper.schema)}")


def main() -> None:
    template_dir = Path("backend/app/pdf/templates")

    if len(sys.argv) > 1:
        form_name = sys.argv[1]
        pdf_path = template_dir / f"{form_name}.pdf"
        if not pdf_path.exists():
            print(f"Template not found: {pdf_path}")
            print("Run 'python scripts/download_irs_templates.py' first.")
            sys.exit(1)
        inspect_fields(str(pdf_path))
    else:
        if not template_dir.exists():
            print("Template directory not found. Run download_irs_templates.py first.")
            sys.exit(1)
        for pdf_path in sorted(template_dir.glob("*.pdf")):
            inspect_fields(str(pdf_path))


if __name__ == "__main__":
    main()
