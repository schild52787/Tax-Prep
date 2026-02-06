"""
Interview flow API endpoints.

Provides a guided, TurboTax-style wizard experience. The frontend calls these
endpoints to walk through the interview one step at a time. All state is
persisted in the ``InterviewProgress`` model.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.interview.engine import get_interview_engine
from app.models.tax_return import InterviewProgress, TaxReturn

router = APIRouter(
    prefix="/returns/{return_id}/interview",
    tags=["Interview"],
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class AnswerSubmission(BaseModel):
    """Payload for submitting an answer to the current step."""

    step_id: str = Field(..., description="The ID of the step being answered")
    answer: Any = Field(
        ...,
        description=(
            "The answer value. Shape depends on step type: "
            "bool for yes_no, dict for form_entry, list[str] for multi_select, "
            "None for info/computed_display."
        ),
    )


class JumpRequest(BaseModel):
    """Payload for jumping to a specific section."""

    section_id: str = Field(..., description="The section to jump to")
    step_id: str | None = Field(
        None, description="Optional step within the section (defaults to first visible)"
    )


class StepResponse(BaseModel):
    """Response containing the current interview step and navigation metadata."""

    section_id: str
    section_title: str
    step: dict[str, Any]
    position: int
    total_in_section: int
    is_first_in_section: bool
    is_last_in_section: bool
    is_first_overall: bool
    is_last_overall: bool
    progress: dict[str, Any]
    answers: dict[str, Any] = Field(
        default_factory=dict,
        description="Previously recorded answers for this step (if any)",
    )

    model_config = {"from_attributes": True}


class InterviewProgressResponse(BaseModel):
    """Top-level progress overview."""

    current_section: str
    current_step_id: str
    sections: list[dict[str, Any]]
    overall_progress: dict[str, Any]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_return_with_relations(
    return_id: str, db: AsyncSession
) -> TaxReturn:
    """Load a TaxReturn with eagerly-loaded relationships needed by the engine."""
    result = await db.execute(
        select(TaxReturn)
        .where(TaxReturn.id == return_id)
        .options(
            selectinload(TaxReturn.interview_progress),
            selectinload(TaxReturn.taxpayers),
            selectinload(TaxReturn.dependents),
            selectinload(TaxReturn.w2_incomes),
            selectinload(TaxReturn.interest_1099s),
            selectinload(TaxReturn.dividend_1099s),
            selectinload(TaxReturn.retirement_1099rs),
            selectinload(TaxReturn.government_1099gs),
            selectinload(TaxReturn.ssa_1099s),
            selectinload(TaxReturn.capital_asset_sales),
            selectinload(TaxReturn.itemized_deduction),
            selectinload(TaxReturn.education_expenses),
            selectinload(TaxReturn.retirement_contributions),
        )
    )
    tax_return = result.scalar_one_or_none()
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
    return tax_return


def _build_return_data(tax_return: TaxReturn) -> dict[str, Any]:
    """
    Build the return_data dict that the ConditionEvaluator uses to check
    conditions against the actual database state.
    """
    return {
        "filing_status": tax_return.filing_status.value if tax_return.filing_status else None,
        "w2_count": len(tax_return.w2_incomes) if tax_return.w2_incomes else 0,
        "has_w2_income": bool(tax_return.w2_incomes),
        "interest_1099_count": len(tax_return.interest_1099s) if tax_return.interest_1099s else 0,
        "dividend_1099_count": len(tax_return.dividend_1099s) if tax_return.dividend_1099s else 0,
        "capital_sale_count": (
            len(tax_return.capital_asset_sales) if tax_return.capital_asset_sales else 0
        ),
        "retirement_1099r_count": (
            len(tax_return.retirement_1099rs) if tax_return.retirement_1099rs else 0
        ),
        "government_1099g_count": (
            len(tax_return.government_1099gs) if tax_return.government_1099gs else 0
        ),
        "ssa_1099_count": len(tax_return.ssa_1099s) if tax_return.ssa_1099s else 0,
        "dependent_count": len(tax_return.dependents) if tax_return.dependents else 0,
        "taxpayer_count": len(tax_return.taxpayers) if tax_return.taxpayers else 0,
        "has_itemized_deductions": tax_return.itemized_deduction is not None,
        "education_expense_count": (
            len(tax_return.education_expenses) if tax_return.education_expenses else 0
        ),
        "retirement_contribution_count": (
            len(tax_return.retirement_contributions)
            if tax_return.retirement_contributions
            else 0
        ),
    }


def _get_or_create_progress(tax_return: TaxReturn) -> InterviewProgress:
    """Return the existing InterviewProgress or raise if missing."""
    if tax_return.interview_progress is None:
        raise HTTPException(
            status_code=404,
            detail="Interview progress not initialized. Create the return first.",
        )
    return tax_return.interview_progress


def _build_step_response(
    step_data: dict[str, Any],
    progress: InterviewProgress,
    return_data: dict[str, Any],
) -> StepResponse:
    """Wrap engine step_data into a full StepResponse with progress info."""
    engine = get_interview_engine()
    answers = progress.answers or {}
    completed = progress.completed_steps or []

    overall = engine.get_overall_progress(return_data, answers, completed)

    # Extract any previously stored answers for this specific step
    step_id = step_data["step"]["id"]
    step_answers = answers.get(step_id, {})

    return StepResponse(
        section_id=step_data["section_id"],
        section_title=step_data["section_title"],
        step=step_data["step"],
        position=step_data["position"],
        total_in_section=step_data["total_in_section"],
        is_first_in_section=step_data["is_first_in_section"],
        is_last_in_section=step_data["is_last_in_section"],
        is_first_overall=step_data["is_first_overall"],
        is_last_overall=step_data["is_last_overall"],
        progress=overall,
        answers=step_answers if isinstance(step_answers, dict) else {"value": step_answers},
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/current", response_model=StepResponse)
async def get_current_step(return_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the current interview step for a tax return.

    Returns the step definition, position information, and any previously
    recorded answers for the step.
    """
    tax_return = await _get_return_with_relations(return_id, db)
    progress = _get_or_create_progress(tax_return)
    return_data = _build_return_data(tax_return)
    answers = progress.answers or {}
    engine = get_interview_engine()

    step_data = engine.get_current_step(
        progress.current_section,
        progress.current_step_id,
        return_data,
        answers,
    )

    if not step_data:
        raise HTTPException(
            status_code=404,
            detail="No visible step found at the current position.",
        )

    # If the engine resolved to a different step (skipped invisible ones),
    # update progress to match.
    resolved_section = step_data["section_id"]
    resolved_step = step_data["step"]["id"]
    if (
        resolved_section != progress.current_section
        or resolved_step != progress.current_step_id
    ):
        progress.current_section = resolved_section
        progress.current_step_id = resolved_step
        await db.flush()

    return _build_step_response(step_data, progress, return_data)


@router.post("/answer", response_model=StepResponse)
async def submit_answer(
    return_id: str,
    body: AnswerSubmission,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an answer for the current step and advance to the next step.

    The answer is stored in ``InterviewProgress.answers`` keyed by step_id.
    The step is marked as completed, and the engine determines the next
    visible step.
    """
    tax_return = await _get_return_with_relations(return_id, db)
    progress = _get_or_create_progress(tax_return)
    return_data = _build_return_data(tax_return)
    engine = get_interview_engine()

    # Validate that the submitted step_id matches the current position
    if body.step_id != progress.current_step_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Step mismatch: expected '{progress.current_step_id}' "
                f"but received '{body.step_id}'. "
                "Use the /current endpoint to sync state."
            ),
        )

    # Store the answer
    answers = dict(progress.answers or {})
    answers[body.step_id] = body.answer
    progress.answers = answers

    # Mark the step as completed
    completed = list(progress.completed_steps or [])
    if body.step_id not in completed:
        completed.append(body.step_id)
    progress.completed_steps = completed

    # Push the current position onto the navigation stack for back-navigation
    nav_stack = list(progress.navigation_stack or [])
    nav_stack.append({
        "section_id": progress.current_section,
        "step_id": progress.current_step_id,
    })
    progress.navigation_stack = nav_stack

    # Determine next step (using updated answers so conditions re-evaluate)
    next_step_data = engine.get_next_step(
        progress.current_section,
        progress.current_step_id,
        return_data,
        answers,
    )

    if next_step_data:
        progress.current_section = next_step_data["section_id"]
        progress.current_step_id = next_step_data["step"]["id"]
        await db.flush()
        return _build_step_response(next_step_data, progress, return_data)

    # If no next step exists, we're at the end of the interview. Return the
    # current (last) step with an indication that the interview is complete.
    current_data = engine.get_current_step(
        progress.current_section,
        progress.current_step_id,
        return_data,
        answers,
    )
    if current_data:
        await db.flush()
        return _build_step_response(current_data, progress, return_data)

    raise HTTPException(status_code=404, detail="Unable to determine next step.")


@router.post("/back", response_model=StepResponse)
async def go_back(return_id: str, db: AsyncSession = Depends(get_db)):
    """
    Navigate back to the previous step.

    Uses the navigation stack for exact back-tracking. Falls back to
    engine-computed previous step if the stack is empty.
    """
    tax_return = await _get_return_with_relations(return_id, db)
    progress = _get_or_create_progress(tax_return)
    return_data = _build_return_data(tax_return)
    answers = progress.answers or {}
    engine = get_interview_engine()

    # Try the navigation stack first (most accurate)
    nav_stack = list(progress.navigation_stack or [])
    if nav_stack:
        prev_entry = nav_stack.pop()
        progress.navigation_stack = nav_stack
        prev_section = prev_entry["section_id"]
        prev_step_id = prev_entry["step_id"]

        step_data = engine.get_current_step(
            prev_section, prev_step_id, return_data, answers
        )
        if step_data:
            progress.current_section = step_data["section_id"]
            progress.current_step_id = step_data["step"]["id"]
            await db.flush()
            return _build_step_response(step_data, progress, return_data)

    # Fall back to engine-computed previous step
    step_data = engine.get_prev_step(
        progress.current_section,
        progress.current_step_id,
        return_data,
        answers,
    )

    if step_data:
        progress.current_section = step_data["section_id"]
        progress.current_step_id = step_data["step"]["id"]
        await db.flush()
        return _build_step_response(step_data, progress, return_data)

    raise HTTPException(
        status_code=400,
        detail="Already at the first step. Cannot go back further.",
    )


@router.post("/jump", response_model=StepResponse)
async def jump_to_section(
    return_id: str,
    body: JumpRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Jump to the first visible step of a specific section (or a specific step
    within that section).

    The navigation stack is updated so that the user can return to their
    previous position using the back endpoint.
    """
    tax_return = await _get_return_with_relations(return_id, db)
    progress = _get_or_create_progress(tax_return)
    return_data = _build_return_data(tax_return)
    answers = progress.answers or {}
    engine = get_interview_engine()

    # Validate the requested section exists
    section = engine.get_section(body.section_id)
    if not section:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown section: '{body.section_id}'",
        )

    # Push current position onto the nav stack
    nav_stack = list(progress.navigation_stack or [])
    nav_stack.append({
        "section_id": progress.current_section,
        "step_id": progress.current_step_id,
    })
    progress.navigation_stack = nav_stack

    # Jump to the requested step or the first visible step of the section
    if body.step_id:
        step_data = engine.get_current_step(
            body.section_id, body.step_id, return_data, answers
        )
    else:
        step_data = engine.get_first_step_of_section(
            body.section_id, return_data, answers
        )

    if not step_data:
        raise HTTPException(
            status_code=404,
            detail=f"No visible steps found in section '{body.section_id}'.",
        )

    progress.current_section = step_data["section_id"]
    progress.current_step_id = step_data["step"]["id"]
    await db.flush()

    return _build_step_response(step_data, progress, return_data)


@router.get("/progress", response_model=InterviewProgressResponse)
async def get_progress(return_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get overall interview progress for a tax return.

    Returns the current position, section list with per-section progress,
    and overall completion percentage.
    """
    tax_return = await _get_return_with_relations(return_id, db)
    progress = _get_or_create_progress(tax_return)
    return_data = _build_return_data(tax_return)
    answers = progress.answers or {}
    completed = progress.completed_steps or []
    engine = get_interview_engine()

    sections = engine.get_sections()
    overall = engine.get_overall_progress(return_data, answers, completed)

    return InterviewProgressResponse(
        current_section=progress.current_section,
        current_step_id=progress.current_step_id,
        sections=sections,
        overall_progress=overall,
    )


@router.get("/sections", response_model=list[dict[str, Any]])
async def list_sections(return_id: str, db: AsyncSession = Depends(get_db)):
    """
    List all interview sections with metadata.

    This is useful for rendering a sidebar navigation. Each section includes
    its ID, title, description, icon, and step count.
    """
    # Validate the return exists
    tax_return = await db.get(TaxReturn, return_id)
    if not tax_return:
        raise HTTPException(status_code=404, detail="Tax return not found")

    engine = get_interview_engine()
    return engine.get_sections()
