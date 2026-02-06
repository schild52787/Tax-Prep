from datetime import date

from pydantic import BaseModel, Field


class W2Create(BaseModel):
    employer_name: str | None = Field(None, max_length=200)
    employer_ein: str | None = Field(None, max_length=20)
    employer_address: str | None = Field(None, max_length=300)
    box_1_wages: float = 0
    box_2_fed_tax_withheld: float = 0
    box_3_ss_wages: float = 0
    box_4_ss_tax: float = 0
    box_5_medicare_wages: float = 0
    box_6_medicare_tax: float = 0
    box_7_ss_tips: float = 0
    box_8_allocated_tips: float = 0
    box_10_dependent_care: float = 0
    box_11_nonqual_plans: float = 0
    box_12_codes: list[dict] | None = None
    box_13_statutory: bool = False
    box_13_retirement: bool = False
    box_13_third_party_sick: bool = False
    box_14_other: list[dict] | None = None
    state: str | None = Field(None, max_length=2)
    state_employer_id: str | None = Field(None, max_length=30)
    state_wages: float = 0
    state_tax_withheld: float = 0
    local_wages: float = 0
    local_tax_withheld: float = 0


class W2Update(W2Create):
    pass


class W2Response(BaseModel):
    id: str
    return_id: str
    employer_name: str | None
    employer_ein: str | None
    employer_address: str | None
    box_1_wages: float
    box_2_fed_tax_withheld: float
    box_3_ss_wages: float
    box_4_ss_tax: float
    box_5_medicare_wages: float
    box_6_medicare_tax: float
    box_7_ss_tips: float
    box_8_allocated_tips: float
    box_10_dependent_care: float
    box_11_nonqual_plans: float
    box_12_codes: list[dict] | None
    box_13_statutory: bool
    box_13_retirement: bool
    box_13_third_party_sick: bool
    box_14_other: list[dict] | None
    state: str | None
    state_employer_id: str | None
    state_wages: float
    state_tax_withheld: float
    local_wages: float
    local_tax_withheld: float

    model_config = {"from_attributes": True}


class Interest1099Create(BaseModel):
    payer_name: str | None = Field(None, max_length=200)
    box_1_interest: float = 0
    box_2_early_withdrawal_penalty: float = 0
    box_3_us_savings_bond: float = 0
    box_4_fed_tax_withheld: float = 0
    box_8_tax_exempt_interest: float = 0


class Interest1099Update(Interest1099Create):
    pass


class Interest1099Response(BaseModel):
    id: str
    return_id: str
    payer_name: str | None
    box_1_interest: float
    box_2_early_withdrawal_penalty: float
    box_3_us_savings_bond: float
    box_4_fed_tax_withheld: float
    box_8_tax_exempt_interest: float

    model_config = {"from_attributes": True}


class Dividend1099Create(BaseModel):
    payer_name: str | None = Field(None, max_length=200)
    box_1a_ordinary_dividends: float = 0
    box_1b_qualified_dividends: float = 0
    box_2a_total_capital_gain: float = 0
    box_2b_unrecaptured_1250: float = 0
    box_2c_section_1202: float = 0
    box_2d_collectibles_gain: float = 0
    box_3_nondividend_distributions: float = 0
    box_4_fed_tax_withheld: float = 0
    box_5_section_199a: float = 0
    box_6_investment_expenses: float = 0
    box_7_foreign_tax_paid: float = 0
    box_11_exempt_interest_dividends: float = 0


class Dividend1099Update(Dividend1099Create):
    pass


class Dividend1099Response(BaseModel):
    id: str
    return_id: str
    payer_name: str | None
    box_1a_ordinary_dividends: float
    box_1b_qualified_dividends: float
    box_2a_total_capital_gain: float
    box_4_fed_tax_withheld: float
    box_7_foreign_tax_paid: float

    model_config = {"from_attributes": True}


class CapitalAssetSaleCreate(BaseModel):
    description: str | None = Field(None, max_length=200)
    date_acquired: date | None = None
    date_sold: date | None = None
    proceeds: float = 0
    cost_basis: float = 0
    adjustment_code: str | None = Field(None, max_length=10)
    adjustment_amount: float = 0
    holding_period: str | None = None  # "short_term" or "long_term"
    basis_reported_to_irs: bool = True
    brokerage_name: str | None = Field(None, max_length=200)


class CapitalAssetSaleUpdate(CapitalAssetSaleCreate):
    pass


class CapitalAssetSaleResponse(BaseModel):
    id: str
    return_id: str
    description: str | None
    date_acquired: date | None
    date_sold: date | None
    proceeds: float
    cost_basis: float
    adjustment_code: str | None
    adjustment_amount: float
    holding_period: str | None
    basis_reported_to_irs: bool
    brokerage_name: str | None

    model_config = {"from_attributes": True}
