"""Tax calculation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.calculation import CalculationResult
from app.models.tax_return import TaxReturn
from app.schemas.calculation import CalculationResultResponse
from app.tax_engine.engine import TaxEngine

router = APIRouter(prefix="/returns/{return_id}", tags=["calculations"])


async def _load_return(return_id: str, db: AsyncSession) -> TaxReturn:
    """Load a tax return with all relationships eagerly loaded."""
    result = await db.execute(
        select(TaxReturn)
        .where(TaxReturn.id == return_id)
        .options(
            selectinload(TaxReturn.taxpayers),
            selectinload(TaxReturn.dependents),
            selectinload(TaxReturn.w2_incomes),
            selectinload(TaxReturn.interest_1099s),
            selectinload(TaxReturn.dividend_1099s),
            selectinload(TaxReturn.retirement_1099rs),
            selectinload(TaxReturn.government_1099gs),
            selectinload(TaxReturn.ssa_1099s),
            selectinload(TaxReturn.capital_asset_sales),
            selectinload(TaxReturn.itemized_deduction),
            selectinload(TaxReturn.education_expenses),
            selectinload(TaxReturn.retirement_contributions),
            selectinload(TaxReturn.calculation_result),
        )
    )
    tax_return = result.scalar_one_or_none()
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    return tax_return


def _build_return_data(tax_return: TaxReturn) -> dict:
    """Convert ORM model into the dict format expected by TaxEngine."""
    return {
        "filing_status": tax_return.filing_status.value,
        "w2_incomes": [
            {
                "box_1_wages": float(w2.box_1_wages or 0),
                "box_2_fed_tax_withheld": float(w2.box_2_fed_tax_withheld or 0),
                "box_3_ss_wages": float(w2.box_3_ss_wages or 0),
                "box_4_ss_tax": float(w2.box_4_ss_tax or 0),
                "box_5_medicare_wages": float(w2.box_5_medicare_wages or 0),
                "box_6_medicare_tax": float(w2.box_6_medicare_tax or 0),
            }
            for w2 in tax_return.w2_incomes
        ],
        "interest_1099s": [
            {
                "payer_name": i.payer_name or "",
                "box_1_interest": float(i.box_1_interest or 0),
                "box_2_early_withdrawal_penalty": float(i.box_2_early_withdrawal_penalty or 0),
                "box_3_us_savings_bond": float(i.box_3_us_savings_bond or 0),
                "box_4_fed_tax_withheld": float(i.box_4_fed_tax_withheld or 0),
                "box_8_tax_exempt_interest": float(i.box_8_tax_exempt_interest or 0),
            }
            for i in tax_return.interest_1099s
        ],
        "dividend_1099s": [
            {
                "payer_name": d.payer_name or "",
                "box_1a_ordinary_dividends": float(d.box_1a_ordinary_dividends or 0),
                "box_1b_qualified_dividends": float(d.box_1b_qualified_dividends or 0),
                "box_2a_total_capital_gain": float(d.box_2a_total_capital_gain or 0),
                "box_4_fed_tax_withheld": float(d.box_4_fed_tax_withheld or 0),
                "box_7_foreign_tax_paid": float(d.box_7_foreign_tax_paid or 0),
            }
            for d in tax_return.dividend_1099s
        ],
        "retirement_1099rs": [
            {
                "box_1_gross_distribution": float(r.box_1_gross_distribution or 0),
                "box_2a_taxable_amount": float(r.box_2a_taxable_amount or 0),
                "box_4_fed_tax_withheld": float(r.box_4_fed_tax_withheld or 0),
            }
            for r in tax_return.retirement_1099rs
        ],
        "government_1099gs": [
            {
                "box_1_unemployment": float(g.box_1_unemployment or 0),
                "box_2_state_tax_refund": float(g.box_2_state_tax_refund or 0),
                "box_4_fed_tax_withheld": float(g.box_4_fed_tax_withheld or 0),
            }
            for g in tax_return.government_1099gs
        ],
        "ssa_1099s": [
            {
                "box_5_net_benefits": float(s.box_5_net_benefits or 0),
                "box_6_voluntary_withholding": float(s.box_6_voluntary_withholding or 0),
            }
            for s in tax_return.ssa_1099s
        ],
        "capital_asset_sales": [
            {
                "description": sale.description or "",
                "date_acquired": str(sale.date_acquired) if sale.date_acquired else "",
                "date_sold": str(sale.date_sold) if sale.date_sold else "",
                "proceeds": float(sale.proceeds or 0),
                "cost_basis": float(sale.cost_basis or 0),
                "adjustment_code": sale.adjustment_code or "",
                "adjustment_amount": float(sale.adjustment_amount or 0),
                "holding_period": sale.holding_period.value if sale.holding_period else "short_term",
                "basis_reported_to_irs": sale.basis_reported_to_irs,
            }
            for sale in tax_return.capital_asset_sales
        ],
        "itemized_deduction": (
            {
                "medical_expenses": float(tax_return.itemized_deduction.medical_expenses or 0),
                "state_income_tax_paid": float(
                    tax_return.itemized_deduction.state_income_tax_paid or 0
                ),
                "real_estate_tax_paid": float(
                    tax_return.itemized_deduction.real_estate_tax_paid or 0
                ),
                "personal_property_tax": float(
                    tax_return.itemized_deduction.personal_property_tax or 0
                ),
                "mortgage_interest_1098": float(
                    tax_return.itemized_deduction.mortgage_interest_1098 or 0
                ),
                "mortgage_interest_not_1098": float(
                    tax_return.itemized_deduction.mortgage_interest_not_1098 or 0
                ),
                "mortgage_points": float(tax_return.itemized_deduction.mortgage_points or 0),
                "investment_interest": float(
                    tax_return.itemized_deduction.investment_interest or 0
                ),
                "cash_charitable": float(tax_return.itemized_deduction.cash_charitable or 0),
                "noncash_charitable": float(tax_return.itemized_deduction.noncash_charitable or 0),
                "carryover_charitable": float(
                    tax_return.itemized_deduction.carryover_charitable or 0
                ),
                "casualty_loss": float(tax_return.itemized_deduction.casualty_loss or 0),
                "other_deductions": float(tax_return.itemized_deduction.other_deductions or 0),
            }
            if tax_return.itemized_deduction
            else None
        ),
        "dependents": [
            {
                "first_name": dep.first_name or "",
                "last_name": dep.last_name or "",
                "date_of_birth": str(dep.date_of_birth) if dep.date_of_birth else "",
                "relationship": dep.relationship_to_taxpayer or "",
                "months_lived_with": dep.months_lived_with or 12,
            }
            for dep in tax_return.dependents
        ],
    }


def _build_taxpayer_data(tax_return: TaxReturn) -> dict:
    """Build taxpayer data dict for PDF generation."""
    data: dict = {"filing_status": tax_return.filing_status.value}

    for tp in tax_return.taxpayers:
        role = tp.role or "primary"
        data[role] = {
            "first_name": tp.first_name or "",
            "middle_initial": tp.middle_initial or "",
            "last_name": tp.last_name or "",
            "ssn": tp.ssn_encrypted or "",  # In production, decrypt here
            "occupation": tp.occupation or "",
            "street_address": tp.street_address or "",
            "apt_number": tp.apt_number or "",
            "city": tp.city or "",
            "state": tp.state or "",
            "zip_code": tp.zip_code or "",
        }

    return data


@router.post("/calculate", response_model=CalculationResultResponse)
async def run_calculation(return_id: str, db: AsyncSession = Depends(get_db)):
    """Run the tax engine on a return and save/update the calculation result."""
    tax_return = await _load_return(return_id, db)
    return_data = _build_return_data(tax_return)

    # Run tax engine
    engine = TaxEngine()
    calc_result = engine.calculate(return_data)

    # Upsert calculation result
    if tax_return.calculation_result:
        existing = tax_return.calculation_result
        for key, value in calc_result.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
    else:
        db_calc = CalculationResult(
            return_id=return_id,
            **{k: v for k, v in calc_result.items() if hasattr(CalculationResult, k)},
        )
        db.add(db_calc)

    await db.flush()

    # Reload to get the saved object
    result = await db.execute(
        select(CalculationResult).where(CalculationResult.return_id == return_id)
    )
    saved = result.scalar_one()
    return saved


@router.get("/calculation", response_model=CalculationResultResponse)
async def get_calculation(return_id: str, db: AsyncSession = Depends(get_db)):
    """Get the most recent calculation result for a return."""
    result = await db.execute(
        select(CalculationResult).where(CalculationResult.return_id == return_id)
    )
    calc = result.scalar_one_or_none()
    if not calc:
        raise HTTPException(status_code=404, detail="No calculation found. Run /calculate first.")
    return calc
