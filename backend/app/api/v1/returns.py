from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tax_return import InterviewProgress, TaxReturn
from app.schemas.tax_return import (
    TaxReturnCreate,
    TaxReturnResponse,
    TaxReturnSummary,
    TaxReturnUpdate,
)

router = APIRouter(prefix="/returns", tags=["Tax Returns"])


@router.post("/", response_model=TaxReturnResponse, status_code=201)
async def create_return(data: TaxReturnCreate, db: AsyncSession = Depends(get_db)):
    tax_return = TaxReturn(
        return_name=data.return_name,
        tax_year=data.tax_year,
        filing_status=data.filing_status,
    )
    db.add(tax_return)
    await db.flush()

    # Initialize interview progress
    progress = InterviewProgress(return_id=tax_return.id)
    db.add(progress)
    await db.flush()

    return tax_return


@router.get("/", response_model=list[TaxReturnSummary])
async def list_returns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaxReturn).order_by(TaxReturn.created_at.desc()))
    return result.scalars().all()


@router.get("/{return_id}", response_model=TaxReturnResponse)
async def get_return(return_id: str, db: AsyncSession = Depends(get_db)):
    tax_return = await db.get(TaxReturn, return_id)
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    return tax_return


@router.patch("/{return_id}", response_model=TaxReturnResponse)
async def update_return(
    return_id: str, data: TaxReturnUpdate, db: AsyncSession = Depends(get_db)
):
    tax_return = await db.get(TaxReturn, return_id)
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tax_return, field, value)

    await db.flush()
    await db.refresh(tax_return)
    return tax_return


@router.delete("/{return_id}", status_code=204)
async def delete_return(return_id: str, db: AsyncSession = Depends(get_db)):
    tax_return = await db.get(TaxReturn, return_id)
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    await db.delete(tax_return)
