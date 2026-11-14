from __future__ import annotations

import re
from typing import Any, Optional

from api.models import (
    ConditionEvaluation,
    ConditionStatus,
    EligibilityCondition,
    EligibilityResult,
    OverallEligibility,
    StudentProfile,
)
from api.taxonomy import (
    normalize_degree,
    normalize_discipline,
)


def _to_float(value: Any) -> Optional[float]:
    """Best-effort numeric coercion that never raises."""
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> Optional[int]:
    """Best-effort integer coercion that never raises."""
    number = _to_float(value)
    if number is None:
        return None
    try:
        return int(number)
    except (OverflowError, ValueError):
        return None


def evaluate_single_condition(
    condition: EligibilityCondition, profile: StudentProfile
) -> ConditionEvaluation:
    c_type = condition.condition_type.casefold()
    op = condition.operator
    expected = condition.value

    edu = profile.education[0] if profile.education else None

    if c_type == "degree":
        if not edu or not edu.degree:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.UNKNOWN,
                original_text=condition.original_text,
                expected=expected,
                actual=None,
                reason="Candidate degree is not specified in profile.",
                logic_group=condition.logic_group,
            )

        student_deg = normalize_degree(edu.degree)
        if op == "==":
            target_deg = normalize_degree(str(expected))
            if student_deg == target_deg:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.PASS,
                    original_text=condition.original_text,
                    expected=target_deg,
                    actual=student_deg,
                    reason=f"Candidate's degree '{edu.degree}' satisfies required degree '{expected}'.",
                    logic_group=condition.logic_group,
                )
            else:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.FAIL,
                    original_text=condition.original_text,
                    expected=target_deg,
                    actual=student_deg,
                    reason=f"Candidate's degree '{edu.degree}' does not match required degree '{expected}'.",
                    logic_group=condition.logic_group,
                )
        elif op == "in":
            allowed = (
                [normalize_degree(d) for d in expected]
                if isinstance(expected, list)
                else [normalize_degree(str(expected))]
            )
            if student_deg in allowed:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.PASS,
                    original_text=condition.original_text,
                    expected=allowed,
                    actual=student_deg,
                    reason=f"Candidate's degree '{edu.degree}' is accepted among alternative degrees ({', '.join(allowed)}).",
                    logic_group=condition.logic_group,
                )
            else:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.FAIL,
                    original_text=condition.original_text,
                    expected=allowed,
                    actual=student_deg,
                    reason=f"Candidate's degree '{edu.degree}' is not in accepted degrees ({', '.join(allowed)}).",
                    logic_group=condition.logic_group,
                )

    elif c_type == "level":
        if not edu or not edu.level:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.UNKNOWN,
                original_text=condition.original_text,
                expected=expected,
                actual=None,
                reason="Candidate academic level is not stated in profile.",
                logic_group=condition.logic_group,
            )
        candidate_level = edu.level.casefold()
        target_level = str(expected).casefold()
        if candidate_level == target_level:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.PASS,
                original_text=condition.original_text,
                expected=target_level,
                actual=candidate_level,
                reason=f"Academic level '{candidate_level}' meets required '{target_level}'.",
                logic_group=condition.logic_group,
            )
        else:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.FAIL,
                original_text=condition.original_text,
                expected=target_level,
                actual=candidate_level,
                reason=f"Academic level '{candidate_level}' does not match required '{target_level}'.",
                logic_group=condition.logic_group,
            )

    elif c_type == "discipline":
        if not edu or not edu.discipline:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.UNKNOWN,
                original_text=condition.original_text,
                expected=expected,
                actual=None,
                reason="Candidate discipline/branch is not specified in profile.",
                logic_group=condition.logic_group,
            )

        student_disc = normalize_discipline(edu.discipline)
        if op == "in" and isinstance(expected, list):
            allowed = [normalize_discipline(d) for d in expected]
            if student_disc in allowed:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.PASS,
                    original_text=condition.original_text,
                    expected=allowed,
                    actual=student_disc,
                    reason=f"Candidate discipline '{edu.discipline}' matches accepted disciplines.",
                    logic_group=condition.logic_group,
                )
            else:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.FAIL,
                    original_text=condition.original_text,
                    expected=allowed,
                    actual=student_disc,
                    reason=f"Candidate discipline '{edu.discipline}' is not among accepted disciplines.",
                    logic_group=condition.logic_group,
                )
        else:
            target_disc = normalize_discipline(str(expected))
            if student_disc == target_disc or target_disc in student_disc:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.PASS,
                    original_text=condition.original_text,
                    expected=target_disc,
                    actual=student_disc,
                    reason=f"Candidate discipline '{edu.discipline}' matches required discipline '{expected}'.",
                    logic_group=condition.logic_group,
                )
            else:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.FAIL,
                    original_text=condition.original_text,
                    expected=target_disc,
                    actual=student_disc,
                    reason=f"Candidate discipline '{edu.discipline}' does not match required discipline '{expected}'.",
                    logic_group=condition.logic_group,
                )

    elif c_type == "enrolment":
        if not edu or not edu.enrolment_status:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.UNKNOWN,
                original_text=condition.original_text,
                expected=expected,
                actual=None,
                reason="Current enrolment status is unknown in profile.",
                logic_group=condition.logic_group,
            )
        c_status = edu.enrolment_status.casefold()
        t_status = str(expected).casefold()
        if c_status == t_status:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.PASS,
                original_text=condition.original_text,
                expected=t_status,
                actual=c_status,
                reason=f"Enrolment status '{c_status}' satisfies requirement.",
                logic_group=condition.logic_group,
            )
        else:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.FAIL,
                original_text=condition.original_text,
                expected=t_status,
                actual=c_status,
                reason=f"Candidate enrolment status is '{c_status}', but '{t_status}' is required.",
                logic_group=condition.logic_group,
            )

    elif c_type == "marks":
        if not edu or edu.cgpa is None:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.UNKNOWN,
                original_text=condition.original_text,
                expected=expected,
                actual=None,
                reason="Minimum marks/CGPA required, but candidate profile does not report GPA or percentage.",
                logic_group=condition.logic_group,
            )

        c_scale = edu.cgpa_scale
        if not c_scale or c_scale <= 0 or edu.cgpa > c_scale:
            c_scale = 4.0 if edu.cgpa <= 4.0 else (10.0 if edu.cgpa <= 10.0 else 100.0)
        c_pct = (edu.cgpa / c_scale) * 100.0

        if isinstance(expected, dict):
            req_min = _to_float(expected.get("min_value"))
            req_scale = _to_float(expected.get("scale"))
            if req_scale is None and req_min is not None:
                req_scale = (
                    4.0 if req_min <= 4.0 else (10.0 if req_min <= 10.0 else 100.0)
                )
            if req_scale is None:
                req_scale = 4.0
        else:
            req_min = _to_float(expected)
            if req_min is None:
                req_scale = None
            else:
                req_scale = (
                    4.0 if req_min <= 4.0 else (10.0 if req_min <= 10.0 else 100.0)
                )

        if req_min is None or req_scale is None or req_scale <= 0:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.UNKNOWN,
                original_text=condition.original_text,
                expected=expected,
                actual=None,
                reason="Marks requirement could not be interpreted reliably; manual confirmation needed.",
                logic_group=condition.logic_group,
            )

        req_pct = (req_min / req_scale) * 100.0

        if c_pct >= (req_pct - 0.01):
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.PASS,
                original_text=condition.original_text,
                expected=f"{req_min}/{req_scale}",
                actual=f"{edu.cgpa}/{c_scale}",
                reason=f"Candidate marks ({edu.cgpa}/{c_scale}) meet the required threshold ({req_min}/{req_scale}).",
                logic_group=condition.logic_group,
            )
        else:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.FAIL,
                original_text=condition.original_text,
                expected=f"{req_min}/{req_scale}",
                actual=f"{edu.cgpa}/{c_scale}",
                reason=f"Candidate marks ({edu.cgpa}/{c_scale}) are below the required threshold ({req_min}/{req_scale}).",
                logic_group=condition.logic_group,
            )

    elif c_type == "graduation_date":
        if not edu or not edu.graduation_date:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.UNKNOWN,
                original_text=condition.original_text,
                expected=expected,
                actual=None,
                reason="Candidate graduation year is not stated in profile.",
                logic_group=condition.logic_group,
            )

        year_match = re.search(r"(?:19|20)\d{2}", str(edu.graduation_date))
        if year_match is None:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.UNKNOWN,
                original_text=condition.original_text,
                expected=expected,
                actual=edu.graduation_date,
                reason=f"Could not parse candidate graduation year '{edu.graduation_date}'.",
                logic_group=condition.logic_group,
            )

        cand_yr = int(year_match.group(0))

        if (
            op == "between"
            and isinstance(expected, (list, tuple))
            and len(expected) == 2
        ):
            start_yr, end_yr = _to_int(expected[0]), _to_int(expected[1])
            if start_yr is None or end_yr is None:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.UNKNOWN,
                    original_text=condition.original_text,
                    expected=expected,
                    actual=cand_yr,
                    reason="Graduation window could not be interpreted; manual confirmation needed.",
                    logic_group=condition.logic_group,
                )
            if start_yr <= cand_yr <= end_yr:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.PASS,
                    original_text=condition.original_text,
                    expected=f"{start_yr}-{end_yr}",
                    actual=cand_yr,
                    reason=f"Candidate graduation year ({cand_yr}) falls within the required window ({start_yr} - {end_yr}).",
                    logic_group=condition.logic_group,
                )
            else:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.FAIL,
                    original_text=condition.original_text,
                    expected=f"{start_yr}-{end_yr}",
                    actual=cand_yr,
                    reason=f"Candidate graduation year ({cand_yr}) is outside required window ({start_yr} - {end_yr}).",
                    logic_group=condition.logic_group,
                )
        elif op == "==":
            target_yr = _to_int(expected)
            if target_yr is None:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.UNKNOWN,
                    original_text=condition.original_text,
                    expected=expected,
                    actual=cand_yr,
                    reason="Required graduation year could not be interpreted; manual confirmation needed.",
                    logic_group=condition.logic_group,
                )
            if cand_yr == target_yr:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.PASS,
                    original_text=condition.original_text,
                    expected=target_yr,
                    actual=cand_yr,
                    reason=f"Candidate graduation year ({cand_yr}) matches required {target_yr}.",
                    logic_group=condition.logic_group,
                )
            else:
                return ConditionEvaluation(
                    condition_id=condition.condition_id,
                    condition_type=c_type,
                    is_mandatory=condition.is_mandatory,
                    status=ConditionStatus.FAIL,
                    original_text=condition.original_text,
                    expected=target_yr,
                    actual=cand_yr,
                    reason=f"Candidate graduation year ({cand_yr}) does not match required {target_yr}.",
                    logic_group=condition.logic_group,
                )

    elif c_type in ("year", "semester"):
        actual_val = (
            edu.current_semester
            if (edu and c_type == "semester")
            else (edu.current_year if edu else None)
        )
        if actual_val is None:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.UNKNOWN,
                original_text=condition.original_text,
                expected=expected,
                actual=None,
                reason=f"Candidate {c_type} is not specified in profile.",
                logic_group=condition.logic_group,
            )
        req_val = _to_int(expected)
        if req_val is None:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.UNKNOWN,
                original_text=condition.original_text,
                expected=expected,
                actual=actual_val,
                reason=f"Required {c_type} could not be interpreted; manual confirmation needed.",
                logic_group=condition.logic_group,
            )
        if actual_val >= req_val:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.PASS,
                original_text=condition.original_text,
                expected=req_val,
                actual=actual_val,
                reason=f"Candidate current {c_type} ({actual_val}) meets required minimum ({req_val}).",
                logic_group=condition.logic_group,
            )
        else:
            return ConditionEvaluation(
                condition_id=condition.condition_id,
                condition_type=c_type,
                is_mandatory=condition.is_mandatory,
                status=ConditionStatus.FAIL,
                original_text=condition.original_text,
                expected=req_val,
                actual=actual_val,
                reason=f"Candidate current {c_type} ({actual_val}) is below required minimum ({req_val}).",
                logic_group=condition.logic_group,
            )

    return ConditionEvaluation(
        condition_id=condition.condition_id,
        condition_type=c_type,
        is_mandatory=condition.is_mandatory,
        status=ConditionStatus.UNKNOWN,
        original_text=condition.original_text,
        expected=expected,
        actual=None,
        reason="Criterion requires manual confirmation.",
        logic_group=condition.logic_group,
    )


def evaluate_eligibility(
    conditions: list[EligibilityCondition],
    profile: StudentProfile,
    has_posting_contradictions: bool = False,
    contradiction_reasons: list[str] | None = None,
) -> EligibilityResult:
    evaluations: list[ConditionEvaluation] = []

    if has_posting_contradictions and contradiction_reasons:
        for reason in contradiction_reasons:
            evaluations.append(
                ConditionEvaluation(
                    condition_id="conflict",
                    condition_type="conflict",
                    is_mandatory=True,
                    status=ConditionStatus.CONFLICT,
                    original_text=reason,
                    expected=None,
                    actual=None,
                    reason=f"Posting contradiction: {reason}",
                    logic_group="contradictions",
                )
            )

    if not conditions and not evaluations:
        return EligibilityResult(
            status=OverallEligibility.NO_FORMAL_CRITERIA,
            summary="No explicit formal eligibility criteria found in listing.",
            unresolved_mandatory_count=0,
            conditions=[],
        )

    for condition in conditions:
        evaluations.append(evaluate_single_condition(condition, profile))

    groups: dict[str, list[ConditionEvaluation]] = {}
    for ev in evaluations:
        if not ev.is_mandatory:
            continue
        groups.setdefault(ev.logic_group, []).append(ev)

    group_statuses: dict[str, ConditionStatus] = {}
    for g_name, g_evals in groups.items():
        if any(e.status == ConditionStatus.CONFLICT for e in g_evals):
            group_statuses[g_name] = ConditionStatus.CONFLICT
        elif any(e.status == ConditionStatus.PASS for e in g_evals):
            group_statuses[g_name] = ConditionStatus.PASS
        elif all(e.status == ConditionStatus.FAIL for e in g_evals):
            group_statuses[g_name] = ConditionStatus.FAIL
        else:
            group_statuses[g_name] = ConditionStatus.UNKNOWN

    unresolved_count = sum(
        1
        for s in group_statuses.values()
        if s in (ConditionStatus.UNKNOWN, ConditionStatus.CONFLICT)
    )

    if any(s == ConditionStatus.FAIL for s in group_statuses.values()):
        failed_reasons = [
            e.reason
            for e in evaluations
            if e.status == ConditionStatus.FAIL and e.is_mandatory
        ]
        summary = "Conclusively ineligible: " + "; ".join(failed_reasons)
        overall = OverallEligibility.NOT_ELIGIBLE
    elif unresolved_count > 0:
        unknown_reasons = [
            e.reason
            for e in evaluations
            if e.status in (ConditionStatus.UNKNOWN, ConditionStatus.CONFLICT)
            and e.is_mandatory
        ]
        summary = (
            f"Eligibility needs confirmation: {unresolved_count} mandatory condition(s) unresolved. "
            + "; ".join(unknown_reasons[:2])
        )
        overall = OverallEligibility.NEEDS_CONFIRMATION
    else:
        summary = "All explicit mandatory eligibility conditions satisfied."
        overall = OverallEligibility.ELIGIBLE

    return EligibilityResult(
        status=overall,
        summary=summary,
        unresolved_mandatory_count=unresolved_count,
        conditions=evaluations,
    )
