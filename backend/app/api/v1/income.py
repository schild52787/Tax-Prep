from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.capital_gains import CapitalAssetSale
from app.models.income import Dividend1099, Interest1099, W2Income
from app.models.tax_return import TaxReturn
from app.schemas.income import (
    CapitalAssetSaleCreate,
    CapitalAssetSaleResponse,
    CapitalAssetSaleUpdate,
    Dividend1099Create,
    Dividend1099Response,
    Dividend1099Update,
    Interest1099Create,
    Interest1099Response,
    Interest1099Update,
    W2Create,
    W2Response,
    W2Update,
)

router = APIRouter(prefix="/returns/{return_id}/income", tags=["Income"])


async def _get_return(return_id: str, db: AsyncSession) -> TaxReturn:
    tax_return = await db.get(TaxReturn, return_id)
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    return tax_return


# ---- W-2 ----

@router.post("/w2", response_model=W2Response, status_code=201)
async def add_w2(return_id: str, data: W2Create, db: AsyncSession = Depends(get_db)):
    await _get_return(return_id, db)
    w2 = W2Income(return_id=return_id, **data.model_dump())
    db.add(w2)
    await db.flush()
    return w2


@router.get("/w2", response_model=list[W2Response])
async def list_w2s(return_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(W2Income).where(W2Income.return_id == return_id))
    return result.scalars().all()


@router.get("/w2/{w2_id}", response_model=W2Response)
async def get_w2(return_id: str, w2_id: str, db: AsyncSession = Depends(get_db)):
    w2 = await db.get(W2Income, w2_id)
    if not w2 or w2.return_id != return_id:
        raise HTTPException(status_code=404, detail="W-2 not found")
    return w2


@router.put("/w2/{w2_id}", response_model=W2Response)
async def update_w2(
    return_id: str, w2_id: str, data: W2Update, db: AsyncSession = Depends(get_db)
):
    w2 = await db.get(W2Income, w2_id)
    if not w2 or w2.return_id != return_id:
        raise HTTPException(status_code=404, detail="W-2 not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(w2, field, value)
    await db.flush()
    return w2


@router.delete("/w2/{w2_id}", status_code=204)
async def delete_w2(return_id: str, w2_id: str, db: AsyncSession = Depends(get_db)):
    w2 = await db.get(W2Income, w2_id)
    if not w2 or w2.return_id != return_id:
        raise HTTPException(status_code=404, detail="W-2 not found")
    await db.delete(w2)


# ---- 1099-INT ----

@router.post("/1099-int", response_model=Interest1099Response, status_code=201)
async def add_1099_int(
    return_id: str, data: Interest1099Create, db: AsyncSession = Depends(get_db)
):
    await _get_return(return_id, db)
    record = Interest1099(return_id=return_id, **data.model_dump())
    db.add(record)
    await db.flush()
    return record


@router.get("/1099-int", response_model=list[Interest1099Response])
async def list_1099_ints(return_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Interest1099).where(Interest1099.return_id == return_id)
    )
    return result.scalars().all()


@router.put("/1099-int/{item_id}", response_model=Interest1099Response)
async def update_1099_int(
    return_id: str, item_id: str, data: Interest1099Update, db: AsyncSession = Depends(get_db)
):
    record = await db.get(Interest1099, item_id)
    if not record or record.return_id != return_id:
        raise HTTPException(status_code=404, detail="1099-INT not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.flush()
    return record


@router.delete("/1099-int/{item_id}", status_code=204)
async def delete_1099_int(
    return_id: str, item_id: str, db: AsyncSession = Depends(get_db)
):
    record = await db.get(Interest1099, item_id)
    if not record or record.return_id != return_id:
        raise HTTPException(status_code=404, detail="1099-INT not found")
    await db.delete(record)


# ---- 1099-DIV ----

@router.post("/1099-div", response_model=Dividend1099Response, status_code=201)
async def add_1099_div(
    return_id: str, data: Dividend1099Create, db: AsyncSession = Depends(get_db)
):
    await _get_return(return_id, db)
    record = Dividend1099(return_id=return_id, **data.model_dump())
    db.add(record)
    await db.flush()
    return record


@router.get("/1099-div", response_model=list[Dividend1099Response])
async def list_1099_divs(return_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Dividend1099).where(Dividend1099.return_id == return_id)
    )
    return result.scalars().all()


@router.put("/1099-div/{item_id}", response_model=Dividend1099Response)
async def update_1099_div(
    return_id: str, item_id: str, data: Dividend1099Update, db: AsyncSession = Depends(get_db)
):
    record = await db.get(Dividend1099, item_id)
    if not record or record.return_id != return_id:
        raise HTTPException(status_code=404, detail="1099-DIV not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.flush()
    return record


@router.delete("/1099-div/{item_id}", status_code=204)
async def delete_1099_div(
    return_id: str, item_id: str, db: AsyncSession = Depends(get_db)
):
    record = await db.get(Dividend1099, item_id)
    if not record or record.return_id != return_id:
        raise HTTPException(status_code=404, detail="1099-DIV not found")
    await db.delete(record)


# ---- Capital Asset Sales (1099-B) ----

@router.post("/capital-sales", response_model=CapitalAssetSaleResponse, status_code=201)
async def add_capital_sale(
    return_id: str, data: CapitalAssetSaleCreate, db: AsyncSession = Depends(get_db)
):
    await _get_return(return_id, db)
    record = CapitalAssetSale(return_id=return_id, **data.model_dump())
    db.add(record)
    await db.flush()
    return record


@router.get("/capital-sales", response_model=list[CapitalAssetSaleResponse])
async def list_capital_sales(return_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CapitalAssetSale).where(CapitalAssetSale.return_id == return_id)
    )
    return result.scalars().all()


@router.put("/capital-sales/{item_id}", response_model=CapitalAssetSaleResponse)
async def update_capital_sale(
    return_id: str, item_id: str, data: CapitalAssetSaleUpdate,
    db: AsyncSession = Depends(get_db),
):
    record = await db.get(CapitalAssetSale, item_id)
    if not record or record.return_id != return_id:
        raise HTTPException(status_code=404, detail="Capital sale not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.flush()
    return record


@router.delete("/capital-sales/{item_id}", status_code=204)
async def delete_capital_sale(
    return_id: str, item_id: str, db: AsyncSession = Depends(get_db)
):
    record = await db.get(CapitalAssetSale, item_id)
    if not record or record.return_id != return_id:
        raise HTTPException(status_code=404, detail="Capital sale not found")
    await db.delete(record)
