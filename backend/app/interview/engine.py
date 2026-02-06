"""
Interview flow engine for the TurboTax-style guided tax prep wizard.

Loads YAML-defined flow definitions, evaluates conditions to determine step
visibility, and manages navigation through the interview. The engine is
stateless -- all state lives in the InterviewProgress database model. Each
call receives the current progress and return data, computes the requested
navigation result, and returns it.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes for interview structure
# ---------------------------------------------------------------------------

FLOWS_DIR = Path(__file__).parent / "flows"


@dataclass
class StepField:
    """A single input field within a form_entry step."""

    name: str
    label: str
    type: str = "text"
    required: bool = False
    max_length: int | None = None
    min_val: float | None = None
    max_val: float | None = None
    pattern: str | None = None
    placeholder: str | None = None
    help_text: str | None = None
    masked: bool = False
    options: list[dict[str, str]] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepField":
        return cls(
            name=data["name"],
            label=data.get("label", data["name"]),
            type=data.get("type", "text"),
            required=data.get("required", False),
            max_length=data.get("max_length"),
            min_val=data.get("min"),
            max_val=data.get("max"),
            pattern=data.get("pattern"),
            placeholder=data.get("placeholder"),
            help_text=data.get("help_text"),
            masked=data.get("masked", False),
            options=data.get("options"),
        )


@dataclass
class StepOption:
    """An option for multi_select or select-type steps."""

    value: str
    label: str
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepOption":
        return cls(
            value=data["value"],
            label=data["label"],
            description=data.get("description"),
        )


@dataclass
class ComputedField:
    """A computed display field with a reference to a computation function."""

    name: str
    label: str
    computation: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComputedField":
        return cls(
            name=data["name"],
            label=data["label"],
            computation=data["computation"],
        )


@dataclass
class InterviewStep:
    """A single step within an interview flow section."""

    id: str
    type: str  # yes_no, form_entry, multi_select, computed_display, info
    title: str
    description: str = ""
    condition: str | None = None
    fields: list[StepField] = field(default_factory=list)
    options: list[StepOption] = field(default_factory=list)
    computed_fields: list[ComputedField] = field(default_factory=list)
    content: str | None = None
    repeating: bool = False
    repeat_prompt: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InterviewStep":
        fields = [StepField.from_dict(f) for f in data.get("fields", [])]
        options = [StepOption.from_dict(o) for o in data.get("options", [])]
        computed_fields = [
            ComputedField.from_dict(c) for c in data.get("computed_fields", [])
        ]

        return cls(
            id=data["id"],
            type=data["type"],
            title=data["title"],
            description=data.get("description", ""),
            condition=data.get("condition"),
            fields=fields,
            options=options,
            computed_fields=computed_fields,
            content=data.get("content"),
            repeating=data.get("repeating", False),
            repeat_prompt=data.get("repeat_prompt"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the step for API responses."""
        result: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
        }
        if self.fields:
            result["fields"] = [
                {
                    "name": f.name,
                    "label": f.label,
                    "type": f.type,
                    "required": f.required,
                    **({"max_length": f.max_length} if f.max_length else {}),
                    **({"min": f.min_val} if f.min_val is not None else {}),
                    **({"max": f.max_val} if f.max_val is not None else {}),
                    **({"pattern": f.pattern} if f.pattern else {}),
                    **({"placeholder": f.placeholder} if f.placeholder else {}),
                    **({"help_text": f.help_text} if f.help_text else {}),
                    **({"masked": f.masked} if f.masked else {}),
                    **({"options": f.options} if f.options else {}),
                }
                for f in self.fields
            ]
        if self.options:
            result["options"] = [
                {
                    "value": o.value,
                    "label": o.label,
                    **({"description": o.description} if o.description else {}),
                }
                for o in self.options
            ]
        if self.computed_fields:
            result["computed_fields"] = [
                {
                    "name": c.name,
                    "label": c.label,
                    "computation": c.computation,
                }
                for c in self.computed_fields
            ]
        if self.content:
            result["content"] = self.content
        if self.repeating:
            result["repeating"] = True
            if self.repeat_prompt:
                result["repeat_prompt"] = self.repeat_prompt
        return result


@dataclass
class InterviewSection:
    """A section of the interview (e.g., Personal Info, Income)."""

    id: str
    title: str
    description: str = ""
    icon: str | None = None
    steps: list[InterviewStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "icon": self.icon,
            "step_count": len(self.steps),
        }


# ---------------------------------------------------------------------------
# Condition evaluator
# ---------------------------------------------------------------------------


class ConditionEvaluator:
    """
    Evaluates condition expressions against return data and interview answers.

    Supported expression formats:
        - ``filing_status == married_filing_jointly``   (equality)
        - ``filing_status != single``                   (inequality)
        - ``has_w2_income``                             (truthy check)
        - ``income_types contains 1099_int``            (list membership)
        - ``wants_itemized == true``                    (boolean equality)
        - ``has_dependents``                            (truthy check from answers)
        - ``has_dependents == true``                    (explicit boolean)
    """

    def __init__(self, return_data: dict[str, Any], answers: dict[str, Any]):
        self._return_data = return_data
        self._answers = answers

    # -- public API --

    def evaluate(self, condition: str | None) -> bool:
        """Return True if the condition is met (or if there is no condition)."""
        if not condition:
            return True

        condition = condition.strip()

        # Handle "contains" operator: ``key contains value``
        if " contains " in condition:
            return self._eval_contains(condition)

        # Handle equality / inequality: ``key == value`` / ``key != value``
        if " == " in condition:
            return self._eval_equality(condition)
        if " != " in condition:
            return self._eval_inequality(condition)

        # Bare identifier -- truthy check
        return self._eval_truthy(condition)

    # -- private helpers --

    def _resolve(self, key: str) -> Any:
        """
        Look up *key* first in answers, then in return_data.

        Special synthetic keys:
        - ``has_w2_income``: True if the return has any W-2 records
        - ``has_dependents``: True if answer says yes or return has dependents
        - ``income_types``: the list selected in the income_type_selection step
        - ``wants_itemized``: True if deduction_method answer is yes/true
        """
        # Check answers first (interview answers take precedence)
        if key in self._answers:
            return self._answers[key]

        # Synthetic keys derived from return data
        if key == "has_w2_income":
            return bool(self._return_data.get("w2_count", 0))
        if key == "has_dependents":
            # Check both the answer and the return data
            ans = self._answers.get("has_dependents")
            if ans is not None:
                return self._to_bool(ans)
            return bool(self._return_data.get("dependent_count", 0))
        if key == "income_types":
            return self._answers.get("income_type_selection", [])
        if key == "wants_itemized":
            val = self._answers.get("deduction_method")
            if val is not None:
                return self._to_bool(val)
            return bool(self._return_data.get("has_itemized_deductions", False))
        if key == "has_education_expenses":
            ans = self._answers.get("has_education_expenses")
            if ans is not None:
                return self._to_bool(ans)
            return bool(self._return_data.get("education_expense_count", 0))
        if key == "has_retirement_contributions":
            ans = self._answers.get("has_retirement_contributions")
            if ans is not None:
                return self._to_bool(ans)
            return bool(self._return_data.get("retirement_contribution_count", 0))

        # Fall back to return data
        return self._return_data.get(key)

    def _eval_contains(self, condition: str) -> bool:
        parts = condition.split(" contains ", 1)
        if len(parts) != 2:
            logger.warning("Malformed contains condition: %s", condition)
            return False
        key = parts[0].strip()
        value = parts[1].strip()
        resolved = self._resolve(key)
        if resolved is None:
            return False
        if isinstance(resolved, (list, tuple, set)):
            return value in resolved
        if isinstance(resolved, str):
            return value in resolved
        return False

    def _eval_equality(self, condition: str) -> bool:
        parts = condition.split(" == ", 1)
        if len(parts) != 2:
            logger.warning("Malformed equality condition: %s", condition)
            return False
        key = parts[0].strip()
        expected = parts[1].strip()
        actual = self._resolve(key)
        return self._compare(actual, expected)

    def _eval_inequality(self, condition: str) -> bool:
        parts = condition.split(" != ", 1)
        if len(parts) != 2:
            logger.warning("Malformed inequality condition: %s", condition)
            return False
        key = parts[0].strip()
        expected = parts[1].strip()
        actual = self._resolve(key)
        return not self._compare(actual, expected)

    def _eval_truthy(self, key: str) -> bool:
        val = self._resolve(key)
        if val is None:
            return False
        return self._to_bool(val)

    @staticmethod
    def _compare(actual: Any, expected: str) -> bool:
        """Compare a resolved value against an expected string value."""
        if actual is None:
            return False

        # Boolean comparison
        if expected.lower() in ("true", "false"):
            return ConditionEvaluator._to_bool(actual) == (
                expected.lower() == "true"
            )

        # Numeric comparison
        try:
            return float(actual) == float(expected)
        except (ValueError, TypeError):
            pass

        # String comparison (case-insensitive)
        return str(actual).lower() == expected.lower()

    @staticmethod
    def _to_bool(value: Any) -> bool:
        """Coerce a value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "y")
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, (list, dict)):
            return bool(value)
        return bool(value)


# ---------------------------------------------------------------------------
# Interview engine
# ---------------------------------------------------------------------------


class InterviewEngine:
    """
    The main interview engine. Loads YAML flows and provides navigation logic.

    Usage::

        engine = InterviewEngine()
        step = engine.get_current_step("personal_info", "filing_status", return_data, answers)
        next_step = engine.get_next_step("personal_info", "filing_status", return_data, answers)
    """

    def __init__(self, flows_dir: str | Path | None = None):
        self._flows_dir = Path(flows_dir) if flows_dir else FLOWS_DIR
        self._sections: list[InterviewSection] = []
        self._section_map: dict[str, InterviewSection] = {}
        self._step_index: dict[str, tuple[str, int]] = {}  # step_id -> (section_id, idx)
        self._loaded = False

    # -- Loading --

    def load(self) -> None:
        """Load all flow YAML files. Idempotent."""
        if self._loaded:
            return
        self._load_main_flow()
        self._loaded = True

    def _load_main_flow(self) -> None:
        main_path = self._flows_dir / "main.yaml"
        if not main_path.exists():
            raise FileNotFoundError(f"Main flow definition not found: {main_path}")

        with open(main_path) as f:
            main_data = yaml.safe_load(f)

        for section_def in main_data.get("sections", []):
            section = self._load_section(section_def)
            self._sections.append(section)
            self._section_map[section.id] = section

            for idx, step in enumerate(section.steps):
                self._step_index[step.id] = (section.id, idx)

    def _load_section(self, section_def: dict[str, Any]) -> InterviewSection:
        flow_file = section_def.get("flow_file")
        section = InterviewSection(
            id=section_def["id"],
            title=section_def["title"],
            description=section_def.get("description", ""),
            icon=section_def.get("icon"),
        )

        if flow_file:
            flow_path = self._flows_dir / flow_file
            if flow_path.exists():
                with open(flow_path) as f:
                    flow_data = yaml.safe_load(f)
                for step_data in flow_data.get("steps", []):
                    section.steps.append(InterviewStep.from_dict(step_data))
            else:
                logger.warning("Flow file not found: %s", flow_path)

        return section

    # -- Helpers --

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def _make_evaluator(
        self, return_data: dict[str, Any], answers: dict[str, Any]
    ) -> ConditionEvaluator:
        return ConditionEvaluator(return_data, answers)

    def _get_visible_steps(
        self, section: InterviewSection, evaluator: ConditionEvaluator
    ) -> list[InterviewStep]:
        """Return only steps whose conditions are met."""
        return [s for s in section.steps if evaluator.evaluate(s.condition)]

    # -- Public API: Section navigation --

    def get_sections(self) -> list[dict[str, Any]]:
        """Return the ordered list of sections (metadata only)."""
        self._ensure_loaded()
        return [s.to_dict() for s in self._sections]

    def get_section_ids(self) -> list[str]:
        """Return ordered list of section IDs."""
        self._ensure_loaded()
        return [s.id for s in self._sections]

    def get_section(self, section_id: str) -> InterviewSection | None:
        """Return a section by ID."""
        self._ensure_loaded()
        return self._section_map.get(section_id)

    def get_next_section_id(self, current_section_id: str) -> str | None:
        """Return the next section ID, or None if at the end."""
        self._ensure_loaded()
        ids = self.get_section_ids()
        try:
            idx = ids.index(current_section_id)
            if idx + 1 < len(ids):
                return ids[idx + 1]
        except ValueError:
            pass
        return None

    def get_prev_section_id(self, current_section_id: str) -> str | None:
        """Return the previous section ID, or None if at the beginning."""
        self._ensure_loaded()
        ids = self.get_section_ids()
        try:
            idx = ids.index(current_section_id)
            if idx > 0:
                return ids[idx - 1]
        except ValueError:
            pass
        return None

    # -- Public API: Step navigation --

    def get_current_step(
        self,
        section_id: str,
        step_id: str,
        return_data: dict[str, Any],
        answers: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Return the current step data, or None if the step is not visible.

        If the requested step's condition is not met, automatically advance to
        the next visible step.
        """
        self._ensure_loaded()
        section = self._section_map.get(section_id)
        if not section:
            return None

        evaluator = self._make_evaluator(return_data, answers)

        # Find the requested step
        step = self._find_step(section, step_id)
        if step and evaluator.evaluate(step.condition):
            return self._build_step_response(section, step, evaluator)

        # Step not visible -- try to find next visible step from that position
        visible = self._get_visible_steps(section, evaluator)
        if not visible:
            return None

        # Find position of requested step (even if not visible) and get next visible
        step_ids = [s.id for s in section.steps]
        try:
            idx = step_ids.index(step_id)
        except ValueError:
            # Unknown step -- return first visible
            return self._build_step_response(section, visible[0], evaluator)

        # Find the first visible step at or after idx
        for s in section.steps[idx:]:
            if evaluator.evaluate(s.condition):
                return self._build_step_response(section, s, evaluator)

        # Nothing after; return last visible
        return self._build_step_response(section, visible[-1], evaluator)

    def get_next_step(
        self,
        section_id: str,
        current_step_id: str,
        return_data: dict[str, Any],
        answers: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Determine the next visible step after *current_step_id*.

        Returns ``None`` if the current step is the last visible step in its
        section.  The caller should then advance to the next section.

        The returned dict includes ``section_id`` and ``step`` keys so the
        caller knows where to navigate.
        """
        self._ensure_loaded()
        section = self._section_map.get(section_id)
        if not section:
            return None

        evaluator = self._make_evaluator(return_data, answers)
        step_ids = [s.id for s in section.steps]

        try:
            idx = step_ids.index(current_step_id)
        except ValueError:
            return None

        # Search forward for the next visible step
        for s in section.steps[idx + 1 :]:
            if evaluator.evaluate(s.condition):
                return self._build_step_response(section, s, evaluator)

        # No more steps in this section -- check next section
        next_section_id = self.get_next_section_id(section_id)
        if next_section_id:
            next_section = self._section_map[next_section_id]
            for s in next_section.steps:
                if evaluator.evaluate(s.condition):
                    return self._build_step_response(next_section, s, evaluator)

        return None

    def get_prev_step(
        self,
        section_id: str,
        current_step_id: str,
        return_data: dict[str, Any],
        answers: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Determine the previous visible step before *current_step_id*.

        Returns ``None`` if at the very first step of the interview.
        """
        self._ensure_loaded()
        section = self._section_map.get(section_id)
        if not section:
            return None

        evaluator = self._make_evaluator(return_data, answers)
        step_ids = [s.id for s in section.steps]

        try:
            idx = step_ids.index(current_step_id)
        except ValueError:
            return None

        # Search backward for the previous visible step
        for s in reversed(section.steps[:idx]):
            if evaluator.evaluate(s.condition):
                return self._build_step_response(section, s, evaluator)

        # No previous step in this section -- check previous section
        prev_section_id = self.get_prev_section_id(section_id)
        if prev_section_id:
            prev_section = self._section_map[prev_section_id]
            for s in reversed(prev_section.steps):
                if evaluator.evaluate(s.condition):
                    return self._build_step_response(prev_section, s, evaluator)

        return None

    def get_first_step_of_section(
        self,
        section_id: str,
        return_data: dict[str, Any],
        answers: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Return the first visible step of a section."""
        self._ensure_loaded()
        section = self._section_map.get(section_id)
        if not section:
            return None

        evaluator = self._make_evaluator(return_data, answers)
        for s in section.steps:
            if evaluator.evaluate(s.condition):
                return self._build_step_response(section, s, evaluator)

        return None

    # -- Public API: Progress calculations --

    def get_section_progress(
        self,
        section_id: str,
        return_data: dict[str, Any],
        answers: dict[str, Any],
        completed_steps: list[str],
    ) -> dict[str, Any]:
        """Return progress information for a section."""
        self._ensure_loaded()
        section = self._section_map.get(section_id)
        if not section:
            return {"section_id": section_id, "total": 0, "completed": 0, "percentage": 0}

        evaluator = self._make_evaluator(return_data, answers)
        visible = self._get_visible_steps(section, evaluator)
        total = len(visible)
        completed = sum(1 for s in visible if s.id in completed_steps)

        return {
            "section_id": section_id,
            "total": total,
            "completed": completed,
            "percentage": round((completed / total) * 100) if total > 0 else 0,
        }

    def get_overall_progress(
        self,
        return_data: dict[str, Any],
        answers: dict[str, Any],
        completed_steps: list[str],
    ) -> dict[str, Any]:
        """Return overall interview progress across all sections."""
        self._ensure_loaded()
        evaluator = self._make_evaluator(return_data, answers)
        total = 0
        completed = 0
        section_progress = []

        for section in self._sections:
            visible = self._get_visible_steps(section, evaluator)
            section_total = len(visible)
            section_completed = sum(1 for s in visible if s.id in completed_steps)
            total += section_total
            completed += section_completed
            section_progress.append({
                "section_id": section.id,
                "section_title": section.title,
                "total": section_total,
                "completed": section_completed,
                "percentage": (
                    round((section_completed / section_total) * 100)
                    if section_total > 0
                    else 0
                ),
            })

        return {
            "total_steps": total,
            "completed_steps": completed,
            "overall_percentage": round((completed / total) * 100) if total > 0 else 0,
            "sections": section_progress,
        }

    # -- Internal helpers --

    @staticmethod
    def _find_step(
        section: InterviewSection, step_id: str
    ) -> InterviewStep | None:
        for step in section.steps:
            if step.id == step_id:
                return step
        return None

    def _build_step_response(
        self,
        section: InterviewSection,
        step: InterviewStep,
        evaluator: ConditionEvaluator,
    ) -> dict[str, Any]:
        """Build the full response dict for a step."""
        visible_steps = self._get_visible_steps(section, evaluator)
        visible_ids = [s.id for s in visible_steps]

        try:
            position = visible_ids.index(step.id)
        except ValueError:
            position = 0

        return {
            "section_id": section.id,
            "section_title": section.title,
            "step": step.to_dict(),
            "position": position + 1,
            "total_in_section": len(visible_ids),
            "is_first_in_section": position == 0,
            "is_last_in_section": position == len(visible_ids) - 1,
            "is_first_overall": (
                section.id == self._sections[0].id and position == 0
            ),
            "is_last_overall": (
                section.id == self._sections[-1].id
                and position == len(visible_ids) - 1
            ),
        }


# ---------------------------------------------------------------------------
# Module-level singleton for convenience
# ---------------------------------------------------------------------------

_engine: InterviewEngine | None = None


def get_interview_engine() -> InterviewEngine:
    """Return a lazily-initialized singleton InterviewEngine."""
    global _engine
    if _engine is None:
        _engine = InterviewEngine()
        _engine.load()
    return _engine
