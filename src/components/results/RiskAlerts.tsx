import { ShieldAlert } from "lucide-react";

import { StatusStamp } from "../ui/StatusStamp";
import { riskSeverityMeta } from "../../lib/format";
import type { RiskIndicator } from "../../types";

export function RiskAlerts({ risks }: { risks: RiskIndicator[] }) {
  if (risks.length === 0) return null;

  return (
    <div className="risk-list" aria-label="Listing warnings">
      {risks.map((risk, index) => {
        const meta = riskSeverityMeta(risk.severity);
        return (
          <div className={`risk-item risk-item--${meta.tone}`} key={`${risk.category}-${index}`}>
            <span className="risk-item__icon" aria-hidden="true">
              <ShieldAlert size={16} />
            </span>
            <div className="risk-item__body">
              <div className="risk-item__head">
                <strong>Potential warning sign: {risk.title}</strong>
                <StatusStamp tone={meta.tone} icon={<ShieldAlert size={12} />} mono>
                  {meta.label.toUpperCase()}
                </StatusStamp>
              </div>
              <p className="risk-item__explanation">{risk.explanation}</p>
              {risk.excerpt ? (
                <blockquote className="risk-item__quote">“{risk.excerpt}”</blockquote>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}
