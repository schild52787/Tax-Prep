"""OCR processor that extracts text from PDF and image documents.

Uses pdfplumber for native (text-based) PDFs and falls back to
pdf2image + pytesseract for scanned / image-only documents.
"""

from __future__ import annotations

import io
import logging
import tempfile
from pathlib import Path

import pdfplumber
from pdf2image import convert_from_bytes, convert_from_path
from pytesseract import image_to_string

logger = logging.getLogger(__name__)

# Minimum character count to consider a page as having "real" text.
_MIN_CHARS_PER_PAGE = 20


class OCRProcessor:
    """Extract text from uploaded PDF files or image bytes."""

    def extract_text(self, source: bytes | str | Path) -> str:
        """Extract text from the given source.

        Parameters
        ----------
        source:
            Raw file bytes, a file-system path (str or Path) pointing to a
            PDF, or raw image bytes.

        Returns
        -------
        str
            The extracted full text of the document.
        """
        if isinstance(source, (str, Path)):
            return self._extract_from_path(Path(source))
        if isinstance(source, bytes):
            return self._extract_from_bytes(source)
        raise TypeError(f"Unsupported source type: {type(source)}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_from_path(self, path: Path) -> str:
        """Extract text from a file on disk."""
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf_path(path)
        # Treat everything else as an image (png, jpg, tiff, etc.)
        return self._ocr_image_path(path)

    def _extract_from_bytes(self, data: bytes) -> str:
        """Extract text from raw bytes (PDF or image)."""
        # Quick heuristic: PDF files start with %PDF
        if data[:5] == b"%PDF-":
            return self._extract_pdf_bytes(data)
        # Assume image bytes otherwise
        return self._ocr_image_bytes(data)

    # --- PDF native text extraction --------------------------------

    def _extract_pdf_path(self, path: Path) -> str:
        """Try native text extraction first; fall back to OCR."""
        text = self._pdfplumber_extract_path(path)
        if self._has_meaningful_text(text):
            logger.info("Extracted native text from PDF (%d chars)", len(text))
            return text
        logger.info("Native text insufficient; falling back to OCR for %s", path)
        return self._ocr_pdf_path(path)

    def _extract_pdf_bytes(self, data: bytes) -> str:
        """Try native text extraction first; fall back to OCR."""
        text = self._pdfplumber_extract_bytes(data)
        if self._has_meaningful_text(text):
            logger.info("Extracted native text from PDF bytes (%d chars)", len(text))
            return text
        logger.info("Native text insufficient; falling back to OCR for PDF bytes")
        return self._ocr_pdf_bytes(data)

    @staticmethod
    def _pdfplumber_extract_path(path: Path) -> str:
        pages_text: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pages_text.append(page_text)
        return "\n".join(pages_text)

    @staticmethod
    def _pdfplumber_extract_bytes(data: bytes) -> str:
        pages_text: list[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pages_text.append(page_text)
        return "\n".join(pages_text)

    # --- OCR fallback ----------------------------------------------

    @staticmethod
    def _ocr_pdf_path(path: Path) -> str:
        images = convert_from_path(str(path))
        texts = [image_to_string(img) for img in images]
        return "\n".join(texts)

    @staticmethod
    def _ocr_pdf_bytes(data: bytes) -> str:
        images = convert_from_bytes(data)
        texts = [image_to_string(img) for img in images]
        return "\n".join(texts)

    @staticmethod
    def _ocr_image_path(path: Path) -> str:
        from PIL import Image

        img = Image.open(path)
        return image_to_string(img)

    @staticmethod
    def _ocr_image_bytes(data: bytes) -> str:
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        return image_to_string(img)

    # --- Utilities -------------------------------------------------

    @staticmethod
    def _has_meaningful_text(text: str) -> bool:
        """Return True if the extracted text looks like real content."""
        stripped = text.strip()
        if len(stripped) < _MIN_CHARS_PER_PAGE:
            return False
        # Check that there are actual alphabetic characters (not just whitespace / garbage)
        alpha_count = sum(1 for ch in stripped if ch.isalpha())
        return alpha_count > _MIN_CHARS_PER_PAGE
