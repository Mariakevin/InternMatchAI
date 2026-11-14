import { Flag } from "lucide-react";

import { StatusStamp } from "../ui/StatusStamp";
import { gapPriorityRank, gapPriorityTone, normalizeLabel } from "../../lib/format";
import type { GapReport as GapReportType } from "../../types";

export function GapReport({ gapReport }: { gapReport: GapReportType }) {
  const gaps = [...gapReport.gaps].sort(
    (a, b) => gapPriorityRank(a.priority) - gapPriorityRank(b.priority),
  );

  return (
    <div className="gap-report">
      {gaps.length === 0 ? (
        <p className="plain-note">No material gaps were identified for this posting.</p>
      ) : (
        <div className="gap-list">
          {gaps.map((gap, index) => {
            const tone = gapPriorityTone(gap.priority);
            return (
              <div className={`gap-item gap-item--${tone}`} key={`${gap.skill_or_requirement}-${index}`}>
                <div className="gap-item__head">
                  <strong>{gap.skill_or_requirement}</strong>
                  <StatusStamp tone={tone} icon={<Flag size={12} />} mono>
                    {normalizeLabel(gap.priority).toUpperCase()}
                  </StatusStamp>
                </div>
                <p className="gap-item__category mono">{normalizeLabel(gap.category)}</p>
                <p className="gap-item__guidance">{gap.guidance}</p>
              </div>
            );
          })}
        </div>
      )}

      {gapReport.questions_for_employer.length > 0 ? (
        <div className="employer-questions">
          <h5 className="employer-questions__title">Questions to clarify with the employer</h5>
          <ol className="employer-questions__list">
            {gapReport.questions_for_employer.map((question, index) => (
              <li key={`${question}-${index}`}>
                <span className="mono employer-questions__number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span>{question}</span>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
    </div>
  );
}
