"""Registry mapping document types to their field extractors."""

from __future__ import annotations

from app.ocr.extractors.base import BaseExtractor
from app.ocr.extractors.f1099_div_extractor import Dividend1099Extractor
from app.ocr.extractors.f1099_int_extractor import Interest1099Extractor
from app.ocr.extractors.w2_extractor import W2Extractor

# Maps classifier output (document_type string) -> extractor instance.
EXTRACTOR_REGISTRY: dict[str, BaseExtractor] = {
    "w2": W2Extractor(),
    "1099_int": Interest1099Extractor(),
    "1099_div": Dividend1099Extractor(),
}


def get_extractor(document_type: str) -> BaseExtractor | None:
    """Return the extractor for *document_type*, or ``None`` if unsupported."""
    return EXTRACTOR_REGISTRY.get(document_type)
