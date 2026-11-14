import { ProgressBar } from "../ui/ProgressBar";
import type { FitScore, ScoreBreakdown as ScoreBreakdownType } from "../../types";

const ROWS: Array<{ key: keyof ScoreBreakdownType; label: string; weight: number }> = [
  { key: "required_skills", label: "Required-skill evidence", weight: 30 },
  { key: "preferred_skills", label: "Preferred-skill relevance", weight: 15 },
  { key: "project_experience", label: "Project & experience evidence", weight: 25 },
  { key: "education_relevance", label: "Education relevance", weight: 15 },
  { key: "practical_preferences", label: "Practical preference fit", weight: 15 },
];

export function ScoreBreakdown({ fitScore }: { fitScore: FitScore }) {
  const breakdown = fitScore.breakdown ?? {};

  return (
    <div className="score-breakdown">
      <div className="score-breakdown__head" aria-hidden="true">
        <span>Component</span>
        <span>Weight</span>
        <span>Value</span>
      </div>
      {ROWS.map((row) => {
        const value = breakdown[row.key];
        const present = value !== null && value !== undefined;
        return (
          <div className="score-row" key={row.key}>
            <span className="score-row__label">{row.label}</span>
            <span className="score-row__weight mono">{row.weight}%</span>
            <span className="score-row__value mono">{present ? `${value}%` : "N/A"}</span>
            <div className="score-row__bar">
              <ProgressBar
                value={present ? value : null}
                label={`${row.label}: ${present ? `${value}%` : "not available"}`}
                tone="accent"
              />
            </div>
          </div>
        );
      })}
      <p className="score-breakdown__formula mono">
        {fitScore.formula_description ||
          "Required 30% + Preferred 15% + Projects 25% + Education 15% + Preferences 15%"}
      </p>
    </div>
  );
}
