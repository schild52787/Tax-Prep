from datetime import datetime

from pydantic import BaseModel


class CalculationResultResponse(BaseModel):
    id: str
    return_id: str
    calculated_at: datetime

    # Summary figures
    total_income: float
    agi: float
    taxable_income: float
    total_tax: float
    total_credits: float
    total_payments: float
    refund_amount: float
    amount_owed: float
    effective_tax_rate: float
    marginal_tax_rate: float

    # Deduction info
    standard_deduction_amount: float
    itemized_deduction_amount: float
    deduction_method: str | None

    # Detailed results
    form_results: dict | None
    required_forms: list[str] | None
    errors: list | None
    warnings: list | None

    model_config = {"from_attributes": True}


class CalculationSummary(BaseModel):
    total_income: float
    agi: float
    taxable_income: float
    total_tax: float
    refund_amount: float
    amount_owed: float
    effective_tax_rate: float
    deduction_method: str | None
