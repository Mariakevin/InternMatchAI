import { Plus, X } from "lucide-react";

import { IconButton } from "../ui/IconButton";
import type { SkillProvenance } from "../../types";

type SkillTone = "pass" | "fail" | "info";

function sourceLabel(skill: SkillProvenance): string {
  if (skill.is_confirmed_gap) return "Confirmed gap";
  if (skill.source === "resume_demonstrated") return "Demonstrated";
  if (skill.source === "student_added") return "Self-reported";
  if (skill.source === "student_confirmed") return "Self-reported";
  return "Self-reported";
}

function sourceTone(skill: SkillProvenance): SkillTone {
  if (skill.is_confirmed_gap) return "fail";
  if (skill.source === "resume_demonstrated") return "pass";
  return "info";
}

type SkillsManagerProps = {
  skills: SkillProvenance[];
  newSkillInput: string;
  onNewSkillChange: (value: string) => void;
  onAddSkill: () => void;
  onRemoveSkill: (normalizedName: string) => void;
};

export function SkillsManager({
  skills,
  newSkillInput,
  onNewSkillChange,
  onAddSkill,
  onRemoveSkill,
}: SkillsManagerProps) {
  return (
    <section className="editor-block" aria-labelledby="skills-title">
      <h4 className="editor-block__title" id="skills-title">
        Skills &amp; provenance{" "}
        <span className="editor-block__count mono">({skills.length})</span>
      </h4>
      <p className="editor-block__hint">
        Every skill carries its source. Missing keywords are never treated as missing skills.
      </p>

      {skills.length === 0 ? (
        <p className="muted-note">
          No skills captured yet. Upload a resume, paste text, or add one below.
        </p>
      ) : (
        <ul className="skill-stamps" aria-label="Recognized skills">
          {skills.map((skill) => (
            <li
              key={skill.normalized_name}
              className={`skill-stamp skill-stamp--${sourceTone(skill)}`}
            >
              <span className="skill-stamp__name">{skill.name}</span>
              <span className="skill-stamp__source mono">{sourceLabel(skill)}</span>
              <IconButton
                label={`Remove ${skill.name}`}
                icon={<X size={13} />}
                className="skill-stamp__remove"
                onClick={() => onRemoveSkill(skill.normalized_name)}
              />
            </li>
          ))}
        </ul>
      )}

      <div className="add-skill">
        <label className="sr-only" htmlFor="new-skill">
          Add a skill
        </label>
        <input
          id="new-skill"
          className="input"
          value={newSkillInput}
          onChange={(event) => onNewSkillChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              onAddSkill();
            }
          }}
          placeholder="Add another skill (e.g. Docker, GraphQL)…"
        />
        <button
          type="button"
          className="btn btn--secondary btn--sm"
          onClick={onAddSkill}
          disabled={!newSkillInput.trim()}
        >
          <Plus size={14} aria-hidden="true" />
          <span>Add skill</span>
        </button>
      </div>
    </section>
  );
}
