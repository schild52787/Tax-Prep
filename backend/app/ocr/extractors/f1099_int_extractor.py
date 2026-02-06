"""1099-INT Interest Income field extractor."""

from __future__ import annotations

from app.ocr.extractors.base import BaseExtractor


class Interest1099Extractor(BaseExtractor):
    """Extract fields from a 1099-INT document's OCR text."""

    def extract(self, text: str) -> dict:
        return {
            "payer_name": self._extract_payer_name(text),
            "box_1_interest": self._extract_box_1(text),
            "box_4_fed_tax_withheld": self._extract_box_4(text),
        }

    # ------------------------------------------------------------------
    # Field-specific extraction
    # ------------------------------------------------------------------

    def _extract_payer_name(self, text: str) -> str | None:
        return self._find_text(text, [
            r"(?:PAYER(?:'|')S|Payer(?:'|')s)\s+name[,\s\w]*\n+\s*(.+)",
            r"(?:PAYER|Payer)(?:'|')?\s*(?:name|NAME)\s*[\.:]\s*(.+)",
        ])

    def _extract_box_1(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*1\b|Interest\s+income)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:1\s+Interest\s+income)[\s.:]*\$?([\d,]+\.?\d*)",
        ])

    def _extract_box_4(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*4\b|Federal\s+income\s+tax\s+withheld)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:4\s+Federal\s+income\s+tax\s+withheld)[\s.:]*\$?([\d,]+\.?\d*)",
        ])
