import { useRef } from "react";
import type { KeyboardEvent } from "react";

import { MATCH_TABS, type MatchTab } from "../../lib/matchFilters";

type Counts = {
  all: number;
  eligible: number;
  needsConfirmation: number;
  notEligible: number;
};

const COUNT_KEYS: Record<MatchTab, keyof Counts> = {
  all: "all",
  ELIGIBLE: "eligible",
  NEEDS_CONFIRMATION: "needsConfirmation",
  NOT_ELIGIBLE: "notEligible",
};

type FilterTabsProps = {
  activeTab: MatchTab;
  counts: Counts;
  onChange: (tab: MatchTab) => void;
};

export function FilterTabs({ activeTab, counts, onChange }: FilterTabsProps) {
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    let nextIndex = index;

    if (event.key === "ArrowRight") nextIndex = (index + 1) % MATCH_TABS.length;
    else if (event.key === "ArrowLeft") nextIndex = (index - 1 + MATCH_TABS.length) % MATCH_TABS.length;
    else if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = MATCH_TABS.length - 1;
    else return;

    event.preventDefault();
    onChange(MATCH_TABS[nextIndex].id);
    tabRefs.current[nextIndex]?.focus();
  };

  return (
    <div className="filter-tabs" role="tablist" aria-label="Filter postings by eligibility">
      {MATCH_TABS.map((tab, index) => {
        const selected = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            ref={(element) => {
              tabRefs.current[index] = element;
            }}
            type="button"
            role="tab"
            id={`match-tab-${tab.id}`}
            aria-selected={selected}
            aria-controls="matches-panel"
            tabIndex={selected ? 0 : -1}
            className={`filter-tab filter-tab--${tab.id.toLowerCase()}${selected ? " is-active" : ""}`}
            onClick={() => onChange(tab.id)}
            onKeyDown={(event) => handleKeyDown(event, index)}
          >
            <span className="filter-tab__label">{tab.label}</span>
            <span className="filter-tab__count mono">{counts[COUNT_KEYS[tab.id]]}</span>
          </button>
        );
      })}
    </div>
  );
}
