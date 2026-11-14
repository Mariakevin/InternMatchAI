type ProgressBarProps = {
  value: number | null;
  label: string;
  tone?: "accent" | "pass" | "warn" | "fail";
  indeterminate?: boolean;
};

export function ProgressBar({
  value,
  label,
  tone = "accent",
  indeterminate = false,
}: ProgressBarProps) {
  if (indeterminate) {
    return (
      <div
        className={`progress progress--${tone} progress--indeterminate`}
        role="progressbar"
        aria-label={label}
        aria-valuetext="In progress"
      >
        <span />
      </div>
    );
  }

  const clamped = Math.max(0, Math.min(100, value ?? 0));

  return (
    <div
      className={`progress progress--${tone}`}
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={value === null ? undefined : Math.round(clamped)}
      aria-valuetext={value === null ? "Not scored" : `${Math.round(clamped)}%`}
    >
      <span style={{ width: `${clamped}%` }} />
    </div>
  );
}
