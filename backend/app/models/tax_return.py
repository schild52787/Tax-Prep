from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid

import enum


class FilingStatus(str, enum.Enum):
    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "married_filing_jointly"


class ReturnStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaxReturn(Base, TimestampMixin):
    __tablename__ = "tax_returns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_year: Mapped[int] = mapped_column(nullable=False, default=2025)
    filing_status: Mapped[FilingStatus] = mapped_column(
        Enum(FilingStatus), nullable=False, default=FilingStatus.SINGLE
    )
    status: Mapped[ReturnStatus] = mapped_column(
        Enum(ReturnStatus), nullable=False, default=ReturnStatus.IN_PROGRESS
    )

    # Relationships
    taxpayers: Mapped[list["Taxpayer"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    dependents: Mapped[list["Dependent"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    w2_incomes: Mapped[list["W2Income"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    interest_1099s: Mapped[list["Interest1099"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    dividend_1099s: Mapped[list["Dividend1099"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    retirement_1099rs: Mapped[list["Retirement1099R"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    government_1099gs: Mapped[list["Government1099G"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    ssa_1099s: Mapped[list["SSA1099"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    capital_asset_sales: Mapped[list["CapitalAssetSale"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    itemized_deduction: Mapped["ItemizedDeduction | None"] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan", uselist=False
    )
    education_expenses: Mapped[list["EducationExpense"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    retirement_contributions: Mapped[list["RetirementContribution"]] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan"
    )
    interview_progress: Mapped["InterviewProgress | None"] = relationship(
        back_populates="tax_return", cascade="all, delete-orphan", uselist=False
    )
    calculation_result: Mapped["CalculationResult | None"] = relationship(  # noqa: F821
        back_populates="tax_return", cascade="all, delete-orphan", uselist=False
    )


class InterviewProgress(Base, TimestampMixin):
    __tablename__ = "interview_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    current_section: Mapped[str] = mapped_column(String(100), default="personal_info")
    current_step_id: Mapped[str] = mapped_column(String(100), default="filing_status")
    completed_steps: Mapped[dict | None] = mapped_column(JSON, default=list)
    answers: Mapped[dict | None] = mapped_column(JSON, default=dict)
    navigation_stack: Mapped[dict | None] = mapped_column(JSON, default=list)

    tax_return: Mapped["TaxReturn"] = relationship(back_populates="interview_progress")
