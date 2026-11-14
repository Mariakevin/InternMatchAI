import type { InternshipMatchAnalysis, OverallEligibility } from "../types";

export type MatchTab = "all" | "ELIGIBLE" | "NEEDS_CONFIRMATION" | "NOT_ELIGIBLE";

export const MATCH_TABS: Array<{ id: MatchTab; label: string }> = [
  { id: "all", label: "All" },
  { id: "ELIGIBLE", label: "Eligible" },
  { id: "NEEDS_CONFIRMATION", label: "Needs confirmation" },
  { id: "NOT_ELIGIBLE", label: "Not eligible" },
];

export function statusMatchesTab(status: OverallEligibility, tab: MatchTab): boolean {
  if (tab === "all") return true;
  if (tab === "ELIGIBLE") {
    return status === "ELIGIBLE" || status === "NO_FORMAL_CRITERIA";
  }
  return status === tab;
}

export function filterMatches(
  matches: InternshipMatchAnalysis[],
  tab: MatchTab,
): InternshipMatchAnalysis[] {
  if (tab === "all") return matches;
  return matches.filter((match) => statusMatchesTab(match.eligibility.status, tab));
}

export function countMatches(
  matches: InternshipMatchAnalysis[],
  tab: MatchTab,
): number {
  return filterMatches(matches, tab).length;
}
