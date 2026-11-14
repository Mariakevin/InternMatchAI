import { Edit3, GraduationCap, MapPin, Timer } from "lucide-react";

import { Button } from "../ui/Button";
import { formatCgpa, formatWorkMode } from "../../lib/format";
import type { StudentProfile } from "../../types";

type ProfileSnapshotProps = {
  profile: StudentProfile;
  editorOpen: boolean;
  onToggleEditor: () => void;
};

export function ProfileSnapshot({ profile, editorOpen, onToggleEditor }: ProfileSnapshotProps) {
  const education = profile.education[0];
  const modes = profile.preferences.preferred_work_modes
    .filter((mode) => mode !== "any")
    .map((mode) => formatWorkMode(mode))
    .join(" · ");

  return (
    <section className="card snapshot-card" aria-labelledby="snapshot-title">
      <div className="card__head">
        <span className="card__icon" aria-hidden="true">
          <GraduationCap size={18} />
        </span>
        <div>
          <h3 className="card__title" id="snapshot-title">
            Profile snapshot
          </h3>
          <p className="card__subtitle">What the audit will read from your profile.</p>
        </div>
      </div>

      <dl className="snapshot-grid">
        <div className="snapshot-row">
          <dt>Degree</dt>
          <dd>
            <strong>{education?.degree || "Not captured"}</strong>
            {education?.discipline ? <span>{education.discipline}</span> : null}
          </dd>
        </div>
        <div className="snapshot-row">
          <dt>CGPA</dt>
          <dd className="mono">
            {education ? formatCgpa(education.cgpa, education.cgpa_scale) : "—"}
          </dd>
        </div>
        <div className="snapshot-row">
          <dt>Graduation</dt>
          <dd className="mono">{education?.graduation_date || "Not stated"}</dd>
        </div>
        <div className="snapshot-row">
          <dt>Skills</dt>
          <dd>
            <span className="mono">{profile.skills.length}</span> captured
            {profile.skills.length > 0 ? (
              <span className="snapshot-row__note">
                {" "}
                · {profile.skills.filter((skill) => !skill.is_confirmed_gap).length} usable
              </span>
            ) : null}
          </dd>
        </div>
        <div className="snapshot-row snapshot-row--wide">
          <dt>
            <MapPin size={12} aria-hidden="true" /> Preferred modes
          </dt>
          <dd>{modes || "None selected"}</dd>
        </div>
        <div className="snapshot-row snapshot-row--wide">
          <dt>
            <Timer size={12} aria-hidden="true" /> Weekly availability
          </dt>
          <dd className="mono">
            {profile.preferences.available_hours_per_week
              ? `${profile.preferences.available_hours_per_week} hrs / week`
              : "Not stated"}
            {profile.preferences.minimum_stipend
              ? ` · min ${profile.preferences.stipend_currency} ${profile.preferences.minimum_stipend}/mo`
              : ""}
          </dd>
        </div>
      </dl>

      <Button
        variant="secondary"
        size="sm"
        icon={<Edit3 size={14} />}
        onClick={onToggleEditor}
        aria-expanded={editorOpen}
        aria-controls="profile-editor"
      >
        {editorOpen ? "Close profile editor" : "Edit profile"}
      </Button>
    </section>
  );
}
