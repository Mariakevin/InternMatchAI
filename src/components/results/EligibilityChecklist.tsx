import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";

import { StatusStamp } from "../ui/StatusStamp";
import {
  conditionStatusLabel,
  conditionTone,
  conditionTypeLabel,
  formatConditionValue,
} from "../../lib/format";
import type { ConditionStatus, EligibilityResult } from "../../types";

function statusIcon(status: ConditionStatus) {
  switch (status) {
    case "PASS":
      return <CheckCircle2 size={14} />;
    case "FAIL":
      return <XCircle size={14} />;
    case "CONFLICT":
      return <XCircle size={14} />;
    default:
      return <AlertTriangle size={14} />;
  }
}

export function EligibilityChecklist({ eligibility }: { eligibility: EligibilityResult }) {
  if (eligibility.conditions.length === 0) {
    return (
      <p className="plain-note">
        No explicit formal conditions — such as degree, CGPA, semester, or graduation date —
        were stated in this posting.
      </p>
    );
  }

  return (
    <div className="eligibility-ledger">
      <div className="eligibility-ledger__head" aria-hidden="true">
        <span>State</span>
        <span>Condition</span>
        <span>Expected / actual</span>
        <span>Reason &amp; source</span>
      </div>
      {eligibility.conditions.map((condition, index) => {
        const tone = conditionTone(condition.status);
        return (
          <div
            className={`eligibility-row eligibility-row--${tone}`}
            key={condition.condition_id || index}
          >
            <div className="eligibility-row__state" data-label="State">
              <StatusStamp tone={tone} icon={statusIcon(condition.status)} mono>
                {conditionStatusLabel(condition.status).toUpperCase()}
              </StatusStamp>
            </div>
            <div className="eligibility-row__type" data-label="Condition">
              <strong>{conditionTypeLabel(condition)}</strong>
              <span className="mono">
                {condition.is_mandatory ? "MANDATORY" : "OPTIONAL"} · GROUP{" "}
                {condition.logic_group}
              </span>
            </div>
            <div className="eligibility-row__values" data-label="Expected / actual">
              <span>
                <span className="mono eligibility-row__tag">EXPECTED</span>{" "}
                <code>{formatConditionValue(condition.expected)}</code>
              </span>
              <span>
                <span className="mono eligibility-row__tag">PROFILE</span>{" "}
                <code>
                  {condition.actual === null || condition.actual === undefined
                    ? "Not stated"
                    : formatConditionValue(condition.actual)}
                </code>
              </span>
            </div>
            <div className="eligibility-row__reason" data-label="Reason & source">
              <p>{condition.reason}</p>
              {condition.original_text ? (
                <blockquote>“{condition.original_text}”</blockquote>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}
