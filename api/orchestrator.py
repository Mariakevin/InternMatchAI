from __future__ import annotations


from api.eligibility_engine import evaluate_eligibility
from api.fit_scorer import calculate_fit_score, calculate_practical_fit
from api.internship_parser import analyze_listing_risks
from api.models import (
    InternshipDetail,
    InternshipMatchAnalysis,
    MatchResponse,
    StudentProfile,
)
from api.skill_matcher import match_skills


def analyze_single_internship(
    profile: StudentProfile,
    internship: InternshipDetail,
) -> InternshipMatchAnalysis:
    # 1. Listing risks
    risks = analyze_listing_risks(internship.description)

    # 2. Evaluate hard eligibility
    eligibility = evaluate_eligibility(
        conditions=internship.eligibility_conditions,
        profile=profile,
        has_posting_contradictions=internship.has_contradictions,
        contradiction_reasons=internship.contradiction_details,
    )

    # 3. Match skills
    skill_matches, gap_report = match_skills(
        required_skills=internship.required_skills,
        preferred_skills=internship.preferred_skills,
        profile=profile,
    )

    # 4. Practical preferences
    practical_fit, practical_score = calculate_practical_fit(
        profile=profile,
        internship_mode=internship.work_mode,
        internship_location=internship.location,
        internship_duration=internship.duration_months,
        internship_hours=internship.weekly_hours,
        stipend_amount=internship.stipend_amount,
        is_unpaid=internship.is_unpaid,
        stipend_currency=internship.stipend_currency,
        stipend_period=internship.stipend_period,
    )

    # 5. Fit score
    fit_score = calculate_fit_score(
        skill_matches=skill_matches,
        profile=profile,
        eligibility_status=eligibility.status,
        practical_score=practical_score,
        role_title=internship.title,
    )

    return InternshipMatchAnalysis(
        internship_id=internship.id,
        title=internship.title,
        company=internship.company,
        eligibility=eligibility,
        fit_score=fit_score,
        skill_matches=skill_matches,
        practical_fit=practical_fit,
        risk_indicators=risks,
        gap_report=gap_report,
        internship_detail=internship,
    )


def orchestrate_matching(
    profile: StudentProfile,
    internships: list[InternshipDetail],
) -> MatchResponse:
    analyses: list[InternshipMatchAnalysis] = []
    for internship in internships:
        analysis = analyze_single_internship(profile, internship)
        analyses.append(analysis)

    # Sort matches:
    # Priority:
    # 1. ELIGIBLE / NO_FORMAL_CRITERIA with highest score first
    # 2. NEEDS_CONFIRMATION with highest score
    # 3. NOT_ELIGIBLE at bottom
    def sort_key(item: InternshipMatchAnalysis):
        status_rank = {
            "ELIGIBLE": 0,
            "NO_FORMAL_CRITERIA": 0,
            "NEEDS_CONFIRMATION": 1,
            "NOT_ELIGIBLE": 2,
        }.get(item.eligibility.status.value, 3)
        score_val = item.fit_score.score or 0
        return (status_rank, -score_val, item.title.casefold())

    analyses.sort(key=sort_key)

    return MatchResponse(
        profile=profile,
        matches=analyses,
    )
