"""Deductions API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.deductions import ItemizedDeduction
from app.models.tax_return import TaxReturn

router = APIRouter(prefix="/returns/{return_id}/deductions", tags=["deductions"])


class ItemizedDeductionCreate(BaseModel):
    medical_expenses: float = 0
    state_income_tax_paid: float = 0
    real_estate_tax_paid: float = 0
    personal_property_tax: float = 0
    mortgage_interest_1098: float = 0
    mortgage_interest_not_1098: float = 0
    mortgage_points: float = 0
    investment_interest: float = 0
    cash_charitable: float = 0
    noncash_charitable: float = 0
    carryover_charitable: float = 0
    casualty_loss: float = 0
    other_deductions: float = 0


class ItemizedDeductionResponse(BaseModel):
    id: str
    return_id: str
    medical_expenses: float
    state_income_tax_paid: float
    real_estate_tax_paid: float
    personal_property_tax: float
    mortgage_interest_1098: float
    mortgage_interest_not_1098: float
    mortgage_points: float
    investment_interest: float
    cash_charitable: float
    noncash_charitable: float
    carryover_charitable: float
    casualty_loss: float
    other_deductions: float

    model_config = {"from_attributes": True}


@router.get("", response_model=ItemizedDeductionResponse)
async def get_deductions(return_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ItemizedDeduction).where(ItemizedDeduction.return_id == return_id)
    )
    deduction = result.scalar_one_or_none()
    if not deduction:
        raise HTTPException(status_code=404, detail="No itemized deductions found")
    return deduction


@router.put("", response_model=ItemizedDeductionResponse)
async def upsert_deductions(
    return_id: str, data: ItemizedDeductionCreate, db: AsyncSession = Depends(get_db)
):
    # Verify return exists
    tax_return = await db.get(TaxReturn, return_id)
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")

    result = await db.execute(
        select(ItemizedDeduction).where(ItemizedDeduction.return_id == return_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        for field, value in data.model_dump().items():
            setattr(existing, field, value)
        await db.flush()
        return existing
    else:
        deduction = ItemizedDeduction(return_id=return_id, **data.model_dump())
        db.add(deduction)
        await db.flush()
        return deduction


@router.delete("", status_code=204)
async def delete_deductions(return_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ItemizedDeduction).where(ItemizedDeduction.return_id == return_id)
    )
    deduction = result.scalar_one_or_none()
    if deduction:
        await db.delete(deduction)
