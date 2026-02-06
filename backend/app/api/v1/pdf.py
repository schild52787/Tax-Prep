"""PDF generation and download API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.calculation import CalculationResult
from app.models.tax_return import TaxReturn
from app.pdf.generator import PDFGenerator
from app.pdf.summary_report import SummaryReportBuilder

router = APIRouter(prefix="/returns/{return_id}/pdf", tags=["pdf"])


async def _get_return_with_calc(
    return_id: str, db: AsyncSession
) -> tuple[TaxReturn, CalculationResult]:
    """Load a return with its calculation result and taxpayer data."""
    result = await db.execute(
        select(TaxReturn)
        .where(TaxReturn.id == return_id)
        .options(
            selectinload(TaxReturn.taxpayers),
            selectinload(TaxReturn.calculation_result),
            selectinload(TaxReturn.interest_1099s),
            selectinload(TaxReturn.dividend_1099s),
        )
    )
    tax_return = result.scalar_one_or_none()
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    if not tax_return.calculation_result:
        raise HTTPException(
            status_code=400,
            detail="No calculation result. Run POST /calculate first.",
        )
    return tax_return, tax_return.calculation_result


def _build_taxpayer_data(tax_return: TaxReturn) -> dict:
    """Build taxpayer data dict for PDF generation."""
    data: dict = {"filing_status": tax_return.filing_status.value}
    for tp in tax_return.taxpayers:
        role = tp.role or "primary"
        data[role] = {
            "first_name": tp.first_name or "",
            "middle_initial": tp.middle_initial or "",
            "last_name": tp.last_name or "",
            "ssn": tp.ssn_encrypted or "",
            "occupation": tp.occupation or "",
            "street_address": tp.street_address or "",
            "apt_number": getattr(tp, "apt_number", "") or "",
            "city": tp.city or "",
            "state": tp.state or "",
            "zip_code": tp.zip_code or "",
        }
    return data


def _build_return_data(tax_return: TaxReturn) -> dict:
    """Build raw return data for enriching forms (e.g., Schedule B payer names)."""
    return {
        "interest_1099s": [
            {
                "payer_name": i.payer_name or "",
                "box_1_interest": float(i.box_1_interest or 0),
            }
            for i in tax_return.interest_1099s
        ],
        "dividend_1099s": [
            {
                "payer_name": d.payer_name or "",
                "box_1a_ordinary_dividends": float(d.box_1a_ordinary_dividends or 0),
            }
            for d in tax_return.dividend_1099s
        ],
    }


@router.get("/forms")
async def download_forms(return_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and download all filled IRS forms as a single merged PDF."""
    tax_return, calc = await _get_return_with_calc(return_id, db)
    taxpayer_data = _build_taxpayer_data(tax_return)
    return_data = _build_return_data(tax_return)

    calc_dict = {
        "total_income": float(calc.total_income or 0),
        "agi": float(calc.agi or 0),
        "taxable_income": float(calc.taxable_income or 0),
        "total_tax": float(calc.total_tax or 0),
        "total_credits": float(calc.total_credits or 0),
        "total_payments": float(calc.total_payments or 0),
        "refund_amount": float(calc.refund_amount or 0),
        "amount_owed": float(calc.amount_owed or 0),
        "effective_tax_rate": float(calc.effective_tax_rate or 0),
        "marginal_tax_rate": float(calc.marginal_tax_rate or 0),
        "standard_deduction_amount": float(calc.standard_deduction_amount or 0),
        "itemized_deduction_amount": float(calc.itemized_deduction_amount or 0),
        "deduction_method": calc.deduction_method,
        "form_results": calc.form_results or {},
        "required_forms": calc.required_forms or ["form_1040"],
    }

    generator = PDFGenerator()
    try:
        pdf_bytes = generator.generate_all_forms(calc_dict, taxpayer_data, return_data)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="IRS PDF templates not found. Run scripts/download_irs_templates.py first.",
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="tax_return_{return_id}_forms.pdf"'
        },
    )


@router.get("/summary")
async def download_summary(return_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and download a human-readable tax return summary PDF."""
    tax_return, calc = await _get_return_with_calc(return_id, db)
    taxpayer_data = _build_taxpayer_data(tax_return)

    calc_dict = {
        "total_income": float(calc.total_income or 0),
        "agi": float(calc.agi or 0),
        "taxable_income": float(calc.taxable_income or 0),
        "total_tax": float(calc.total_tax or 0),
        "total_credits": float(calc.total_credits or 0),
        "total_payments": float(calc.total_payments or 0),
        "refund_amount": float(calc.refund_amount or 0),
        "amount_owed": float(calc.amount_owed or 0),
        "effective_tax_rate": float(calc.effective_tax_rate or 0),
        "marginal_tax_rate": float(calc.marginal_tax_rate or 0),
        "standard_deduction_amount": float(calc.standard_deduction_amount or 0),
        "itemized_deduction_amount": float(calc.itemized_deduction_amount or 0),
        "deduction_method": calc.deduction_method,
        "form_results": calc.form_results or {},
        "required_forms": calc.required_forms or ["form_1040"],
    }

    builder = SummaryReportBuilder()
    pdf_bytes = builder.build(calc_dict, taxpayer_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="tax_return_{return_id}_summary.pdf"'
        },
    )
