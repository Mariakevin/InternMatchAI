import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";

import { StatusStamp } from "../ui/StatusStamp";
import {
  eligibilityLabel,
  eligibilityTone,
  formatConditionValue,
  formatDuration,
  formatStipend,
  formatWorkMode,
} from "../../lib/format";
import type {
  InternshipDetail,
  InternshipMatchAnalysis,
  MatchResponse,
  OverallEligibility,
} from "../../types";

function statusIcon(status: OverallEligibility) {
  switch (status) {
    case "ELIGIBLE":
      return <CheckCircle2 size={12} />;
    case "NOT_ELIGIBLE":
      return <XCircle size={12} />;
    case "NEEDS_CONFIRMATION":
      return <AlertTriangle size={12} />;
    default:
      return <Info size={12} />;
  }
}

function roleNumber(
  match: InternshipMatchAnalysis,
  internships: InternshipDetail[],
  fallbackIndex: number,
): string {
  const index = internships.findIndex((item) => item.id === match.internship_id);
  return String((index >= 0 ? index : fallbackIndex) + 1).padStart(2, "0");
}

function skillsEvidenced(match: InternshipMatchAnalysis): string {
  const required = match.skill_matches.filter((row) => row.is_required);
  if (required.length === 0) return "—";
  const met = required.filter(
    (row) => row.status === "DEMONSTRATED" || row.status === "SELF_REPORTED",
  ).length;
  return `${met} of ${required.length}`;
}

type ComparisonTableProps = {
  result: MatchResponse;
  internships: InternshipDetail[];
};

export function ComparisonTable({ result, internships }: ComparisonTableProps) {
  const matches = result.matches ?? [];

  return (
    <div className="comparison-table-wrap">
      <table className="comparison-table">
        <caption className="sr-only">Side-by-side comparison of analyzed internships</caption>
        <thead>
          <tr>
            <th scope="col" className="comparison-table__metric-head">
              Metric
            </th>
            {matches.map((match, matchIndex) => (
              <th scope="col" key={match.internship_id}>
                <span className="mono comparison-table__role">
                  ROLE {roleNumber(match, internships, matchIndex)}
                </span>
                <strong>{match.title || "Untitled role"}</strong>
                <small>{match.company || "Company not stated"}</small>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Eligibility</th>
            {matches.map((match) => (
              <td key={match.internship_id}>
                <StatusStamp
                  tone={eligibilityTone(match.eligibility.status)}
                  icon={statusIcon(match.eligibility.status)}
                  mono
                >
                  {eligibilityLabel(match.eligibility.status).toUpperCase()}
                </StatusStamp>
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Fit score</th>
            {matches.map((match) => (
              <td key={match.internship_id} className="mono">
                {match.fit_score.score !== null && match.fit_score.score !== undefined
                  ? `${match.fit_score.score} / 100`
                  : "—"}
                {match.fit_score.is_provisional ? (
                  <span className="comparison-table__note"> · provisional</span>
                ) : null}
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Work mode</th>
            {matches.map((match) => (
              <td key={match.internship_id}>{formatWorkMode(match.internship_detail.work_mode)}</td>
            ))}
          </tr>
          <tr>
            <th scope="row">Location</th>
            {matches.map((match) => (
              <td key={match.internship_id}>
                {match.internship_detail.location.trim() || "—"}
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Duration</th>
            {matches.map((match) => (
              <td key={match.internship_id}>{formatDuration(match.internship_detail.duration_months)}</td>
            ))}
          </tr>
          <tr>
            <th scope="row">Weekly hours</th>
            {matches.map((match) => (
              <td key={match.internship_id} className="mono">
                {match.internship_detail.weekly_hours
                  ? `${match.internship_detail.weekly_hours} hrs/wk`
                  : "—"}
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Stipend</th>
            {matches.map((match) => (
              <td key={match.internship_id} className="mono">
                {formatStipend(match.internship_detail)}
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Required skills evidenced</th>
            {matches.map((match) => (
              <td key={match.internship_id} className="mono">
                {skillsEvidenced(match)}
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Mandatory conditions unmet</th>
            {matches.map((match) => {
              const failed = match.eligibility.conditions.filter(
                (condition) => condition.status === "FAIL",
              ).length;
              const unresolved = match.eligibility.conditions.filter(
                (condition) => condition.status === "UNKNOWN",
              ).length;
              return (
                <td key={match.internship_id} className="mono">
                  {failed} failed · {unresolved} unverified
                </td>
              );
            })}
          </tr>
          <tr>
            <th scope="row">First failing rule</th>
            {matches.map((match) => {
              const failed = match.eligibility.conditions.find(
                (condition) => condition.status === "FAIL",
              );
              return (
                <td key={match.internship_id}>
                  {failed
                    ? `${failed.condition_type}: ${formatConditionValue(failed.expected)}`
                    : "—"}
                </td>
              );
            })}
          </tr>
          <tr>
            <th scope="row">Listing warnings</th>
            {matches.map((match) => (
              <td key={match.internship_id} className="mono">
                {match.risk_indicators.length > 0
                  ? `${match.risk_indicators.length} flagged`
                  : "None"}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
