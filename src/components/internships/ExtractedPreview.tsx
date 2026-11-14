import { SlidersHorizontal } from "lucide-react";

import { Alert } from "../ui/Alert";
import { Disclosure } from "../ui/Disclosure";
import { Tag } from "../ui/Tag";
import type { ExtractionMeta } from "../../hooks/useWorkspace";
import { formatStipend, formatWorkMode } from "../../lib/format";
import type { InternshipDetail } from "../../types";

type ExtractedPreviewProps = {
  internship: InternshipDetail;
  meta?: ExtractionMeta;
  editorOpen: boolean;
  onToggleEditor: () => void;
};

export function ExtractedPreview({
  internship,
  meta,
  editorOpen,
  onToggleEditor,
}: ExtractedPreviewProps) {
  const hasData =
    internship.eligibility_conditions.length > 0 ||
    internship.required_skills.length > 0 ||
    internship.work_mode !== "any" ||
    internship.stipend_amount !== null ||
    internship.is_unpaid;

  if (!hasData && !meta?.attempted) return null;

  const conditions = internship.eligibility_conditions.length;
  const skills = internship.required_skills.length;

  return (
    <div className="extracted-preview">
      {meta?.stale ? (
        <Alert tone="warn" title="Re-extract required" className="extracted-preview__alert">
          The description changed, so extracted conditions, skills, mode, and stipend were
          cleared. Run auto-extract again before analyzing.
        </Alert>
      ) : null}

      <div className="extracted-preview__tags">
        <Tag label="MODE" tone="info">
          {formatWorkMode(internship.work_mode)}
        </Tag>
        <Tag label="STIPEND" tone="neutral">
          {formatStipend(internship)}
        </Tag>
        <Tag label="CONDITIONS" tone={conditions > 0 ? "warn" : "unknown"}>
          {conditions}
        </Tag>
        <Tag label="SKILLS" tone={skills > 0 ? "pass" : "unknown"}>
          {skills} required
        </Tag>
      </div>

      {!hasData && meta?.attempted ? (
        <p className="muted-note">
          No formal conditions or required skills were found in this description. You can
          inspect the empty ledger or revise the text.
        </p>
      ) : null}

      <Disclosure
        controls={`conditions-${internship.id}`}
        expanded={editorOpen}
        onToggle={onToggleEditor}
        icon={<SlidersHorizontal size={14} />}
        className="extracted-preview__disclosure"
      >
        {editorOpen ? "Hide extracted criteria" : "Review extracted criteria"}
      </Disclosure>
    </div>
  );
}
