import type {
  ConditionStatus,
  InternshipDetail,
  OverallEligibility,
  SkillEvidenceState,
  WorkMode,
} from "../types";

export type Tone = "pass" | "warn" | "fail" | "info" | "unknown" | "neutral";

const numberFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

export function formatNumber(value: number): string {
  return numberFormatter.format(value);
}

export function formatStipend(
  input: Pick<
    InternshipDetail,
    "is_unpaid" | "stipend_amount" | "stipend_currency" | "stipend_period"
  >,
): string {
  if (input.is_unpaid) return "Unpaid";
  if (input.stipend_amount === null || input.stipend_amount === undefined) {
    return "Not disclosed";
  }
  const period = input.stipend_period || "monthly";
  return `${input.stipend_currency || "USD"} ${formatNumber(input.stipend_amount)}/${periodLabel(period)}`;
}

function periodLabel(period: string): string {
  switch (period.toLowerCase()) {
    case "monthly":
      return "month";
    case "weekly":
      return "week";
    case "daily":
      return "day";
    case "hourly":
      return "hour";
    case "yearly":
    case "annual":
    case "annually":
      return "year";
    default:
      return period;
  }
}

export function formatWorkMode(mode: WorkMode): string {
  switch (mode) {
    case "remote":
      return "Remote";
    case "hybrid":
      return "Hybrid";
    case "on-site":
      return "On-site";
    default:
      return "Mode unspecified";
  }
}

export function formatDuration(months: number | null | undefined): string {
  if (months === null || months === undefined) return "Duration unstated";
  return months === 1 ? "1 month" : `${months} months`;
}

export function formatLocation(location: string | null | undefined): string {
  const trimmed = (location ?? "").trim();
  return trimmed || "Location not specified";
}

export function formatConditionValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) {
    const parts = value.map((item) => String(item)).filter(Boolean);
    return parts.length > 0 ? parts.join(" OR ") : "—";
  }
  if (typeof value === "object") return JSON.stringify(value);
  const text = String(value);
  return text.trim() || "—";
}

export function formatFileSize(bytes: number | null): string {
  if (bytes === null) return "";
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(kb < 10 ? 1 : 0)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

export function formatCgpa(cgpa: number | null | undefined, scale: number): string {
  if (cgpa === null || cgpa === undefined) return "Not stated";
  return `${cgpa} / ${scale}`;
}

export function normalizeLabel(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function eligibilityLabel(status: OverallEligibility): string {
  switch (status) {
    case "ELIGIBLE":
      return "Eligible";
    case "NOT_ELIGIBLE":
      return "Not eligible";
    case "NEEDS_CONFIRMATION":
      return "Needs confirmation";
    case "NO_FORMAL_CRITERIA":
      return "No formal criteria";
    default:
      return "Unknown";
  }
}

export function eligibilityDescription(status: OverallEligibility): string {
  switch (status) {
    case "ELIGIBLE":
      return "Every explicit academic condition is satisfied by your profile.";
    case "NOT_ELIGIBLE":
      return "At least one explicit mandatory condition is not satisfied.";
    case "NEEDS_CONFIRMATION":
      return "Some mandatory conditions cannot be verified from your profile.";
    case "NO_FORMAL_CRITERIA":
      return "The posting states no explicit academic conditions to evaluate.";
    default:
      return "Eligibility has not been determined.";
  }
}

export function eligibilityTone(status: OverallEligibility): Tone {
  switch (status) {
    case "ELIGIBLE":
      return "pass";
    case "NOT_ELIGIBLE":
      return "fail";
    case "NEEDS_CONFIRMATION":
      return "warn";
    default:
      return "info";
  }
}

export function conditionStatusLabel(status: ConditionStatus): string {
  switch (status) {
    case "PASS":
      return "Pass";
    case "FAIL":
      return "Fail";
    case "UNKNOWN":
      return "Unverified";
    case "CONFLICT":
      return "Conflict";
    default:
      return "Unknown";
  }
}

export function conditionTone(status: ConditionStatus): Tone {
  switch (status) {
    case "PASS":
      return "pass";
    case "FAIL":
      return "fail";
    case "CONFLICT":
      return "fail";
    default:
      return "warn";
  }
}

export function conditionTypeLabel(condition: { condition_type: string }): string {
  return normalizeLabel(condition.condition_type);
}

export function skillStatusLabel(status: SkillEvidenceState): string {
  switch (status) {
    case "DEMONSTRATED":
      return "Demonstrated";
    case "SELF_REPORTED":
      return "Self-reported";
    case "NOT_FOUND_IN_RESUME":
      return "No evidence found";
    case "CONFIRMED_GAP":
      return "Confirmed gap";
    default:
      return "Unknown";
  }
}

export function skillStatusTone(status: SkillEvidenceState): Tone {
  switch (status) {
    case "DEMONSTRATED":
      return "pass";
    case "SELF_REPORTED":
      return "info";
    case "CONFIRMED_GAP":
      return "fail";
    case "NOT_FOUND_IN_RESUME":
      return "unknown";
    default:
      return "unknown";
  }
}

export function scoreBand(score: number | null | undefined): { label: string; tone: Tone } {
  if (score === null || score === undefined) return { label: "Not scored", tone: "unknown" };
  if (score >= 75) return { label: "Strong fit", tone: "pass" };
  if (score >= 50) return { label: "Moderate fit", tone: "info" };
  if (score >= 25) return { label: "Limited fit", tone: "warn" };
  return { label: "Low fit", tone: "fail" };
}

export function riskSeverityMeta(severity: string): {
  label: string;
  tone: Tone;
} {
  const normalized = severity.toLowerCase();
  if (normalized === "warning") return { label: "Warning", tone: "fail" };
  if (normalized === "review_carefully") return { label: "Review carefully", tone: "warn" };
  if (normalized === "notice") return { label: "Notice", tone: "info" };
  return { label: normalizeLabel(severity), tone: "unknown" };
}

export function gapPriorityRank(priority: string): number {
  switch (priority.toLowerCase()) {
    case "high":
      return 0;
    case "medium":
      return 1;
    case "low":
      return 2;
    default:
      return 3;
  }
}

export function gapPriorityTone(priority: string): Tone {
  switch (priority.toLowerCase()) {
    case "high":
      return "fail";
    case "medium":
      return "warn";
    case "low":
      return "pass";
    default:
      return "unknown";
  }
}

export function coveragePercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value)}%`;
}
