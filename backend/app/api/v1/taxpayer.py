from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tax_return import TaxReturn
from app.models.taxpayer import Dependent, Taxpayer, TaxpayerRole
from app.schemas.taxpayer import (
    DependentCreate,
    DependentResponse,
    DependentUpdate,
    TaxpayerCreate,
    TaxpayerResponse,
    TaxpayerUpdate,
)

router = APIRouter(prefix="/returns/{return_id}/taxpayer", tags=["Taxpayer"])


async def _get_return(return_id: str, db: AsyncSession) -> TaxReturn:
    tax_return = await db.get(TaxReturn, return_id)
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    return tax_return


async def _upsert_taxpayer(
    return_id: str, role: TaxpayerRole, data: TaxpayerCreate, db: AsyncSession
) -> Taxpayer:
    await _get_return(return_id, db)

    result = await db.execute(
        select(Taxpayer).where(
            Taxpayer.return_id == return_id, Taxpayer.role == role
        )
    )
    taxpayer = result.scalar_one_or_none()

    if taxpayer is None:
        taxpayer = Taxpayer(return_id=return_id, role=role)
        db.add(taxpayer)

    update_data = data.model_dump(exclude_unset=True)
    ssn = update_data.pop("ssn", None)
    if ssn is not None:
        # TODO: Encrypt SSN before storage
        taxpayer.ssn_encrypted = ssn.replace("-", "")

    for field, value in update_data.items():
        setattr(taxpayer, field, value)

    await db.flush()
    return taxpayer


@router.put("/primary", response_model=TaxpayerResponse)
async def upsert_primary(
    return_id: str, data: TaxpayerCreate, db: AsyncSession = Depends(get_db)
):
    return await _upsert_taxpayer(return_id, TaxpayerRole.PRIMARY, data, db)


@router.put("/spouse", response_model=TaxpayerResponse)
async def upsert_spouse(
    return_id: str, data: TaxpayerCreate, db: AsyncSession = Depends(get_db)
):
    return await _upsert_taxpayer(return_id, TaxpayerRole.SPOUSE, data, db)


@router.get("/primary", response_model=TaxpayerResponse)
async def get_primary(return_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Taxpayer).where(
            Taxpayer.return_id == return_id, Taxpayer.role == TaxpayerRole.PRIMARY
        )
    )
    taxpayer = result.scalar_one_or_none()
    if not taxpayer:
        raise HTTPException(status_code=404, detail="Primary taxpayer not found")
    return taxpayer


@router.get("/spouse", response_model=TaxpayerResponse)
async def get_spouse(return_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Taxpayer).where(
            Taxpayer.return_id == return_id, Taxpayer.role == TaxpayerRole.SPOUSE
        )
    )
    taxpayer = result.scalar_one_or_none()
    if not taxpayer:
        raise HTTPException(status_code=404, detail="Spouse not found")
    return taxpayer


# --- Dependents ---

@router.post("/dependents", response_model=DependentResponse, status_code=201)
async def add_dependent(
    return_id: str, data: DependentCreate, db: AsyncSession = Depends(get_db)
):
    await _get_return(return_id, db)

    dependent = Dependent(return_id=return_id)
    update_data = data.model_dump(exclude_unset=True)
    ssn = update_data.pop("ssn", None)
    if ssn is not None:
        dependent.ssn_encrypted = ssn.replace("-", "")

    for field, value in update_data.items():
        setattr(dependent, field, value)

    db.add(dependent)
    await db.flush()
    return dependent


@router.get("/dependents", response_model=list[DependentResponse])
async def list_dependents(return_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Dependent).where(Dependent.return_id == return_id)
    )
    return result.scalars().all()


@router.put("/dependents/{dep_id}", response_model=DependentResponse)
async def update_dependent(
    return_id: str, dep_id: str, data: DependentUpdate, db: AsyncSession = Depends(get_db)
):
    dependent = await db.get(Dependent, dep_id)
    if not dependent or dependent.return_id != return_id:
        raise HTTPException(status_code=404, detail="Dependent not found")

    update_data = data.model_dump(exclude_unset=True)
    ssn = update_data.pop("ssn", None)
    if ssn is not None:
        dependent.ssn_encrypted = ssn.replace("-", "")

    for field, value in update_data.items():
        setattr(dependent, field, value)

    await db.flush()
    return dependent


@router.delete("/dependents/{dep_id}", status_code=204)
async def delete_dependent(
    return_id: str, dep_id: str, db: AsyncSession = Depends(get_db)
):
    dependent = await db.get(Dependent, dep_id)
    if not dependent or dependent.return_id != return_id:
        raise HTTPException(status_code=404, detail="Dependent not found")
    await db.delete(dependent)
