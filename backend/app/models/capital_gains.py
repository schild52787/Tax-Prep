import enum

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class HoldingPeriod(str, enum.Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class CapitalAssetSale(Base, TimestampMixin):
    __tablename__ = "capital_asset_sales"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )

    description: Mapped[str | None] = mapped_column(String(200))
    date_acquired: Mapped[str | None] = mapped_column(Date)
    date_sold: Mapped[str | None] = mapped_column(Date)
    proceeds: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    cost_basis: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    adjustment_code: Mapped[str | None] = mapped_column(String(10))
    adjustment_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    holding_period: Mapped[HoldingPeriod | None] = mapped_column(Enum(HoldingPeriod))
    basis_reported_to_irs: Mapped[bool] = mapped_column(Boolean, default=True)
    brokerage_name: Mapped[str | None] = mapped_column(String(200))

    tax_return: Mapped["TaxReturn"] = relationship(  # noqa: F821
        back_populates="capital_asset_sales"
    )
