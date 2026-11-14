import { X } from "lucide-react";

import { IconButton } from "../ui/IconButton";
import { conditionTypeLabel, formatConditionValue } from "../../lib/format";
import type { InternshipDetail } from "../../types";

type ConditionsEditorProps = {
  internship: InternshipDetail;
  onRemoveCondition: (index: number) => void;
};

export function ConditionsEditor({ internship, onRemoveCondition }: ConditionsEditorProps) {
  return (
    <div className="conditions-panel" id={`conditions-${internship.id}`}>
      <div className="conditions-panel__head">
        <h4 className="conditions-panel__title">Extracted formal eligibility conditions</h4>
        <span className="mono conditions-panel__count">
          {String(internship.eligibility_conditions.length).padStart(2, "0")} RULES
        </span>
      </div>

      {internship.eligibility_conditions.length === 0 ? (
        <p className="muted-note">
          No formal academic conditions extracted. Run auto-extract, or revise the description
          so the rule is stated explicitly.
        </p>
      ) : (
        <div className="condition-ledger">
          <div className="condition-ledger__head" aria-hidden="true">
            <span>Type</span>
            <span>Operator</span>
            <span>Value</span>
            <span>Source text</span>
            <span />
          </div>
          {internship.eligibility_conditions.map((condition, index) => (
            <div className="condition-row" key={condition.condition_id || index}>
              <span className="condition-row__type mono">
                {conditionTypeLabel(condition)}
                <span className="condition-row__logic">
                  {condition.is_mandatory ? "mandatory" : "optional"}
                </span>
              </span>
              <span className="condition-row__operator mono">{condition.operator || "—"}</span>
              <span className="condition-row__value mono">
                {formatConditionValue(condition.value)}
              </span>
              <span className="condition-row__quote">
                {condition.original_text ? `“${condition.original_text}”` : "No quoted source"}
              </span>
              <IconButton
                label={`Remove ${conditionTypeLabel(condition)} condition`}
                icon={<X size={14} />}
                onClick={() => onRemoveCondition(index)}
              />
            </div>
          ))}
        </div>
      )}

      <div className="conditions-panel__skills">
        <div>
          <h5 className="conditions-panel__subtitle">Required skills</h5>
          {internship.required_skills.length > 0 ? (
            <ul className="skill-inline-list">
              {internship.required_skills.map((skill, skillIndex) => (
                <li key={`${skill}-${skillIndex}`} className="mono">
                  {skill}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted-note">None extracted.</p>
          )}
        </div>
        <div>
          <h5 className="conditions-panel__subtitle">Preferred skills</h5>
          {internship.preferred_skills.length > 0 ? (
            <ul className="skill-inline-list">
              {internship.preferred_skills.map((skill, skillIndex) => (
                <li key={`${skill}-${skillIndex}`} className="mono">
                  {skill}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted-note">None extracted.</p>
          )}
        </div>
      </div>
    </div>
  );
}
