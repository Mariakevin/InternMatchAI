from __future__ import annotations

from typing import Optional

from api.models import (
    FitScore,
    OverallEligibility,
    PracticalFitComparison,
    ScoreBreakdown,
    SkillEvidenceState,
    SkillMatchItem,
    StudentProfile,
    WorkMode,
)
from api.taxonomy import normalize_currency, normalize_discipline

DEFAULT_WEIGHTS = {
    "required_skills": 0.30,
    "preferred_skills": 0.15,
    "project_experience": 0.25,
    "education_relevance": 0.15,
    "practical_preferences": 0.15,
}

HOURS_PER_MONTH = 160
WEEKS_PER_MONTH = 4
RELEVANT_DISCIPLINES = {
    "computer science",
    "information technology",
    "data science",
    "artificial intelligence",
}


def _to_monthly(
    amount: float, period: str, duration_months: Optional[int]
) -> Optional[float]:
    """Normalize a stipend to a monthly amount, or None when not convertible."""
    normalized = (period or "monthly").casefold()
    if normalized == "monthly":
        return amount
    if normalized == "hourly":
        return amount * HOURS_PER_MONTH
    if normalized == "weekly":
        return amount * WEEKS_PER_MONTH
    if normalized == "yearly":
        return amount / 12.0
    if normalized == "total":
        if duration_months and duration_months > 0:
            return amount / duration_months
        return None
    return None


def calculate_practical_fit(
    profile: StudentProfile,
    internship_mode: WorkMode,
    internship_location: str,
    internship_duration: Optional[int] = None,
    internship_hours: Optional[int] = None,
    stipend_amount: Optional[float] = None,
    is_unpaid: bool = False,
    stipend_currency: str = "USD",
    stipend_period: str = "monthly",
) -> tuple[PracticalFitComparison, Optional[float]]:
    prefs = profile.preferences
    details: list[str] = []
    comparisons: list[float] = []

    # 1. Work mode
    mode_match: Optional[bool] = None
    if internship_mode != WorkMode.ANY and prefs.preferred_work_modes:
        if internship_mode in prefs.preferred_work_modes:
            mode_match = True
            comparisons.append(1.0)
            details.append(f"Work mode matches ({internship_mode.value}).")
        else:
            mode_match = False
            comparisons.append(0.0)
            details.append(
                f"Work mode mismatch: Role is {internship_mode.value}, but you prefer {', '.join(m.value for m in prefs.preferred_work_modes)}."
            )

    # 2. Location
    loc_match: Optional[bool] = None
    if (
        internship_location
        and prefs.preferred_locations
        and internship_mode != WorkMode.REMOTE
    ):
        norm_cand_locs = [l.casefold() for l in prefs.preferred_locations]
        if (
            any(l in internship_location.casefold() for l in norm_cand_locs)
            or prefs.willing_to_relocate
        ):
            loc_match = True
            comparisons.append(1.0)
            details.append(f"Location ({internship_location}) is acceptable.")
        else:
            loc_match = False
            comparisons.append(0.0)
            details.append(
                f"Location preference mismatch: Role is in {internship_location}, and relocation is marked as false."
            )

    # 3. Duration
    dur_match: Optional[bool] = None
    if internship_duration and prefs.preferred_duration_months:
        if abs(internship_duration - prefs.preferred_duration_months) <= 1:
            dur_match = True
            comparisons.append(1.0)
            details.append(f"Duration matches ({internship_duration} months).")
        else:
            dur_match = False
            comparisons.append(0.5)
            details.append(
                f"Duration difference: Role is {internship_duration} months; your preferred duration is {prefs.preferred_duration_months} months."
            )

    # 4. Weekly hours
    hours_match: Optional[bool] = None
    if internship_hours and prefs.available_hours_per_week:
        if prefs.available_hours_per_week >= internship_hours:
            hours_match = True
            comparisons.append(1.0)
            details.append(
                f"Available weekly hours ({prefs.available_hours_per_week}h) cover required ({internship_hours}h)."
            )
        else:
            hours_match = False
            comparisons.append(0.3)
            details.append(
                f"Weekly hours tight: Role requires {internship_hours}h/wk; you indicated {prefs.available_hours_per_week}h/wk available."
            )

    # 5. Stipend
    stipend_match: Optional[bool] = None
    if is_unpaid:
        if prefs.unpaid_acceptable:
            stipend_match = True
            comparisons.append(0.8)
            details.append("Role is unpaid; your preference allows unpaid internships.")
        else:
            stipend_match = False
            comparisons.append(0.0)
            details.append(
                "Role is unpaid, but your preferences require a paid stipend."
            )
    elif stipend_amount is not None and prefs.minimum_stipend is not None:
        offered_currency = normalize_currency(stipend_currency or "USD")
        minimum_currency = normalize_currency(prefs.stipend_currency or "USD")
        if offered_currency != minimum_currency:
            stipend_match = None
            details.append(
                f"Stipend currency is {offered_currency} but your minimum is in {minimum_currency}; direct comparison not possible."
            )
        else:
            offered_monthly = _to_monthly(
                stipend_amount, stipend_period, internship_duration
            )
            minimum_monthly = _to_monthly(
                prefs.minimum_stipend, prefs.stipend_period, internship_duration
            )
            if offered_monthly is None or minimum_monthly is None:
                stipend_match = None
                details.append(
                    "Stipend period could not be normalized to a monthly basis; direct comparison not possible."
                )
            elif offered_monthly >= minimum_monthly:
                stipend_match = True
                comparisons.append(1.0)
                details.append(
                    f"Offered stipend ({stipend_amount}) meets your minimum ({prefs.minimum_stipend})."
                )
            else:
                stipend_match = False
                comparisons.append(0.4)
                details.append(
                    f"Offered stipend ({stipend_amount}) is below your minimum preference ({prefs.minimum_stipend})."
                )

    practical_score = (
        (sum(comparisons) / len(comparisons) * 100.0) if comparisons else None
    )

    return (
        PracticalFitComparison(
            work_mode_match=mode_match,
            location_match=loc_match,
            duration_match=dur_match,
            hours_match=hours_match,
            stipend_match=stipend_match,
            start_date_match=None,
            details=details,
        ),
        practical_score,
    )


def calculate_fit_score(
    skill_matches: list[SkillMatchItem],
    profile: StudentProfile,
    eligibility_status: OverallEligibility,
    practical_score: Optional[float],
    role_title: str = "",
    weights: dict[str, float] | None = None,
) -> FitScore:
    if weights is None:
        weights = DEFAULT_WEIGHTS

    req_matches = [m for m in skill_matches if m.is_required]
    pref_matches = [m for m in skill_matches if not m.is_required]

    # 1. Required skills score (0-100)
    req_score: Optional[float] = None
    if req_matches:
        points = 0.0
        for m in req_matches:
            if m.status == SkillEvidenceState.DEMONSTRATED:
                points += 1.0
            elif m.status == SkillEvidenceState.SELF_REPORTED:
                points += 0.75
            elif m.status == SkillEvidenceState.NOT_FOUND_IN_RESUME:
                points += 0.0
            elif m.status == SkillEvidenceState.CONFIRMED_GAP:
                points += 0.0
        req_score = (points / len(req_matches)) * 100.0

    # 2. Preferred skills score (0-100)
    pref_score: Optional[float] = None
    if pref_matches:
        points = 0.0
        for m in pref_matches:
            if m.status == SkillEvidenceState.DEMONSTRATED:
                points += 1.0
            elif m.status == SkillEvidenceState.SELF_REPORTED:
                points += 0.75
            else:
                points += 0.0
        pref_score = (points / len(pref_matches)) * 100.0

    # 3. Project and experience evidence score (0-100)
    proj_exp_score: Optional[float] = None
    if profile.projects or profile.experience:
        # Check relevance to required skills
        demonstrated_count = sum(
            1 for m in skill_matches if m.status == SkillEvidenceState.DEMONSTRATED
        )
        total_skills = len(skill_matches)
        if total_skills > 0:
            proj_exp_score = min(
                100.0, (demonstrated_count / total_skills) * 100.0 + 20.0
            )
        else:
            proj_exp_score = 75.0 if profile.projects else 50.0

    # 4. Education relevance score (0-100)
    edu_score: Optional[float] = None
    if profile.education:
        edu = profile.education[0]
        pts = 60.0
        if edu.discipline:
            normalized_discipline = normalize_discipline(edu.discipline)
            discipline_text = edu.discipline.casefold()
            if normalized_discipline in RELEVANT_DISCIPLINES:
                pts += 30.0
        if edu.cgpa is not None:
            # high cgpa bonus
            scale = edu.cgpa_scale or 4.0
            if (edu.cgpa / scale) >= 0.75:
                pts += 10.0
        edu_score = min(100.0, pts)

    # 5. Practical preference fit score
    # practical_score is passed in

    breakdown = ScoreBreakdown(
        required_skills=round(req_score, 1) if req_score is not None else None,
        preferred_skills=round(pref_score, 1) if pref_score is not None else None,
        project_experience=round(proj_exp_score, 1)
        if proj_exp_score is not None
        else None,
        education_relevance=round(edu_score, 1) if edu_score is not None else None,
        practical_preferences=round(practical_score, 1)
        if practical_score is not None
        else None,
    )

    component_values = {
        "required_skills": req_score,
        "preferred_skills": pref_score,
        "project_experience": proj_exp_score,
        "education_relevance": edu_score,
        "practical_preferences": practical_score,
    }

    evaluable_weights = {
        key: weights.get(key, DEFAULT_WEIGHTS[key])
        for key, value in component_values.items()
        if value is not None
    }
    total_evaluable_weight = sum(evaluable_weights.values())

    coverage_pct = round(total_evaluable_weight * 100.0, 1)
    unresolved_reasons: list[str] = []

    if req_score is None:
        unresolved_reasons.append("No specific required skills extracted from listing.")
    if pref_score is None:
        unresolved_reasons.append("No preferred skills listed.")
    if proj_exp_score is None:
        unresolved_reasons.append("No projects or work experience found in resume.")
    if practical_score is None:
        unresolved_reasons.append(
            "Practical details (mode, duration, stipend) not specified."
        )

    if total_evaluable_weight < 0.20:
        return FitScore(
            score=None,
            label="Not enough information",
            is_provisional=True,
            coverage_percentage=coverage_pct,
            breakdown=breakdown,
            unresolved_reasons=unresolved_reasons,
        )

    # Calculate normalized weighted score
    weighted_sum = sum(
        component_values[key] * weight
        for key, weight in evaluable_weights.items()
        if component_values[key] is not None
    )
    normalized_score = round(weighted_sum / total_evaluable_weight)

    is_provisional = (eligibility_status == OverallEligibility.NEEDS_CONFIRMATION) or (
        coverage_pct < 70.0
    )

    label = "Profile fit"
    if eligibility_status == OverallEligibility.NOT_ELIGIBLE:
        label = "Not eligible (academic/formal criteria unmet)"

    return FitScore(
        score=normalized_score,
        label=label,
        is_provisional=is_provisional,
        coverage_percentage=coverage_pct,
        breakdown=breakdown,
        unresolved_reasons=unresolved_reasons,
    )
