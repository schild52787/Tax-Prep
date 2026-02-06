import enum

from sqlalchemy import Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class TaxpayerRole(str, enum.Enum):
    PRIMARY = "primary"
    SPOUSE = "spouse"


class Taxpayer(Base, TimestampMixin):
    __tablename__ = "taxpayers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[TaxpayerRole] = mapped_column(Enum(TaxpayerRole), nullable=False)

    first_name: Mapped[str | None] = mapped_column(String(50))
    middle_initial: Mapped[str | None] = mapped_column(String(1))
    last_name: Mapped[str | None] = mapped_column(String(50))
    ssn_encrypted: Mapped[str | None] = mapped_column(String(200))
    date_of_birth: Mapped[str | None] = mapped_column(Date)
    occupation: Mapped[str | None] = mapped_column(String(100))

    # Address (primary taxpayer only)
    street_address: Mapped[str | None] = mapped_column(String(200))
    apt_number: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(2))
    zip_code: Mapped[str | None] = mapped_column(String(10))

    tax_return: Mapped["TaxReturn"] = relationship(back_populates="taxpayers")  # noqa: F821


class Dependent(Base, TimestampMixin):
    __tablename__ = "dependents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    return_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tax_returns.id", ondelete="CASCADE"), nullable=False
    )

    first_name: Mapped[str | None] = mapped_column(String(50))
    last_name: Mapped[str | None] = mapped_column(String(50))
    ssn_encrypted: Mapped[str | None] = mapped_column(String(200))
    relationship_to_taxpayer: Mapped[str | None] = mapped_column(String(50))
    date_of_birth: Mapped[str | None] = mapped_column(Date)
    months_lived_with: Mapped[int | None] = mapped_column(Integer, default=12)
    is_student: Mapped[bool] = mapped_column(default=False)
    is_disabled: Mapped[bool] = mapped_column(default=False)

    tax_return: Mapped["TaxReturn"] = relationship(back_populates="dependents")  # noqa: F821
