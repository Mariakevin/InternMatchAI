import { Plus } from "lucide-react";

import { InternshipCard } from "./InternshipCard";
import type { ExtractionMeta } from "../../hooks/useWorkspace";
import type { InternshipDetail } from "../../types";

type InternshipListProps = {
  internships: InternshipDetail[];
  extractingIds: Record<string, boolean>;
  extractionMeta: Record<string, ExtractionMeta>;
  extractionErrors: Record<string, string>;
  editingId: string | null;
  onFieldChange: (
    id: string,
    field: keyof InternshipDetail,
    value: InternshipDetail[keyof InternshipDetail],
  ) => void;
  onExtract: (id: string) => void;
  onRemove: (id: string) => void;
  onToggleEditor: (id: string) => void;
  onAdd: () => void;
};

export function InternshipList({
  internships,
  extractingIds,
  extractionMeta,
  extractionErrors,
  editingId,
  onFieldChange,
  onExtract,
  onRemove,
  onToggleEditor,
  onAdd,
}: InternshipListProps) {
  return (
    <div className="roles">
      <div className="roles-list">
        {internships.map((internship, index) => (
          <InternshipCard
            key={internship.id}
            internship={internship}
            index={index}
            canRemove={internships.length > 1}
            extracting={Boolean(extractingIds[internship.id])}
            extractionError={extractionErrors[internship.id] ?? ""}
            meta={extractionMeta[internship.id]}
            editorOpen={editingId === internship.id}
            onFieldChange={onFieldChange}
            onExtract={onExtract}
            onRemove={onRemove}
            onToggleEditor={onToggleEditor}
          />
        ))}
      </div>

      {internships.length < 20 ? (
        <button type="button" className="add-role" onClick={onAdd}>
          <Plus size={16} aria-hidden="true" />
          <span>Add another opportunity</span>
          <span className="add-role__count mono">{internships.length} / 20</span>
        </button>
      ) : (
        <p className="limit-note mono">POSTING LIMIT REACHED · 20 / 20</p>
      )}
    </div>
  );
}
