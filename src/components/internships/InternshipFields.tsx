import { RefreshCw } from "lucide-react";

import { Button } from "../ui/Button";
import { Field } from "../ui/Field";
import { Spinner } from "../ui/Spinner";
import type { InternshipDetail } from "../../types";

type InternshipFieldsProps = {
  internship: InternshipDetail;
  extracting: boolean;
  extractionError: string;
  onFieldChange: (
    id: string,
    field: keyof InternshipDetail,
    value: InternshipDetail[keyof InternshipDetail],
  ) => void;
  onExtract: (id: string) => void;
};

export function InternshipFields({
  internship,
  extracting,
  extractionError,
  onFieldChange,
  onExtract,
}: InternshipFieldsProps) {
  const prefix = `role-${internship.id}`;
  const descriptionId = `${prefix}-description`;

  return (
    <div className="role-card__fields">
      <div className="field-row">
        <Field htmlFor={`${prefix}-title`} label="Role title" required>
          <input
            id={`${prefix}-title`}
            className="input"
            value={internship.title}
            onChange={(event) => onFieldChange(internship.id, "title", event.target.value)}
            placeholder="e.g. Backend Software Engineer Intern"
            required
          />
        </Field>
        <Field htmlFor={`${prefix}-company`} label="Company / organization">
          <input
            id={`${prefix}-company`}
            className="input"
            value={internship.company}
            onChange={(event) => onFieldChange(internship.id, "company", event.target.value)}
            placeholder="e.g. Google, Datadog, Studio Labs"
          />
        </Field>
      </div>

      <Field
        htmlFor={descriptionId}
        label="Job description"
        required
        action={
          <Button
            variant="secondary"
            size="sm"
            icon={extracting ? <Spinner size={13} /> : <RefreshCw size={13} />}
            onClick={() => onExtract(internship.id)}
            disabled={extracting || !internship.description.trim()}
          >
            {extracting ? "Extracting…" : "Auto-extract criteria"}
          </Button>
        }
        help="Editing the description clears extracted criteria so matching never runs on stale data."
        error={extractionError || undefined}
      >
        <textarea
          id={descriptionId}
          className="textarea"
          value={internship.description}
          onChange={(event) =>
            onFieldChange(internship.id, "description", event.target.value)
          }
          placeholder="Paste the role description: eligibility conditions (degree, GPA, semester), required skills, stipend, work mode, duration…"
          rows={4}
          required
          aria-describedby={`${descriptionId}-help${
            extractionError ? ` ${descriptionId}-error` : ""
          }`}
          aria-invalid={extractionError ? true : undefined}
        />
      </Field>
    </div>
  );
}
