import { ScoreMeter } from "../ui/ScoreMeter";
import {
  coveragePercent,
  eligibilityTone,
  scoreBand,
} from "../../lib/format";
import type { FitScore, OverallEligibility } from "../../types";

type FitScoreBoxProps = {
  fitScore: FitScore;
  status: OverallEligibility;
};

export function FitScoreBox({ fitScore, status }: FitScoreBoxProps) {
  const score = fitScore.score ?? null;
  const band = scoreBand(score);
  const breakdown = fitScore.breakdown ?? {};
  const components = [
    breakdown.required_skills,
    breakdown.preferred_skills,
    breakdown.project_experience,
    breakdown.education_relevance,
    breakdown.practical_preferences,
  ];
  const covered = components.filter(
    (value) => value !== null && value !== undefined,
  ).length;
  const tone = eligibilityTone(status);
  const meterTone = tone === "pass" || tone === "warn" || tone === "fail" ? tone : "info";

  return (
    <div className={`fit-score fit-score--${tone}`}>
      <p className="fit-score__label mono">PROFILE FIT</p>
      <p className="fit-score__value-row">
        <span className="fit-score__value mono">{score ?? "—"}</span>
        <span className="fit-score__denom mono">/100</span>
      </p>
      <p className="fit-score__band">{band.label}</p>
      <ScoreMeter score={score} tone={meterTone} label={`Fit score ${score ?? "unscored"} of 100`} />
      <p className="fit-score__coverage mono">
        {covered} of 5 components · coverage {coveragePercent(fitScore.coverage_percentage)}
      </p>
      {fitScore.is_provisional ? (
        <span className="stamp stamp--warn mono">PROVISIONAL</span>
      ) : null}
    </div>
  );
}
