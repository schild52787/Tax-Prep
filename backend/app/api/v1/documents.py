"""Document upload, OCR, classification, extraction, and import endpoints."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.income import (
    Dividend1099,
    Government1099G,
    Interest1099,
    Retirement1099R,
    SSA1099,
    W2Income,
)
from app.models.tax_return import TaxReturn
from app.ocr.classifier import DocumentClassifier
from app.ocr.extractors import get_extractor
from app.ocr.processor import OCRProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/returns/{return_id}/documents", tags=["Documents"])

# Singletons -- stateless, safe to share across requests.
_ocr_processor = OCRProcessor()
_classifier = DocumentClassifier()

# Max length of raw text returned in the preview field.
_RAW_TEXT_PREVIEW_LENGTH = 500


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class UploadResponse(BaseModel):
    """Returned after OCR + classification + extraction of an uploaded file."""

    document_type: str
    extracted_data: dict[str, Any]
    confidence: float
    raw_text_preview: str


class ImportRequest(BaseModel):
    """Accepted by the import endpoint to persist reviewed/corrected data."""

    document_type: str
    data: dict[str, Any]


class ImportResponse(BaseModel):
    """Returned after a successful import."""

    id: str
    document_type: str
    message: str


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

async def _get_return(return_id: str, db: AsyncSession) -> TaxReturn:
    tax_return = await db.get(TaxReturn, return_id)
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    return tax_return


# Maps document_type -> SQLAlchemy model class for import.
_MODEL_MAP: dict[str, type] = {
    "w2": W2Income,
    "1099_int": Interest1099,
    "1099_div": Dividend1099,
    "1099_b": None,  # Capital sales handled via separate endpoint
    "1099_r": Retirement1099R,
    "1099_g": Government1099G,
    "ssa_1099": SSA1099,
}


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    return_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF document, OCR it, classify it, and extract data.

    The extracted fields are returned for the user to review and correct
    before calling the ``/import`` endpoint to persist them.
    """
    await _get_return(return_id, db)

    # 1. Read the uploaded file into memory.
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # 2. Save to a temporary file so pdfplumber/pdf2image can work with it.
    suffix = Path(file.filename or "upload.pdf").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        # 3. Run OCR to extract text.
        raw_text = _ocr_processor.extract_text(tmp_path)
    except Exception as exc:
        logger.exception("OCR processing failed for %s", file.filename)
        raise HTTPException(
            status_code=422,
            detail=f"Failed to extract text from document: {exc}",
        ) from exc
    finally:
        # Clean up temp file.
        try:
            tmp_path.unlink()
        except OSError:
            pass

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from the uploaded document",
        )

    # 4. Classify the document.
    classification = _classifier.classify(raw_text)

    # 5. Run the appropriate field extractor.
    extractor = get_extractor(classification.document_type)
    if extractor is not None:
        extracted_data = extractor.extract(raw_text)
    else:
        extracted_data = {}

    # 6. Return results for review.
    return UploadResponse(
        document_type=classification.document_type,
        extracted_data=extracted_data,
        confidence=classification.confidence,
        raw_text_preview=raw_text[:_RAW_TEXT_PREVIEW_LENGTH],
    )


@router.post("/import", response_model=ImportResponse, status_code=201)
async def import_document(
    return_id: str,
    body: ImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Accept reviewed/corrected extracted data and save to the DB.

    The ``data`` field should match the schema for the given
    ``document_type`` (same fields as the corresponding Create schema in
    ``app.schemas.income``).
    """
    await _get_return(return_id, db)

    model_class = _MODEL_MAP.get(body.document_type)
    if model_class is None:
        raise HTTPException(
            status_code=400,
            detail=f"Import not supported for document type: {body.document_type}",
        )

    # Build the model instance from the provided data dict.
    try:
        record = model_class(return_id=return_id, **body.data)
    except TypeError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid fields for {body.document_type}: {exc}",
        ) from exc

    db.add(record)
    await db.flush()

    return ImportResponse(
        id=record.id,
        document_type=body.document_type,
        message=f"Successfully imported {body.document_type} document",
    )
