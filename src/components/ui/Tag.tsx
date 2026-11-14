import type { ReactNode } from "react";

import type { Tone } from "../../lib/format";

type TagProps = {
  label?: string;
  tone?: Tone;
  children: ReactNode;
};

export function Tag({ label, tone = "neutral", children }: TagProps) {
  return (
    <span className={`tag tag--${tone}`}>
      {label ? <span className="tag__label">{label}</span> : null}
      <span className="tag__value">{children}</span>
    </span>
  );
}
