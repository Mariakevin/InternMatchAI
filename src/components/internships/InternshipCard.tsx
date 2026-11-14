import { X } from "lucide-react";

import { ConditionsEditor } from "./ConditionsEditor";
import { ExtractedPreview } from "./ExtractedPreview";
import { InternshipFields } from "./InternshipFields";
import { IconButton } from "../ui/IconButton";
import type { ExtractionMeta } from "../../hooks/useWorkspace";
import type { InternshipDetail } from "../../types";

type InternshipCardProps = {
  internship: InternshipDetail;
  index: number;
  canRemove: boolean;
  extracting: boolean;
  extractionError: string;
  meta?: ExtractionMeta;
  editorOpen: boolean;
  onFieldChange: (
    id: string,
    field: keyof InternshipDetail,
    value: InternshipDetail[keyof InternshipDetail],
  ) => void;
  onExtract: (id: string) => void;
  onRemove: (id: string) => void;
  onToggleEditor: (id: string) => void;
};

export function InternshipCard({
  internship,
  index,
  canRemove,
  extracting,
  extractionError,
  meta,
  editorOpen,
  onFieldChange,
  onExtract,
  onRemove,
  onToggleEditor,
}: InternshipCardProps) {
  const number = String(index + 1).padStart(2, "0");
  const headingId = `role-${internship.id}-heading`;
  const hasData =
    internship.eligibility_conditions.length > 0 ||
    internship.required_skills.length > 0 ||
    internship.work_mode !== "any" ||
    internship.stipend_amount !== null ||
    internship.is_unpaid;

  return (
    <article className="card role-card" aria-labelledby={headingId}>
      <div className="role-card__head">
        <span className="role-card__index mono" aria-hidden="true">
          {number}
        </span>
        <h3 className="sr-only" id={headingId}>
          Internship role {number}: {internship.title || internship.company || "untitled"}
        </h3>
        <span className="role-card__label mono">INTERNSHIP ROLE</span>
        <IconButton
          label={`Remove internship role ${number}`}
          icon={<X size={16} />}
          className="role-card__remove"
          onClick={() => onRemove(internship.id)}
          disabled={!canRemove}
        />
      </div>

      <InternshipFields
        internship={internship}
        extracting={extracting}
        extractionError={extractionError}
        onFieldChange={onFieldChange}
        onExtract={onExtract}
      />

      <ExtractedPreview
        internship={internship}
        meta={meta}
        editorOpen={editorOpen}
        onToggleEditor={() => onToggleEditor(internship.id)}
      />

      {editorOpen && (meta?.attempted || hasData) ? (
        <ConditionsEditor
          internship={internship}
          onRemoveCondition={(conditionIndex) => {
            const next = internship.eligibility_conditions.filter(
              (_, itemIndex) => itemIndex !== conditionIndex,
            );
            onFieldChange(internship.id, "eligibility_conditions", next);
          }}
        />
      ) : null}
    </article>
  );
}
