from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid


class CalculationResult(Base):
    __tablename__ = "calculation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    calculated_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())

    # Summary figures
    total_income: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    agi: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    taxable_income: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_tax: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_credits: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_payments: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    refund_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount_owed: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    effective_tax_rate: Mapped[float] = mapped_column(Numeric(6, 4), default=0)
    marginal_tax_rate: Mapped[float] = mapped_column(Numeric(6, 4), default=0)

    # Deduction info
    standard_deduction_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    itemized_deduction_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    deduction_method: Mapped[str | None] = mapped_column(String(20))  # "standard" or "itemized"

    # Detailed form results: {form_id: {line_id: value}}
    form_results: Mapped[dict | None] = mapped_column(JSON)
    required_forms: Mapped[list | None] = mapped_column(JSON)

    # Validation
    errors: Mapped[list | None] = mapped_column(JSON, default=list)
    warnings: Mapped[list | None] = mapped_column(JSON, default=list)

    tax_return: Mapped["TaxReturn"] = relationship(  # noqa: F821
        back_populates="calculation_result"
    )
