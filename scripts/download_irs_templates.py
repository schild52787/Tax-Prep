#!/usr/bin/env python3
"""Download official IRS fillable PDF form templates.

Usage:
    python scripts/download_irs_templates.py

Downloads all required IRS PDF forms into backend/app/pdf/templates/.
These forms are used by the PDF generator to produce filled tax returns.
"""

import sys
from pathlib import Path
from urllib.request import urlretrieve

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "backend" / "app" / "pdf" / "templates"

# IRS PDF download URLs (names must match form_ids in app/pdf/field_mappings)
FORMS = {
    "form_1040": "https://www.irs.gov/pub/irs-pdf/f1040.pdf",
    "schedule_a": "https://www.irs.gov/pub/irs-pdf/f1040sa.pdf",
    "schedule_b": "https://www.irs.gov/pub/irs-pdf/f1040sb.pdf",
    "schedule_d": "https://www.irs.gov/pub/irs-pdf/f1040sd.pdf",
    "schedule_1": "https://www.irs.gov/pub/irs-pdf/f1040s1.pdf",
    "schedule_2": "https://www.irs.gov/pub/irs-pdf/f1040s2.pdf",
    "schedule_3": "https://www.irs.gov/pub/irs-pdf/f1040s3.pdf",
    "form_8949": "https://www.irs.gov/pub/irs-pdf/f8949.pdf",
    "schedule_8812": "https://www.irs.gov/pub/irs-pdf/f1040s8.pdf",
    "form_8863": "https://www.irs.gov/pub/irs-pdf/f8863.pdf",
    "form_8880": "https://www.irs.gov/pub/irs-pdf/f8880.pdf",
}


def main() -> None:
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

    for name, url in FORMS.items():
        dest = TEMPLATE_DIR / f"{name}.pdf"
        if dest.exists():
            print(f"  [skip] {name}.pdf already exists")
            continue
        print(f"  [download] {name}.pdf from {url}")
        try:
            urlretrieve(url, dest)
            print(f"  [ok] {name}.pdf ({dest.stat().st_size:,} bytes)")
        except Exception as e:
            print(f"  [error] {name}.pdf: {e}", file=sys.stderr)

    print(f"\nTemplates saved to: {TEMPLATE_DIR}")


if __name__ == "__main__":
    main()
