from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class EducationExpense(Base, TimestampMixin):
    """Form 8863 - Education Credits (AOTC / LLC)"""

    __tablename__ = "education_expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )

    student_name: Mapped[str | None] = mapped_column(String(100))
    student_ssn_encrypted: Mapped[str | None] = mapped_column(String(200))
    institution_name: Mapped[str | None] = mapped_column(String(200))
    institution_ein: Mapped[str | None] = mapped_column(String(20))
    qualified_expenses: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    scholarships_received: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    is_first_four_years: Mapped[bool] = mapped_column(default=True)
    is_at_least_half_time: Mapped[bool] = mapped_column(default=True)
    has_felony_drug_conviction: Mapped[bool] = mapped_column(default=False)
    credit_type: Mapped[str] = mapped_column(String(10), default="aotc")  # "aotc" or "llc"

    tax_return: Mapped["TaxReturn"] = relationship(  # noqa: F821
        back_populates="education_expenses"
    )


class RetirementContribution(Base, TimestampMixin):
    """Form 8880 - Retirement Savings Contributions Credit"""

    __tablename__ = "retirement_contributions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )

    contributor: Mapped[str] = mapped_column(String(10), default="primary")  # "primary" or "spouse"
    traditional_ira: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    roth_ira: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    employer_401k: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    employer_403b: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    employer_457: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    employer_tsp: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    simple_ira: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    tax_return: Mapped["TaxReturn"] = relationship(  # noqa: F821
        back_populates="retirement_contributions"
    )
