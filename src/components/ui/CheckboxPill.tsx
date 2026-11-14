import type { ReactNode } from "react";
import { Check } from "lucide-react";

type CheckboxPillProps = {
  checked: boolean;
  onChange: (checked: boolean) => void;
  children: ReactNode;
  name?: string;
};

export function CheckboxPill({ checked, onChange, children, name }: CheckboxPillProps) {
  return (
    <label className={`check-pill${checked ? " is-checked" : ""}`}>
      <input
        type="checkbox"
        name={name}
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span className="check-pill__box" aria-hidden="true">
        {checked ? <Check size={13} strokeWidth={3} /> : null}
      </span>
      <span className="check-pill__label">{children}</span>
    </label>
  );
}
