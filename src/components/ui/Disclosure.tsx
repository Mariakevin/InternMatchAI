import type { ReactNode } from "react";
import { ChevronDown } from "lucide-react";

type DisclosureProps = {
  controls: string;
  expanded: boolean;
  onToggle: () => void;
  children: ReactNode;
  icon?: ReactNode;
  className?: string;
};

export function Disclosure({
  controls,
  expanded,
  onToggle,
  children,
  icon,
  className,
}: DisclosureProps) {
  return (
    <button
      type="button"
      className={["disclosure", className ?? ""].filter(Boolean).join(" ")}
      aria-expanded={expanded}
      aria-controls={controls}
      onClick={onToggle}
    >
      {icon ? (
        <span className="disclosure__icon" aria-hidden="true">
          {icon}
        </span>
      ) : null}
      <span className="disclosure__label">{children}</span>
      <ChevronDown
        size={16}
        className={`disclosure__chevron${expanded ? " is-open" : ""}`}
        aria-hidden="true"
      />
    </button>
  );
}
