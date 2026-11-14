type ScoreMeterProps = {
  score: number | null;
  tone?: "pass" | "warn" | "fail" | "info" | "neutral";
  label: string;
};

const SEGMENTS = [0, 1, 2, 3, 4];

export function ScoreMeter({ score, tone = "neutral", label }: ScoreMeterProps) {
  const filled =
    score === null ? 0 : Math.max(0, Math.min(5, Math.ceil(score / 20)));

  return (
    <div className={`score-meter score-meter--${tone}`} role="img" aria-label={label}>
      {SEGMENTS.map((segment) => (
        <span
          key={segment}
          className={`score-meter__segment${segment < filled ? " is-filled" : ""}`}
        />
      ))}
    </div>
  );
}
