export type WorkMode = "remote" | "hybrid" | "on-site" | "any";

export type ConditionStatus = "PASS" | "FAIL" | "UNKNOWN" | "CONFLICT";

export type OverallEligibility =
  | "ELIGIBLE"
  | "NOT_ELIGIBLE"
  | "NEEDS_CONFIRMATION"
  | "NO_FORMAL_CRITERIA";

export type SkillEvidenceState =
  | "DEMONSTRATED"
  | "SELF_REPORTED"
  | "NOT_FOUND_IN_RESUME"
  | "CONFIRMED_GAP"
  | "UNKNOWN";

export type StudentPreferences = {
  preferred_work_modes: WorkMode[];
  preferred_locations: string[];
  willing_to_relocate: boolean;
  earliest_start_date?: string | null;
  latest_start_date?: string | null;
  available_hours_per_week?: number | null;
  preferred_duration_months?: number | null;
  minimum_stipend?: number | null;
  stipend_currency: string;
  stipend_period: string;
  unpaid_acceptable: boolean;
};

export type EducationItem = {
  level: string;
  degree: string;
  discipline: string;
  institution: string;
  current_year?: number | null;
  current_semester?: number | null;
  enrolment_status: string;
  graduation_date?: string | null;
  cgpa?: number | null;
  cgpa_scale: number;
};

export type SkillProvenance = {
  name: string;
  normalized_name: string;
  source: string;
  evidence_refs: string[];
  student_confirmed: boolean;
  is_confirmed_gap: boolean;
  confidence: number;
};

export type ProjectItem = {
  title: string;
  description: string;
  technologies: string[];
};

export type ExperienceItem = {
  role: string;
  organization: string;
  description: string;
  technologies: string[];
};

export type StudentProfile = {
  id: string;
  education: EducationItem[];
  skills: SkillProvenance[];
  projects: ProjectItem[];
  experience: ExperienceItem[];
  certifications: string[];
  coursework: string[];
  preferences: StudentPreferences;
  raw_text: string;
};

export type EligibilityCondition = {
  condition_id: string;
  condition_type: string;
  operator: string;
  value: any;
  logic_group: string;
  is_mandatory: boolean;
  original_text: string;
  source_reference: string;
  extraction_confidence: number;
};

export type InternshipDetail = {
  id: string;
  title: string;
  company: string;
  source_url?: string | null;
  description: string;
  domain: string;
  responsibilities: string[];
  work_mode: WorkMode;
  location: string;
  duration_months?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  weekly_hours?: number | null;
  stipend_amount?: number | null;
  stipend_currency: string;
  stipend_period: string;
  stipend_disclosed: boolean;
  is_unpaid: boolean;
  application_deadline?: string | null;
  eligibility_conditions: EligibilityCondition[];
  required_skills: string[];
  preferred_skills: string[];
  tools_and_tech: string[];
  has_contradictions: boolean;
  contradiction_details: string[];
};

export type ConditionEvaluation = {
  condition_id: string;
  condition_type: string;
  is_mandatory: boolean;
  status: ConditionStatus;
  original_text: string;
  expected: any;
  actual: any;
  reason: string;
  logic_group: string;
};

export type EligibilityResult = {
  status: OverallEligibility;
  summary: string;
  unresolved_mandatory_count: number;
  conditions: ConditionEvaluation[];
};

export type SkillMatchItem = {
  internship_skill: string;
  normalized_skill: string;
  status: SkillEvidenceState;
  is_required: boolean;
  matched_student_skill?: string | null;
  evidence_source: string;
  supporting_excerpt: string;
  confidence: number;
};

export type ScoreBreakdown = {
  required_skills?: number | null;
  preferred_skills?: number | null;
  project_experience?: number | null;
  education_relevance?: number | null;
  practical_preferences?: number | null;
};

export type FitScore = {
  score?: number | null;
  label: string;
  is_provisional: boolean;
  coverage_percentage: number;
  formula_description: string;
  breakdown: ScoreBreakdown;
  unresolved_reasons: string[];
};

export type PracticalFitComparison = {
  work_mode_match?: boolean | null;
  location_match?: boolean | null;
  duration_match?: boolean | null;
  hours_match?: boolean | null;
  stipend_match?: boolean | null;
  start_date_match?: boolean | null;
  details: string[];
};

export type RiskIndicator = {
  category: string;
  severity: string;
  title: string;
  excerpt: string;
  explanation: string;
};

export type GapItem = {
  skill_or_requirement: string;
  category: string;
  guidance: string;
  priority: string;
};

export type GapReport = {
  gaps: GapItem[];
  questions_for_employer: string[];
};

export type InternshipMatchAnalysis = {
  internship_id: string;
  title: string;
  company: string;
  eligibility: EligibilityResult;
  fit_score: FitScore;
  skill_matches: SkillMatchItem[];
  practical_fit: PracticalFitComparison;
  risk_indicators: RiskIndicator[];
  gap_report: GapReport;
  internship_detail: InternshipDetail;
};

export type MatchResponse = {
  profile: StudentProfile;
  matches: InternshipMatchAnalysis[];
  scoring_weights: Record<string, number>;
};
