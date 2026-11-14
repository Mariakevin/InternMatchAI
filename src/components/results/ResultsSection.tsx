import {
  AlertTriangle,
  CheckCircle2,
  Columns3,
  ListChecks,
  XCircle,
} from "lucide-react";
import type { ReactNode } from "react";

import { FilterTabs } from "./FilterTabs";
import { MatchCard } from "./MatchCard";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { SectionHeading } from "../layout/SectionHeading";
import type { MatchTab } from "../../lib/matchFilters";
import type { SkillCorrectionAction } from "../../hooks/useWorkspace";
import type { InternshipDetail, MatchResponse } from "../../types";

type ResultsSectionProps = {
  result: MatchResponse;
  internships: InternshipDetail[];
  activeTab: MatchTab;
  filteredMatches: MatchResponse["matches"];
  counts: {
    all: number;
    eligible: number;
    needsConfirmation: number;
    notEligible: number;
  };
  expandedCards: Record<string, boolean>;
  correcting: boolean;
  onTabChange: (tab: MatchTab) => void;
  onToggleCard: (id: string) => void;
  onCorrect: (skillName: string, action: SkillCorrectionAction) => void;
  onOpenComparison: () => void;
};

function Stat({
  value,
  label,
  tone,
  icon,
}: {
  value: number;
  label: string;
  tone: string;
  icon: ReactNode;
}) {
  return (
    <div className={`result-stat result-stat--${tone}`}>
      <span className="result-stat__icon" aria-hidden="true">
        {icon}
      </span>
      <span className="result-stat__value mono">{String(value).padStart(2, "0")}</span>
      <span className="result-stat__label">{label}</span>
    </div>
  );
}

export function ResultsSection({
  result,
  internships,
  activeTab,
  filteredMatches,
  counts,
  expandedCards,
  correcting,
  onTabChange,
  onToggleCard,
  onCorrect,
  onOpenComparison,
}: ResultsSectionProps) {
  const matches = result.matches ?? [];
  const indexById = new Map(internships.map((item, index) => [item.id, index]));

  return (
    <section className="results" id="results" aria-labelledby="results-title">
      <SectionHeading
        id="results-title"
        index="03"
        title="Matchboard & audit trail"
        description="Sorted by eligibility, then fit. Every verdict is traceable to a stated rule or an excerpt."
        action={
          matches.length >= 2 ? (
            <Button
              variant="secondary"
              icon={<Columns3 size={15} />}
              onClick={onOpenComparison}
            >
              Compare postings
            </Button>
          ) : undefined
        }
      />

      <div className="result-summary" aria-label="Result summary">
        <Stat value={counts.all} label="All postings" tone="neutral" icon={<ListChecks size={15} />} />
        <Stat value={counts.eligible} label="Eligible" tone="pass" icon={<CheckCircle2 size={15} />} />
        <Stat
          value={counts.needsConfirmation}
          label="Needs confirmation"
          tone="warn"
          icon={<AlertTriangle size={15} />}
        />
        <Stat
          value={counts.notEligible}
          label="Not eligible"
          tone="fail"
          icon={<XCircle size={15} />}
        />
      </div>

      <FilterTabs activeTab={activeTab} counts={counts} onChange={onTabChange} />

      <div
        className="matches-panel"
        id="matches-panel"
        role="tabpanel"
        aria-labelledby={`match-tab-${activeTab}`}
        tabIndex={0}
      >
        {filteredMatches.length === 0 ? (
          <EmptyState
            title={`No postings under “${activeTab === "all" ? "all" : activeTab.replace(/_/g, " ").toLowerCase()}”`}
            description="Change the filter to inspect the other verdicts. No posting was removed."
            action={
              activeTab !== "all" ? (
                <Button variant="secondary" size="sm" onClick={() => onTabChange("all")}>
                  Show all postings
                </Button>
              ) : undefined
            }
          />
        ) : (
          <div className="matches-list">
            {filteredMatches.map((match, matchIndex) => {
              const found = indexById.get(match.internship_id);
              const originalIndex = found ?? matchIndex;
              return (
                <MatchCard
                  key={match.internship_id}
                  match={match}
                  roleNumber={String(originalIndex + 1).padStart(2, "0")}
                  expanded={Boolean(expandedCards[match.internship_id])}
                  onToggle={() => onToggleCard(match.internship_id)}
                  correcting={correcting}
                  onCorrect={onCorrect}
                />
              );
            })}
          </div>
        )}
      </div>

      <div className="results-disclaimer">
        <p>
          Fit scores represent profile similarity and practical alignment on the evidence
          provided. They are never a guarantee, ranking, or prediction of selection, and cannot
          override a failed mandatory condition.
        </p>
        <p>
          Listing warnings are cautious signals for you to verify — not conclusions about an
          organisation. Always confirm requirements and terms directly with the employer.
        </p>
      </div>
    </section>
  );
}
