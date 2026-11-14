import type { ReactNode } from "react";
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from "lucide-react";

import type { Tone } from "../../lib/format";

type AlertProps = {
  tone?: Extract<Tone, "pass" | "warn" | "fail" | "info">;
  title?: string;
  children: ReactNode;
  className?: string;
};

function defaultIcon(tone: AlertProps["tone"]) {
  switch (tone) {
    case "pass":
      return <CheckCircle2 size={16} />;
    case "warn":
      return <AlertTriangle size={16} />;
    case "fail":
      return <AlertCircle size={16} />;
    default:
      return <Info size={16} />;
  }
}

export function Alert({ tone = "info", title, children, className }: AlertProps) {
  return (
    <div
      className={["alert", `alert--${tone}`, className ?? ""].filter(Boolean).join(" ")}
      role={tone === "fail" ? "alert" : undefined}
    >
      <span className="alert__icon" aria-hidden="true">
        {defaultIcon(tone)}
      </span>
      <div className="alert__body">
        {title ? <strong className="alert__title">{title}</strong> : null}
        <div className="alert__text">{children}</div>
      </div>
    </div>
  );
}
