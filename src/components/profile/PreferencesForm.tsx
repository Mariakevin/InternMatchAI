import { CheckboxPill } from "../ui/CheckboxPill";
import { Field } from "../ui/Field";
import type { StudentPreferences, WorkMode } from "../../types";

const WORK_MODES: Array<{ value: WorkMode; label: string }> = [
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "on-site", label: "On-site" },
];

type PreferencesFormProps = {
  preferences: StudentPreferences;
  onChange: (patch: Partial<StudentPreferences>) => void;
};

export function PreferencesForm({ preferences, onChange }: PreferencesFormProps) {
  const toggleMode = (mode: WorkMode, checked: boolean) => {
    const current = preferences.preferred_work_modes;
    const next = checked ? [...current, mode] : current.filter((item) => item !== mode);
    onChange({ preferred_work_modes: next });
  };

  return (
    <section className="editor-block" aria-labelledby="preferences-title">
      <h4 className="editor-block__title" id="preferences-title">
        Practical preferences
      </h4>
      <p className="editor-block__hint">
        These shape the practical-fit component, not academic eligibility.
      </p>

      <fieldset className="fieldset">
        <legend className="fieldset__legend">Acceptable work modes</legend>
        <div className="check-pill-row">
          {WORK_MODES.map((mode) => (
            <CheckboxPill
              key={mode.value}
              name="work-mode"
              checked={preferences.preferred_work_modes.includes(mode.value)}
              onChange={(checked) => toggleMode(mode.value, checked)}
            >
              {mode.label}
            </CheckboxPill>
          ))}
        </div>
      </fieldset>

      <div className="field-grid field-grid--preferences">
        <Field htmlFor="pref-hours" label="Hours / week available">
          <input
            id="pref-hours"
            className="input mono"
            type="number"
            inputMode="numeric"
            min="0"
            max="168"
            value={preferences.available_hours_per_week ?? ""}
            onChange={(event) =>
              onChange({
                available_hours_per_week:
                  event.target.value === "" ? null : Number(event.target.value),
              })
            }
            placeholder="e.g. 40"
          />
        </Field>

        <Field
          htmlFor="pref-stipend"
          label={`Minimum stipend (${preferences.stipend_currency || "USD"} / month)`}
        >
          <input
            id="pref-stipend"
            className="input mono"
            type="number"
            inputMode="numeric"
            min="0"
            value={preferences.minimum_stipend ?? ""}
            onChange={(event) =>
              onChange({
                minimum_stipend:
                  event.target.value === "" ? null : Number(event.target.value),
              })
            }
            placeholder="e.g. 1000"
          />
        </Field>
      </div>

      <div className="check-pill-row check-pill-row--loose">
        <CheckboxPill
          name="unpaid"
          checked={preferences.unpaid_acceptable}
          onChange={(checked) => onChange({ unpaid_acceptable: checked })}
        >
          Unpaid or volunteer positions are acceptable
        </CheckboxPill>
      </div>
    </section>
  );
}
