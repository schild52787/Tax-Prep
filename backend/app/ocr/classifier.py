"""Document classifier that identifies tax document types from OCR text.

Uses regex pattern matching against known labels and titles that appear on
standard IRS tax forms.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Supported document types
DOCUMENT_TYPES = (
    "w2",
    "1099_int",
    "1099_div",
    "1099_b",
    "1099_r",
    "1099_g",
    "ssa_1099",
    "unknown",
)

# Each entry is (document_type, list_of_patterns, weight).
# Patterns are matched case-insensitively against the full OCR text.
# Weight allows us to prefer more-specific matches when multiple patterns hit.
_CLASSIFICATION_RULES: list[tuple[str, list[str], int]] = [
    (
        "w2",
        [
            r"Wage\s+and\s+Tax\s+Statement",
            r"\bW[\-\s]*2\b",
            r"Employer\s+identification\s+number",
        ],
        10,
    ),
    (
        "1099_int",
        [
            r"Interest\s+Income",
            r"1099[\-\s]*INT",
        ],
        10,
    ),
    (
        "1099_div",
        [
            r"Dividends\s+and\s+Distributions",
            r"1099[\-\s]*DIV",
        ],
        10,
    ),
    (
        "1099_b",
        [
            r"Proceeds\s+From\s+Broker",
            r"1099[\-\s]*B\b",
        ],
        10,
    ),
    (
        "1099_r",
        [
            r"Distributions\s+From\s+Pensions",
            r"1099[\-\s]*R\b",
        ],
        10,
    ),
    (
        "1099_g",
        [
            r"Certain\s+Government\s+Payments",
            r"1099[\-\s]*G\b",
        ],
        10,
    ),
    (
        "ssa_1099",
        [
            r"Social\s+Security\s+Benefit\s+Statement",
            r"SSA[\-\s]*1099",
        ],
        10,
    ),
]


@dataclass
class ClassificationResult:
    """Result of document classification."""

    document_type: str
    confidence: float  # 0.0 - 1.0
    matched_patterns: list[str]


class DocumentClassifier:
    """Classify tax documents based on extracted OCR text."""

    def classify(self, text: str) -> ClassificationResult:
        """Identify the document type from *text*.

        Returns a ClassificationResult with the best-matching document type,
        a confidence score (ratio of patterns matched for that type), and the
        list of patterns that fired.
        """
        if not text or not text.strip():
            return ClassificationResult(
                document_type="unknown",
                confidence=0.0,
                matched_patterns=[],
            )

        scores: dict[str, list[str]] = {}

        for doc_type, patterns, _weight in _CLASSIFICATION_RULES:
            matched: list[str] = []
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matched.append(pattern)
            if matched:
                scores[doc_type] = matched

        if not scores:
            return ClassificationResult(
                document_type="unknown",
                confidence=0.0,
                matched_patterns=[],
            )

        # Pick the type with the most pattern matches.  Break ties by
        # preferring the more specific (longer pattern list) rule set.
        best_type = max(
            scores,
            key=lambda dt: (
                len(scores[dt]),
                len(
                    next(
                        patterns
                        for dtype, patterns, _ in _CLASSIFICATION_RULES
                        if dtype == dt
                    )
                ),
            ),
        )

        # Confidence = fraction of patterns matched for the winning type.
        total_patterns = len(
            next(
                patterns
                for dtype, patterns, _ in _CLASSIFICATION_RULES
                if dtype == best_type
            )
        )
        confidence = len(scores[best_type]) / total_patterns

        return ClassificationResult(
            document_type=best_type,
            confidence=round(confidence, 2),
            matched_patterns=scores[best_type],
        )
