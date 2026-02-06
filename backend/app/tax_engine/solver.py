"""Dependency-resolving tax form solver.

Topologically sorts forms by their declared dependencies and
computes them in the correct order.
"""

from app.tax_engine.forms.base import BaseTaxForm


class TaxFormSolver:
    """Resolves dependencies between tax forms and computes them in order."""

    def __init__(self):
        self.registry: dict[str, BaseTaxForm] = {}

    def register(self, form: BaseTaxForm) -> None:
        self.registry[form.form_id] = form

    def solve(self, return_data: dict) -> dict[str, BaseTaxForm]:
        """Compute all registered forms in dependency order.

        Returns:
            Dict of form_id -> computed BaseTaxForm instances.
        """
        computed: dict[str, BaseTaxForm] = {}
        order = self._topological_sort()

        for form_id in order:
            form = self.registry[form_id]
            form.calculate(return_data, computed)
            computed[form_id] = form

        return computed

    def _topological_sort(self) -> list[str]:
        """Topologically sort forms by dependency order."""
        visited: set[str] = set()
        order: list[str] = []

        def visit(form_id: str, ancestors: set[str]) -> None:
            if form_id in ancestors:
                raise ValueError(
                    f"Circular dependency detected involving {form_id}"
                )
            if form_id in visited:
                return
            ancestors.add(form_id)
            form = self.registry.get(form_id)
            if form:
                for dep_id in form.dependencies:
                    if dep_id in self.registry:
                        visit(dep_id, ancestors)
            visited.add(form_id)
            ancestors.discard(form_id)
            order.append(form_id)

        for form_id in self.registry:
            visit(form_id, set())

        return order
