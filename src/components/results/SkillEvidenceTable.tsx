import { AlertTriangle, CheckCircle2, CircleDashed, UserCheck } from "lucide-react";

import { StatusStamp } from "../ui/StatusStamp";
import {
  normalizeLabel,
  skillStatusLabel,
  skillStatusTone,
} from "../../lib/format";
import type { SkillCorrectionAction } from "../../hooks/useWorkspace";
import type { SkillEvidenceState, SkillMatchItem } from "../../types";

function statusIcon(status: SkillEvidenceState) {
  switch (status) {
    case "DEMONSTRATED":
      return <CheckCircle2 size={13} />;
    case "SELF_REPORTED":
      return <UserCheck size={13} />;
    case "CONFIRMED_GAP":
      return <AlertTriangle size={13} />;
    default:
      return <CircleDashed size={13} />;
  }
}

type SkillEvidenceTableProps = {
  rows: SkillMatchItem[];
  correcting: boolean;
  onCorrect: (skillName: string, action: SkillCorrectionAction) => void;
};

export function SkillEvidenceTable({ rows, correcting, onCorrect }: SkillEvidenceTableProps) {
  if (rows.length === 0) {
    return <p className="plain-note">No skill requirements were listed for this posting.</p>;
  }

  return (
    <div className="table-wrap skill-table-wrap">
      <table className="skill-table">
        <caption className="sr-only">
          Skill evidence with source, status, and student correction actions
        </caption>
        <thead>
          <tr>
            <th scope="col">Requirement</th>
            <th scope="col">Evidence</th>
            <th scope="col">Source</th>
            <th scope="col">Status</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.normalized_skill}-${index}`}>
              <th scope="row" className="skill-table__name">
                <strong>{row.internship_skill}</strong>
                <span className="mono">
                  {row.is_required ? "REQUIRED" : "PREFERRED"}
                </span>
              </th>
              <td data-label="Evidence" className="skill-table__evidence">
                {row.supporting_excerpt || "No excerpt captured."}
              </td>
              <td data-label="Source" className="mono skill-table__source">
                {normalizeLabel(row.evidence_source || "not stated")}
              </td>
              <td data-label="Status">
                <StatusStamp
                  tone={skillStatusTone(row.status)}
                  icon={statusIcon(row.status)}
                  mono
                >
                  {skillStatusLabel(row.status).toUpperCase()}
                </StatusStamp>
              </td>
              <td data-label="Actions" className="skill-table__actions">
                {row.status === "NOT_FOUND_IN_RESUME" ? (
                  <>
                    <button
                      type="button"
                      className="table-action table-action--yes"
                      onClick={() => onCorrect(row.normalized_skill, "self_report")}
                      disabled={correcting}
                    >
                      I know this
                    </button>
                    <button
                      type="button"
                      className="table-action table-action--no"
                      onClick={() => onCorrect(row.normalized_skill, "confirm_gap")}
                      disabled={correcting}
                    >
                      I don&apos;t know this
                    </button>
                  </>
                ) : row.status === "CONFIRMED_GAP" ? (
                  <button
                    type="button"
                    className="table-action table-action--yes"
                    onClick={() => onCorrect(row.normalized_skill, "self_report")}
                    disabled={correcting}
                  >
                    Switch to self-reported
                  </button>
                ) : (
                  <span className="muted-inline" aria-label="No action needed">
                    —
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
