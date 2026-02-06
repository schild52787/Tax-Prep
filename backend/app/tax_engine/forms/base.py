"""Base class for all tax form calculations."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTaxForm(ABC):
    """Abstract base class for tax form calculators.

    Each IRS form/schedule is a subclass that declares its dependencies
    and implements the calculate() method to compute all line values.
    """

    # Subclasses set this to the form identifier
    form_id: str = ""

    # List of form_ids this form depends on
    dependencies: list[str] = []

    def __init__(self):
        self.lines: dict[str, Any] = {}

    @abstractmethod
    def calculate(self, return_data: dict, other_forms: dict["str", "BaseTaxForm"]) -> None:
        """Compute all line values for this form.

        Args:
            return_data: Raw tax return data from the database.
            other_forms: Dict of already-computed forms keyed by form_id.
                         Only forms listed in `dependencies` are guaranteed present.
        """
        ...

    def get_line(self, line_id: str, default: float = 0) -> float:
        """Get a computed line value."""
        return float(self.lines.get(line_id, default))

    def set_line(self, line_id: str, value: float) -> None:
        """Store a computed line value."""
        self.lines[line_id] = round(value, 2)

    def get_all_lines(self) -> dict[str, float]:
        """Return all computed line values."""
        return dict(self.lines)
