"""Download official IRS fillable PDF templates for tax year 2025.

Usage:
    python scripts/download_irs_templates.py
"""

import sys
from pathlib import Path

import httpx

IRS_BASE = "https://www.irs.gov/pub/irs-pdf"

TEMPLATES = {
    "form_1040": f"{IRS_BASE}/f1040.pdf",
    "schedule_a": f"{IRS_BASE}/f1040sa.pdf",
    "schedule_b": f"{IRS_BASE}/f1040sb.pdf",
    "schedule_d": f"{IRS_BASE}/f1040sd.pdf",
    "schedule_1": f"{IRS_BASE}/f1040s1.pdf",
    "schedule_2": f"{IRS_BASE}/f1040s2.pdf",
    "schedule_3": f"{IRS_BASE}/f1040s3.pdf",
    "form_8949": f"{IRS_BASE}/f8949.pdf",
    "form_8863": f"{IRS_BASE}/f8863.pdf",
    "form_8880": f"{IRS_BASE}/f8880.pdf",
}


def download_templates(output_dir: str = "backend/app/pdf/templates") -> None:
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)

    client = httpx.Client(timeout=30, follow_redirects=True)

    for form_id, url in TEMPLATES.items():
        filepath = dest / f"{form_id}.pdf"
        if filepath.exists():
            print(f"  Skipping {form_id} (already exists)")
            continue
        print(f"  Downloading {form_id} from {url}")
        try:
            response = client.get(url)
            response.raise_for_status()
            filepath.write_bytes(response.content)
            print(f"    Saved to {filepath} ({len(response.content):,} bytes)")
        except httpx.HTTPError as e:
            print(f"    ERROR downloading {form_id}: {e}", file=sys.stderr)

    client.close()
    print("Done.")


if __name__ == "__main__":
    download_templates()
