"""1099-DIV Dividends and Distributions field extractor."""

from __future__ import annotations

from app.ocr.extractors.base import BaseExtractor


class Dividend1099Extractor(BaseExtractor):
    """Extract fields from a 1099-DIV document's OCR text."""

    def extract(self, text: str) -> dict:
        return {
            "payer_name": self._extract_payer_name(text),
            "box_1a_ordinary_dividends": self._extract_box_1a(text),
            "box_1b_qualified_dividends": self._extract_box_1b(text),
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

    def _extract_box_1a(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*1a\b|(?:Total\s+)?[Oo]rdinary\s+dividends)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:1a\s+(?:Total\s+)?[Oo]rdinary\s+dividends)[\s.:]*\$?([\d,]+\.?\d*)",
        ])

    def _extract_box_1b(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*1b\b|[Qq]ualified\s+dividends)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:1b\s+[Qq]ualified\s+dividends)[\s.:]*\$?([\d,]+\.?\d*)",
        ])

    def _extract_box_4(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*4\b|Federal\s+income\s+tax\s+withheld)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:4\s+Federal\s+income\s+tax\s+withheld)[\s.:]*\$?([\d,]+\.?\d*)",
        ])
