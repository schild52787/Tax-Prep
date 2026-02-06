from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class ItemizedDeduction(Base, TimestampMixin):
    __tablename__ = "itemized_deductions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Medical and Dental (Schedule A, Lines 1-4)
    medical_expenses: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    # State and Local Taxes (Schedule A, Lines 5-7)
    state_income_tax_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    real_estate_tax_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    personal_property_tax: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    # Interest (Schedule A, Lines 8-10)
    mortgage_interest_1098: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    mortgage_interest_not_1098: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    mortgage_points: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    mortgage_loan_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    investment_interest: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    # Charitable (Schedule A, Lines 11-14)
    cash_charitable: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    noncash_charitable: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    carryover_charitable: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    # Casualty and Theft (Line 15)
    casualty_loss: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    # Other (Lines 16-17)
    other_deductions: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    other_deductions_description: Mapped[str | None] = mapped_column(String(500))

    tax_return: Mapped["TaxReturn"] = relationship(  # noqa: F821
        back_populates="itemized_deduction"
    )
