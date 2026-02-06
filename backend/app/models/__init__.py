from app.models.base import Base
from app.models.calculation import CalculationResult
from app.models.capital_gains import CapitalAssetSale
from app.models.credits import EducationExpense, RetirementContribution
from app.models.deductions import ItemizedDeduction
from app.models.income import (
    Dividend1099,
    Government1099G,
    Interest1099,
    Retirement1099R,
    SSA1099,
    W2Income,
)
from app.models.tax_return import InterviewProgress, TaxReturn
from app.models.taxpayer import Dependent, Taxpayer

__all__ = [
    "Base",
    "TaxReturn",
    "InterviewProgress",
    "Taxpayer",
    "Dependent",
    "W2Income",
    "Interest1099",
    "Dividend1099",
    "Retirement1099R",
    "Government1099G",
    "SSA1099",
    "CapitalAssetSale",
    "ItemizedDeduction",
    "EducationExpense",
    "RetirementContribution",
    "CalculationResult",
]
