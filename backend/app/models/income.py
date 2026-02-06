from sqlalchemy import JSON, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class W2Income(Base, TimestampMixin):
    __tablename__ = "w2_incomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )

    employer_name: Mapped[str | None] = mapped_column(String(200))
    employer_ein: Mapped[str | None] = mapped_column(String(20))
    employer_address: Mapped[str | None] = mapped_column(String(300))

    # Box values
    box_1_wages: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_2_fed_tax_withheld: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_3_ss_wages: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_4_ss_tax: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_5_medicare_wages: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_6_medicare_tax: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_7_ss_tips: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_8_allocated_tips: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_10_dependent_care: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_11_nonqual_plans: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_12_codes: Mapped[dict | None] = mapped_column(JSON)
    box_13_statutory: Mapped[bool] = mapped_column(default=False)
    box_13_retirement: Mapped[bool] = mapped_column(default=False)
    box_13_third_party_sick: Mapped[bool] = mapped_column(default=False)
    box_14_other: Mapped[dict | None] = mapped_column(JSON)

    # State info
    state: Mapped[str | None] = mapped_column(String(2))
    state_employer_id: Mapped[str | None] = mapped_column(String(30))
    state_wages: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    state_tax_withheld: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    local_wages: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    local_tax_withheld: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    tax_return: Mapped["TaxReturn"] = relationship(back_populates="w2_incomes")  # noqa: F821


class Interest1099(Base, TimestampMixin):
    __tablename__ = "interest_1099s"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )

    payer_name: Mapped[str | None] = mapped_column(String(200))
    box_1_interest: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_2_early_withdrawal_penalty: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_3_us_savings_bond: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_4_fed_tax_withheld: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_8_tax_exempt_interest: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    tax_return: Mapped["TaxReturn"] = relationship(back_populates="interest_1099s")  # noqa: F821


class Dividend1099(Base, TimestampMixin):
    __tablename__ = "dividend_1099s"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )

    payer_name: Mapped[str | None] = mapped_column(String(200))
    box_1a_ordinary_dividends: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_1b_qualified_dividends: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_2a_total_capital_gain: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_2b_unrecaptured_1250: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_2c_section_1202: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_2d_collectibles_gain: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_3_nondividend_distributions: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_4_fed_tax_withheld: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_5_section_199a: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_6_investment_expenses: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_7_foreign_tax_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_11_exempt_interest_dividends: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    tax_return: Mapped["TaxReturn"] = relationship(back_populates="dividend_1099s")  # noqa: F821


class Retirement1099R(Base, TimestampMixin):
    __tablename__ = "retirement_1099rs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )

    payer_name: Mapped[str | None] = mapped_column(String(200))
    box_1_gross_distribution: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_2a_taxable_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_2b_taxable_not_determined: Mapped[bool] = mapped_column(default=False)
    box_2b_total_distribution: Mapped[bool] = mapped_column(default=False)
    box_4_fed_tax_withheld: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_7_distribution_code: Mapped[str | None] = mapped_column(String(10))
    box_7_ira_sep_simple: Mapped[bool] = mapped_column(default=False)

    tax_return: Mapped["TaxReturn"] = relationship(  # noqa: F821
        back_populates="retirement_1099rs"
    )


class Government1099G(Base, TimestampMixin):
    __tablename__ = "government_1099gs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )

    payer_name: Mapped[str | None] = mapped_column(String(200))
    box_1_unemployment: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_2_state_tax_refund: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_4_fed_tax_withheld: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    tax_return: Mapped["TaxReturn"] = relationship(  # noqa: F821
        back_populates="government_1099gs"
    )


class SSA1099(Base, TimestampMixin):
    __tablename__ = "ssa_1099s"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )

    box_3_benefits_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_4_benefits_repaid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_5_net_benefits: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    box_6_voluntary_withholding: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    tax_return: Mapped["TaxReturn"] = relationship(back_populates="ssa_1099s")  # noqa: F821
