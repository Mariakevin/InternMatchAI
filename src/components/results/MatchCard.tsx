import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  DollarSign,
  Info,
  MapPin,
  Timer,
  XCircle,
} from "lucide-react";

import { AuditAccordion } from "./AuditAccordion";
import { FitScoreBox } from "./FitScoreBox";
import { RiskAlerts } from "./RiskAlerts";
import { Alert } from "../ui/Alert";
import { Disclosure } from "../ui/Disclosure";
import { StatusStamp } from "../ui/StatusStamp";
import {
  eligibilityLabel,
  eligibilityTone,
  formatDuration,
  formatLocation,
  formatStipend,
  formatWorkMode,
} from "../../lib/format";
import type { SkillCorrectionAction } from "../../hooks/useWorkspace";
import type { InternshipMatchAnalysis, OverallEligibility } from "../../types";

function statusIcon(status: OverallEligibility) {
  switch (status) {
    case "ELIGIBLE":
      return <CheckCircle2 size={13} />;
    case "NOT_ELIGIBLE":
      return <XCircle size={13} />;
    case "NEEDS_CONFIRMATION":
      return <AlertTriangle size={13} />;
    default:
      return <Info size={13} />;
  }
}

type MatchCardProps = {
  match: InternshipMatchAnalysis;
  roleNumber: string;
  expanded: boolean;
  onToggle: () => void;
  correcting: boolean;
  onCorrect: (skillName: string, action: SkillCorrectionAction) => void;
};

export function MatchCard({
  match,
  roleNumber,
  expanded,
  onToggle,
  correcting,
  onCorrect,
}: MatchCardProps) {
  const status = match.eligibility.status;
  const tone = eligibilityTone(status);
  const detail = match.internship_detail;
  const detailsId = `match-details-${match.internship_id}`;

  return (
    <article className={`match-card match-card--${tone}`} data-status={status}>
      <span className={`match-card__rail match-card__rail--${tone}`} aria-hidden="true" />

      {status === "NEEDS_CONFIRMATION" ? (
        <Alert tone="warn" title="Verification required before relying on this score">
          {match.eligibility.summary}
        </Alert>
      ) : null}

      {status === "NOT_ELIGIBLE" ? (
        <Alert tone="fail" title="Conclusively ineligible on stated conditions">
          {match.eligibility.summary}
        </Alert>
      ) : null}

      <header className="match-card__head">
        <div className="match-card__identity">
          <div className="match-card__meta">
            <span className="match-card__number mono">ROLE {roleNumber}</span>
            <StatusStamp tone={tone} icon={statusIcon(status)} mono>
              {eligibilityLabel(status).toUpperCase()}
            </StatusStamp>
          </div>
          <h3 className="match-card__title">{match.title || "Untitled role"}</h3>
          <p className="match-card__company">{match.company || "Company not stated"}</p>

          <ul className="match-facts">
            <li>
              <MapPin size={12} aria-hidden="true" />
              <span>
                <span className="mono">{formatWorkMode(detail.work_mode)}</span>
                <span className="match-facts__sep">·</span>
                {formatLocation(detail.location)}
              </span>
            </li>
            <li>
              <Clock size={12} aria-hidden="true" />
              <span>{formatDuration(detail.duration_months)}</span>
            </li>
            <li>
              <Timer size={12} aria-hidden="true" />
              <span className="mono">
                {detail.weekly_hours ? `${detail.weekly_hours} hrs/wk` : "Hours unstated"}
              </span>
            </li>
            <li>
              <DollarSign size={12} aria-hidden="true" />
              <span className="mono">{formatStipend(detail)}</span>
            </li>
          </ul>
        </div>

        <FitScoreBox fitScore={match.fit_score} status={status} />
      </header>

      <div className="match-card__body">
        <RiskAlerts risks={match.risk_indicators} />

        <Disclosure
          controls={detailsId}
          expanded={expanded}
          onToggle={onToggle}
          className="match-card__disclosure"
        >
          {expanded
            ? "Hide detailed evidence & checklist"
            : "Inspect eligibility checklist, score breakdown, and evidence trail"}
        </Disclosure>

        {expanded ? (
          <div id={detailsId} className="match-card__details">
            <AuditAccordion match={match} correcting={correcting} onCorrect={onCorrect} />
          </div>
        ) : null}
      </div>
    </article>
  );
}
