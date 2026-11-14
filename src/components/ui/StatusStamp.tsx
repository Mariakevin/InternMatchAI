import type { ReactNode } from "react";

import type { Tone } from "../../lib/format";

type StatusStampProps = {
  tone: Tone;
  icon: ReactNode;
  children: ReactNode;
  mono?: boolean;
  className?: string;
};

export function StatusStamp({ tone, icon, children, mono = false, className }: StatusStampProps) {
  return (
    <span
      className={[
        "status-stamp",
        `status-stamp--${tone}`,
        mono ? "mono" : "",
        className ?? "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span className="status-stamp__icon" aria-hidden="true">
        {icon}
      </span>
      <span>{children}</span>
    </span>
  );
}
