import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";

import { EligibilityChecklist } from "./EligibilityChecklist";
import { GapReport } from "./GapReport";
import { PracticalFitList } from "./PracticalFitList";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { SkillEvidenceTable } from "./SkillEvidenceTable";
import { StatusStamp } from "../ui/StatusStamp";
import { eligibilityLabel, eligibilityTone } from "../../lib/format";
import type { SkillCorrectionAction } from "../../hooks/useWorkspace";
import type { InternshipMatchAnalysis } from "../../types";

function statusIcon(status: InternshipMatchAnalysis["eligibility"]["status"]) {
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

function AuditSection({
  number,
  title,
  aside,
  children,
}: {
  number: string;
  title: string;
  aside?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="audit-section">
      <header className="audit-section__head">
        <span className="audit-section__number mono" aria-hidden="true">
          {number}
        </span>
        <h4 className="audit-section__title">{title}</h4>
        {aside ? <div className="audit-section__aside">{aside}</div> : null}
      </header>
      <div className="audit-section__body">{children}</div>
    </section>
  );
}

type AuditAccordionProps = {
  match: InternshipMatchAnalysis;
  correcting: boolean;
  onCorrect: (skillName: string, action: SkillCorrectionAction) => void;
};

export function AuditAccordion({ match, correcting, onCorrect }: AuditAccordionProps) {
  return (
    <div className="audit">
      <AuditSection
        number="1"
        title="Formal academic eligibility checklist"
        aside={
          <StatusStamp
            tone={eligibilityTone(match.eligibility.status)}
            icon={statusIcon(match.eligibility.status)}
            mono
          >
            {eligibilityLabel(match.eligibility.status).toUpperCase()}
          </StatusStamp>
        }
      >
        <EligibilityChecklist eligibility={match.eligibility} />
      </AuditSection>

      <AuditSection
        number="2"
        title="Explainable fit-score breakdown"
        aside={
          <span className="audit-section__note">
            Score cannot override ineligibility.
          </span>
        }
      >
        <ScoreBreakdown fitScore={match.fit_score} />
      </AuditSection>

      <AuditSection
        number="3"
        title="Skill evidence & student corrections"
        aside={
          <span className="audit-section__note">
            Missing keywords are not assumed to be missing skills.
          </span>
        }
      >
        <SkillEvidenceTable
          rows={match.skill_matches}
          correcting={correcting}
          onCorrect={onCorrect}
        />
      </AuditSection>

      <AuditSection number="4" title="Actionable next steps & employer questions">
        <GapReport gapReport={match.gap_report} />
      </AuditSection>

      <AuditSection number="5" title="Practical alignment with your constraints">
        <PracticalFitList practicalFit={match.practical_fit} />
      </AuditSection>
    </div>
  );
}
