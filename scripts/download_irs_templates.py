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

# IRS PDF download URLs (fillable forms)
FORMS = {
    "f1040": "https://www.irs.gov/pub/irs-pdf/f1040.pdf",
    "f1040sa": "https://www.irs.gov/pub/irs-pdf/f1040sa.pdf",
    "f1040sb": "https://www.irs.gov/pub/irs-pdf/f1040sb.pdf",
    "f1040sd": "https://www.irs.gov/pub/irs-pdf/f1040sd.pdf",
    "f1040s1": "https://www.irs.gov/pub/irs-pdf/f1040s1.pdf",
    "f1040s2": "https://www.irs.gov/pub/irs-pdf/f1040s2.pdf",
    "f1040s3": "https://www.irs.gov/pub/irs-pdf/f1040s3.pdf",
    "f8949": "https://www.irs.gov/pub/irs-pdf/f8949.pdf",
    "f8812": "https://www.irs.gov/pub/irs-pdf/f1040s8.pdf",
    "f8863": "https://www.irs.gov/pub/irs-pdf/f8863.pdf",
    "f8880": "https://www.irs.gov/pub/irs-pdf/f8880.pdf",
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
