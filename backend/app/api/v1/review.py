"""Tax return validation and review API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.calculations import _build_return_data, _build_taxpayer_data, _load_return
from app.database import get_db
from app.models.calculation import CalculationResult
from app.models.credits import EducationExpense, RetirementContribution
from app.models.tax_return import TaxReturn
from app.tax_engine.engine import TaxEngine
from app.validation.validator import ReturnValidator

router = APIRouter(prefix="/returns/{return_id}", tags=["review"])


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------


class ValidationIssueResponse(BaseModel):
    severity: str
    code: str
    message: str
    field: str | None = None
    section: str | None = None


class ValidationResponse(BaseModel):
    return_id: str
    is_valid: bool
    error_count: int
    warning_count: int
    issues: list[ValidationIssueResponse]


class IncomeSummary(BaseModel):
    wages: float = 0
    taxable_interest: float = 0
    ordinary_dividends: float = 0
    retirement_income: float = 0
    social_security: float = 0
    capital_gains: float = 0
    unemployment: float = 0
    total_income: float = 0


class DeductionSummary(BaseModel):
    method: str | None = None
    standard_deduction: float = 0
    itemized_deduction: float = 0
    deduction_used: float = 0


class TaxSummary(BaseModel):
    total_tax: float = 0
    total_credits: float = 0
    total_payments: float = 0
    refund_amount: float = 0
    amount_owed: float = 0
    effective_tax_rate: float = 0
    marginal_tax_rate: float = 0


class TaxpayerSummary(BaseModel):
    role: str
    name: str
    ssn_last_four: str = ""


class ReviewSummaryResponse(BaseModel):
    return_id: str
    filing_status: str
    tax_year: int
    taxpayers: list[TaxpayerSummary]
    income: IncomeSummary
    deductions: DeductionSummary
    tax: TaxSummary
    validation: ValidationResponse
    required_forms: list[str] = []


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _enrich_return_data(tax_return: TaxReturn, return_data: dict) -> dict:
    """Add education expenses and retirement contributions to return_data.

    These relationships are loaded from the ORM but are not included in
    the standard ``_build_return_data`` dict used by the tax engine.
    The validator needs them for credit eligibility checks.
    """
    return_data["education_expenses"] = [
        {
            "student_name": exp.student_name or "",
            "student_ssn_encrypted": exp.student_ssn_encrypted or "",
            "institution_name": exp.institution_name or "",
            "qualified_expenses": float(exp.qualified_expenses or 0),
            "scholarships_received": float(exp.scholarships_received or 0),
            "is_first_four_years": exp.is_first_four_years,
            "is_at_least_half_time": exp.is_at_least_half_time,
            "has_felony_drug_conviction": exp.has_felony_drug_conviction,
            "credit_type": exp.credit_type or "aotc",
        }
        for exp in tax_return.education_expenses
    ]

    return_data["retirement_contributions"] = [
        {
            "contributor": contrib.contributor or "primary",
            "traditional_ira": float(contrib.traditional_ira or 0),
            "roth_ira": float(contrib.roth_ira or 0),
            "employer_401k": float(contrib.employer_401k or 0),
            "employer_403b": float(contrib.employer_403b or 0),
            "employer_457": float(contrib.employer_457 or 0),
            "employer_tsp": float(contrib.employer_tsp or 0),
            "simple_ira": float(contrib.simple_ira or 0),
        }
        for contrib in tax_return.retirement_contributions
    ]

    return return_data


async def _load_return_with_credits(return_id: str, db: AsyncSession) -> TaxReturn:
    """Load a tax return with all relationships including credit-related ones."""
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


def _get_calculation_dict(tax_return: TaxReturn) -> dict:
    """Convert a CalculationResult ORM object to a plain dict, or empty dict."""
    calc = tax_return.calculation_result
    if not calc:
        return {}
    return {
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
        "required_forms": calc.required_forms or [],
    }


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post("/validate", response_model=ValidationResponse)
async def validate_return(return_id: str, db: AsyncSession = Depends(get_db)):
    """Run all validation rules against a tax return and return errors/warnings.

    If no prior calculation result exists, the tax engine is run first so that
    math-consistency checks can be performed.
    """
    tax_return = await _load_return_with_credits(return_id, db)

    # Build the data dicts that the validator needs.
    return_data = _build_return_data(tax_return)
    return_data = _enrich_return_data(tax_return, return_data)
    taxpayer_data = _build_taxpayer_data(tax_return)

    # Ensure we have a calculation result for math-consistency checks.
    calc_dict = _get_calculation_dict(tax_return)
    if not calc_dict:
        # Run the engine on the fly.
        engine = TaxEngine()
        calc_dict = engine.calculate(return_data)

    # Run validation.
    validator = ReturnValidator(
        return_data=return_data,
        calculation_result=calc_dict,
        taxpayer_data=taxpayer_data,
    )
    result = validator.validate_all()

    return ValidationResponse(
        return_id=return_id,
        is_valid=result.is_valid,
        error_count=len(result.errors),
        warning_count=len(result.warnings),
        issues=[
            ValidationIssueResponse(
                severity=issue.severity,
                code=issue.code,
                message=issue.message,
                field=issue.field,
                section=issue.section,
            )
            for issue in result.issues
        ],
    )


@router.get("/review/summary", response_model=ReviewSummaryResponse)
async def get_review_summary(return_id: str, db: AsyncSession = Depends(get_db)):
    """Get a comprehensive summary of the return for final review.

    Includes taxpayer info, income breakdown, deduction details, tax summary,
    validation results, and required forms.
    """
    tax_return = await _load_return_with_credits(return_id, db)

    return_data = _build_return_data(tax_return)
    return_data = _enrich_return_data(tax_return, return_data)
    taxpayer_data = _build_taxpayer_data(tax_return)

    # Get or compute calculation.
    calc_dict = _get_calculation_dict(tax_return)
    if not calc_dict:
        engine = TaxEngine()
        calc_dict = engine.calculate(return_data)

    # Run validation.
    validator = ReturnValidator(
        return_data=return_data,
        calculation_result=calc_dict,
        taxpayer_data=taxpayer_data,
    )
    validation_result = validator.validate_all()

    # Build taxpayer summaries.
    taxpayer_summaries: list[TaxpayerSummary] = []
    for tp in tax_return.taxpayers:
        ssn = tp.ssn_encrypted or ""
        # Show only last 4 digits for display safety.
        ssn_last_four = ssn[-4:] if len(ssn) >= 4 else ""
        taxpayer_summaries.append(
            TaxpayerSummary(
                role=tp.role.value if tp.role else "primary",
                name=f"{tp.first_name or ''} {tp.last_name or ''}".strip(),
                ssn_last_four=ssn_last_four,
            )
        )

    # Build income summary from input data.
    w2s = return_data.get("w2_incomes", [])
    wages = sum(float(w.get("box_1_wages", 0)) for w in w2s)

    interest_forms = return_data.get("interest_1099s", [])
    taxable_interest = sum(float(i.get("box_1_interest", 0)) for i in interest_forms)

    dividend_forms = return_data.get("dividend_1099s", [])
    ordinary_dividends = sum(
        float(d.get("box_1a_ordinary_dividends", 0)) for d in dividend_forms
    )

    retirement_forms = return_data.get("retirement_1099rs", [])
    retirement_income = sum(
        float(r.get("box_2a_taxable_amount", 0)) for r in retirement_forms
    )

    ssa_forms = return_data.get("ssa_1099s", [])
    social_security = sum(float(s.get("box_5_net_benefits", 0)) for s in ssa_forms)

    gov_forms = return_data.get("government_1099gs", [])
    unemployment = sum(float(g.get("box_1_unemployment", 0)) for g in gov_forms)

    # Capital gains from calculation.
    form_results = calc_dict.get("form_results", {})
    form_1040_lines = form_results.get("form_1040", {})
    capital_gains = float(form_1040_lines.get("line_7", 0))

    income_summary = IncomeSummary(
        wages=wages,
        taxable_interest=taxable_interest,
        ordinary_dividends=ordinary_dividends,
        retirement_income=retirement_income,
        social_security=social_security,
        capital_gains=capital_gains,
        unemployment=unemployment,
        total_income=float(calc_dict.get("total_income", 0)),
    )

    deduction_method = calc_dict.get("deduction_method", "standard")
    std_ded = float(calc_dict.get("standard_deduction_amount", 0))
    item_ded = float(calc_dict.get("itemized_deduction_amount", 0))
    deduction_summary = DeductionSummary(
        method=deduction_method,
        standard_deduction=std_ded,
        itemized_deduction=item_ded,
        deduction_used=item_ded if deduction_method == "itemized" else std_ded,
    )

    tax_summary = TaxSummary(
        total_tax=float(calc_dict.get("total_tax", 0)),
        total_credits=float(calc_dict.get("total_credits", 0)),
        total_payments=float(calc_dict.get("total_payments", 0)),
        refund_amount=float(calc_dict.get("refund_amount", 0)),
        amount_owed=float(calc_dict.get("amount_owed", 0)),
        effective_tax_rate=float(calc_dict.get("effective_tax_rate", 0)),
        marginal_tax_rate=float(calc_dict.get("marginal_tax_rate", 0)),
    )

    validation_response = ValidationResponse(
        return_id=return_id,
        is_valid=validation_result.is_valid,
        error_count=len(validation_result.errors),
        warning_count=len(validation_result.warnings),
        issues=[
            ValidationIssueResponse(
                severity=issue.severity,
                code=issue.code,
                message=issue.message,
                field=issue.field,
                section=issue.section,
            )
            for issue in validation_result.issues
        ],
    )

    return ReviewSummaryResponse(
        return_id=return_id,
        filing_status=tax_return.filing_status.value,
        tax_year=tax_return.tax_year,
        taxpayers=taxpayer_summaries,
        income=income_summary,
        deductions=deduction_summary,
        tax=tax_summary,
        validation=validation_response,
        required_forms=calc_dict.get("required_forms", []),
    )
