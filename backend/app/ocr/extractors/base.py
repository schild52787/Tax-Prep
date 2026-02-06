"""Abstract base class for tax-document field extractors."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """Base class that all document-specific extractors must subclass.

    Subclasses implement ``extract()`` which receives the full OCR text and
    returns a dict of extracted field names to values.
    """

    @abstractmethod
    def extract(self, text: str) -> dict:
        """Extract structured fields from *text*.

        Returns
        -------
        dict
            A mapping of field names (matching the DB model columns) to their
            extracted values.  Numeric fields should be ``float``; text fields
            should be ``str | None``.
        """
        ...

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_amount(text: str, patterns: list[str]) -> float | None:
        """Search *text* for a dollar amount near one of the *patterns*.

        Each pattern in *patterns* should be a regex that captures a dollar
        amount in group 1 (digits, commas, optional decimal).  The first
        successful match wins.

        Returns
        -------
        float | None
            The parsed dollar amount, or ``None`` if nothing matched.
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw = match.group(1).replace(",", "").strip()
                try:
                    return float(raw)
                except ValueError:
                    continue
        return None

    @staticmethod
    def _find_text(text: str, patterns: list[str]) -> str | None:
        """Search *text* for a text value near one of the *patterns*.

        Each pattern should capture the desired text in group 1.  The first
        match wins.  Leading/trailing whitespace is stripped.

        Returns
        -------
        str | None
            The matched text, or ``None`` if nothing matched.
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                if value:
                    return value
        return None
