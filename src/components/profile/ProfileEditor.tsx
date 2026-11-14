import { GraduationCap } from "lucide-react";

import { EducationFields } from "./EducationFields";
import { PreferencesForm } from "./PreferencesForm";
import { SkillsManager } from "./SkillsManager";
import type { EducationItem, StudentProfile } from "../../types";

type ProfileEditorProps = {
  open: boolean;
  profile: StudentProfile;
  newSkillInput: string;
  onEducationChange: (index: number, patch: Partial<EducationItem>) => void;
  onPreferencesChange: (patch: Partial<StudentProfile["preferences"]>) => void;
  onNewSkillChange: (value: string) => void;
  onAddSkill: () => void;
  onRemoveSkill: (normalizedName: string) => void;
};

export function ProfileEditor({
  open,
  profile,
  newSkillInput,
  onEducationChange,
  onPreferencesChange,
  onNewSkillChange,
  onAddSkill,
  onRemoveSkill,
}: ProfileEditorProps) {
  return (
    <section
      id="profile-editor"
      className="card editor-card"
      hidden={!open}
      aria-labelledby="profile-editor-title"
    >
      <div className="card__head">
        <span className="card__icon" aria-hidden="true">
          <GraduationCap size={18} />
        </span>
        <div>
          <h3 className="card__title" id="profile-editor-title">
            Editable academic profile &amp; preferences
          </h3>
          <p className="card__subtitle">
            Verify degree, GPA, and constraints before running matching.
          </p>
        </div>
      </div>

      <EducationFields education={profile.education} onChange={onEducationChange} />
      <PreferencesForm preferences={profile.preferences} onChange={onPreferencesChange} />
      <SkillsManager
        skills={profile.skills}
        newSkillInput={newSkillInput}
        onNewSkillChange={onNewSkillChange}
        onAddSkill={onAddSkill}
        onRemoveSkill={onRemoveSkill}
      />
    </section>
  );
}
