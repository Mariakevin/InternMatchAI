from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class WorkMode(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "on-site"
    ANY = "any"


class ConditionStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


class OverallEligibility(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"
    NO_FORMAL_CRITERIA = "NO_FORMAL_CRITERIA"


class SkillEvidenceState(str, Enum):
    DEMONSTRATED = "DEMONSTRATED"
    SELF_REPORTED = "SELF_REPORTED"
    NOT_FOUND_IN_RESUME = "NOT_FOUND_IN_RESUME"
    CONFIRMED_GAP = "CONFIRMED_GAP"
    UNKNOWN = "UNKNOWN"


class StudentPreferences(BaseModel):
    preferred_work_modes: list[WorkMode] = Field(default_factory=lambda: [WorkMode.REMOTE, WorkMode.HYBRID, WorkMode.ONSITE])
    preferred_locations: list[str] = Field(default_factory=list)
    willing_to_relocate: bool = False
    earliest_start_date: Optional[str] = None
    latest_start_date: Optional[str] = None
    available_hours_per_week: Optional[int] = None
    preferred_duration_months: Optional[int] = None
    minimum_stipend: Optional[float] = None
    stipend_currency: str = "USD"
    stipend_period: str = "monthly"  # monthly, weekly, total, hourly
    unpaid_acceptable: bool = True


class EducationItem(BaseModel):
    level: str = ""  # undergraduate, postgraduate, diploma, doctorate
    degree: str = ""  # B.Tech, BCA, BS, M.Tech, MCA, etc.
    discipline: str = ""  # Computer Science, IT, etc.
    institution: str = ""
    current_year: Optional[int] = None
    current_semester: Optional[int] = None
    enrolment_status: str = "enrolled"  # enrolled, completed, graduated
    graduation_date: Optional[str] = None  # YYYY-MM or YYYY
    cgpa: Optional[float] = None
    cgpa_scale: float = 4.0  # 4.0, 10.0, or 100%


class SkillProvenance(BaseModel):
    name: str
    normalized_name: str
    source: str = "resume"  # resume, student_confirmed, manual
    evidence_refs: list[str] = Field(default_factory=list)
    student_confirmed: bool = False
    is_confirmed_gap: bool = False
    confidence: float = 1.0


class ProjectItem(BaseModel):
    title: str
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class ExperienceItem(BaseModel):
    role: str
    organization: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class StudentProfile(BaseModel):
    id: str = "default_student"
    education: list[EducationItem] = Field(default_factory=list)
    skills: list[SkillProvenance] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    coursework: list[str] = Field(default_factory=list)
    preferences: StudentPreferences = Field(default_factory=StudentPreferences)
    raw_text: str = ""


class EligibilityCondition(BaseModel):
    condition_id: str
    condition_type: str  # degree, discipline, year, semester, enrolment, graduation_date, marks, location, citizenship, other
    operator: str  # ==, in, >=, <=, between
    value: Any  # string, list of strings, number, or tuple/range
    logic_group: str = "default"  # Group name or boolean logic ID: conditions in same group are OR, between groups AND
    is_mandatory: bool = True
    original_text: str = ""
    source_reference: str = ""
    extraction_confidence: float = 1.0


class InternshipDetail(BaseModel):
    id: str = "0"
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(default="", max_length=200)
    source_url: Optional[str] = None
    description: str = Field(min_length=1, max_length=20000)
    domain: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    work_mode: WorkMode = WorkMode.ANY
    location: str = ""
    duration_months: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    weekly_hours: Optional[int] = None
    stipend_amount: Optional[float] = None
    stipend_currency: str = "USD"
    stipend_period: str = "monthly"
    stipend_disclosed: bool = True
    is_unpaid: bool = False
    application_deadline: Optional[str] = None
    eligibility_conditions: list[EligibilityCondition] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    tools_and_tech: list[str] = Field(default_factory=list)
    has_contradictions: bool = False
    contradiction_details: list[str] = Field(default_factory=list)


class ConditionEvaluation(BaseModel):
    condition_id: str
    condition_type: str
    is_mandatory: bool
    status: ConditionStatus  # PASS, FAIL, UNKNOWN, CONFLICT
    original_text: str
    expected: Any
    actual: Any
    reason: str
    logic_group: str


class EligibilityResult(BaseModel):
    status: OverallEligibility
    summary: str
    unresolved_mandatory_count: int = 0
    conditions: list[ConditionEvaluation] = Field(default_factory=list)


class SkillMatchItem(BaseModel):
    internship_skill: str
    normalized_skill: str
    status: SkillEvidenceState  # DEMONSTRATED, SELF_REPORTED, NOT_FOUND_IN_RESUME, CONFIRMED_GAP, UNKNOWN
    is_required: bool = True
    matched_student_skill: Optional[str] = None
    evidence_source: str = ""  # projects, experience, coursework, self_report, none
    supporting_excerpt: str = ""
    confidence: float = 1.0


class ScoreBreakdown(BaseModel):
    required_skills: Optional[float] = None
    preferred_skills: Optional[float] = None
    project_experience: Optional[float] = None
    education_relevance: Optional[float] = None
    practical_preferences: Optional[float] = None


class FitScore(BaseModel):
    score: Optional[int] = None  # 0-100 whole number or None if not enough info
    label: str = "Profile fit"
    is_provisional: bool = False
    coverage_percentage: float = 100.0
    formula_description: str = (
        "Weighted score: Required skills (30%), Preferred skills (15%), "
        "Projects/Experience (25%), Education relevance (15%), Practical preferences (15%)."
    )
    breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    unresolved_reasons: list[str] = Field(default_factory=list)


class PracticalFitComparison(BaseModel):
    work_mode_match: Optional[bool] = None
    location_match: Optional[bool] = None
    duration_match: Optional[bool] = None
    hours_match: Optional[bool] = None
    stipend_match: Optional[bool] = None
    start_date_match: Optional[bool] = None
    details: list[str] = Field(default_factory=list)


class RiskIndicator(BaseModel):
    category: str  # application_fee, security_deposit, paid_training, guaranteed_job, early_sensitive_data, vague_identity, unpaid_warning
    severity: str  # warning, notice, review_carefully
    title: str
    excerpt: str
    explanation: str


class GapItem(BaseModel):
    skill_or_requirement: str
    category: str  # missing_required, missing_preferred, confirmed_gap, missing_proof
    guidance: str  # e.g., "Learn this skill" vs "If you have used this in a project, document it"
    priority: str  # high, medium, low


class GapReport(BaseModel):
    gaps: list[GapItem] = Field(default_factory=list)
    questions_for_employer: list[str] = Field(default_factory=list)


class InternshipMatchAnalysis(BaseModel):
    internship_id: str
    title: str
    company: str
    eligibility: EligibilityResult
    fit_score: FitScore
    skill_matches: list[SkillMatchItem] = Field(default_factory=list)
    practical_fit: PracticalFitComparison = Field(default_factory=PracticalFitComparison)
    risk_indicators: list[RiskIndicator] = Field(default_factory=list)
    gap_report: GapReport = Field(default_factory=GapReport)
    internship_detail: InternshipDetail


class MatchResponse(BaseModel):
    profile: StudentProfile
    matches: list[InternshipMatchAnalysis]
    scoring_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "required_skills": 0.30,
            "preferred_skills": 0.15,
            "project_experience": 0.25,
            "education_relevance": 0.15,
            "practical_preferences": 0.15,
        }
    )
