"""W-2 Wage and Tax Statement field extractor."""

from __future__ import annotations

from app.ocr.extractors.base import BaseExtractor


class W2Extractor(BaseExtractor):
    """Extract fields from a W-2 document's OCR text."""

    def extract(self, text: str) -> dict:
        return {
            "employer_name": self._extract_employer_name(text),
            "employer_ein": self._extract_employer_ein(text),
            "box_1_wages": self._extract_box_1(text),
            "box_2_fed_tax_withheld": self._extract_box_2(text),
            "box_3_ss_wages": self._extract_box_3(text),
            "box_4_ss_tax": self._extract_box_4(text),
            "box_5_medicare_wages": self._extract_box_5(text),
            "box_6_medicare_tax": self._extract_box_6(text),
            "state": self._extract_state(text),
            "state_wages": self._extract_state_wages(text),
            "state_tax_withheld": self._extract_state_tax(text),
        }

    # ------------------------------------------------------------------
    # Field-specific extraction
    # ------------------------------------------------------------------

    def _extract_employer_name(self, text: str) -> str | None:
        return self._find_text(text, [
            # "c Employer's name, address, and ZIP code" followed by the name
            r"Employer(?:'|')s\s+name[,\s\w]*\n+\s*(.+)",
            # Sometimes just the line after "Employer's name"
            r"Employer(?:'|')s\s+name\s*[\.:]\s*(.+)",
        ])

    def _extract_employer_ein(self, text: str) -> str | None:
        return self._find_text(text, [
            r"Employer(?:'|')?\s*identification\s*number[^\d]*(\d{2}[\-\s]?\d{7})",
            r"(?:EIN|b\s+Employer)\s*[:\s]*(\d{2}[\-\s]?\d{7})",
        ])

    def _extract_box_1(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*1\b|Wages[,\s]*tips[,\s]*other\s+comp)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:1\s+Wages[,\s]*tips)[\s.:]*\$?([\d,]+\.?\d*)",
        ])

    def _extract_box_2(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*2\b|Federal\s+income\s+tax\s+withheld)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:2\s+Federal\s+income\s+tax)[\s.:]*\$?([\d,]+\.?\d*)",
        ])

    def _extract_box_3(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*3\b|Social\s+security\s+wages)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:3\s+Social\s+security\s+wages)[\s.:]*\$?([\d,]+\.?\d*)",
        ])

    def _extract_box_4(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*4\b|Social\s+security\s+tax\s+withheld)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:4\s+Social\s+security\s+tax\s+withheld)[\s.:]*\$?([\d,]+\.?\d*)",
        ])

    def _extract_box_5(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*5\b|Medicare\s+wages\s+and\s+tips)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:5\s+Medicare\s+wages)[\s.:]*\$?([\d,]+\.?\d*)",
        ])

    def _extract_box_6(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*6\b|Medicare\s+tax\s+withheld)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:6\s+Medicare\s+tax\s+withheld)[\s.:]*\$?([\d,]+\.?\d*)",
        ])

    def _extract_state(self, text: str) -> str | None:
        return self._find_text(text, [
            r"(?:Box\s*15|15\s+State)[\s.:]*([A-Z]{2})\b",
            r"\bState\s*[\.:]\s*([A-Z]{2})\b",
        ])

    def _extract_state_wages(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*16\b|State\s+wages[,\s]*tips)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:16\s+State\s+wages)[\s.:]*\$?([\d,]+\.?\d*)",
        ])

    def _extract_state_tax(self, text: str) -> float | None:
        return self._find_amount(text, [
            r"(?:Box\s*17\b|State\s+income\s+tax)[\s.:]*\$?([\d,]+\.?\d*)",
            r"(?:17\s+State\s+income\s+tax)[\s.:]*\$?([\d,]+\.?\d*)",
        ])
