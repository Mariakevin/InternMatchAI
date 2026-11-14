import { CheckCircle2, MinusCircle, XCircle } from "lucide-react";

import type { PracticalFitComparison } from "../../types";

const ROWS = [
  { key: "work_mode_match", label: "Work mode" },
  { key: "location_match", label: "Location" },
  { key: "duration_match", label: "Duration" },
  { key: "hours_match", label: "Weekly hours" },
  { key: "stipend_match", label: "Stipend" },
  { key: "start_date_match", label: "Start date" },
] as const;

function stateMeta(value: boolean | null | undefined) {
  if (value === true) {
    return { icon: <CheckCircle2 size={14} />, word: "Aligned", tone: "pass" as const };
  }
  if (value === false) {
    return { icon: <XCircle size={14} />, word: "Mismatch", tone: "fail" as const };
  }
  return { icon: <MinusCircle size={14} />, word: "Unverified", tone: "unknown" as const };
}

export function PracticalFitList({ practicalFit }: { practicalFit: PracticalFitComparison }) {
  return (
    <div className="practical-fit">
      <div className="practical-fit__rows">
        {ROWS.map((row) => {
          const meta = stateMeta(practicalFit[row.key]);
          return (
            <div className={`practical-row practical-row--${meta.tone}`} key={row.key}>
              <span className="practical-row__icon" aria-hidden="true">
                {meta.icon}
              </span>
              <span className="practical-row__label">{row.label}</span>
              <span className="practical-row__state mono">{meta.word.toUpperCase()}</span>
            </div>
          );
        })}
      </div>

      {practicalFit.details.length > 0 ? (
        <ul className="practical-fit__details">
          {practicalFit.details.map((detail, index) => (
            <li key={`${detail}-${index}`}>{detail}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
