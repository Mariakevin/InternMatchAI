import { Field } from "../ui/Field";
import type { EducationItem } from "../../types";

type EducationFieldsProps = {
  education: EducationItem[];
  onChange: (index: number, patch: Partial<EducationItem>) => void;
};

export function EducationFields({ education, onChange }: EducationFieldsProps) {
  return (
    <section className="editor-block" aria-labelledby="education-title">
      <h4 className="editor-block__title" id="education-title">
        Academic record
      </h4>
      <p className="editor-block__hint">
        Hard eligibility is evaluated against these facts. Correct anything the parser missed.
      </p>

      {education.map((item, index) => {
        const prefix = `edu-${index}`;
        return (
          <div className="education-item" key={prefix}>
            {education.length > 1 ? (
              <p className="education-item__index mono">RECORD {String(index + 1).padStart(2, "0")}</p>
            ) : null}
            <div className="field-grid field-grid--education">
              <Field htmlFor={`${prefix}-degree`} label="Degree" required>
                <input
                  id={`${prefix}-degree`}
                  className="input"
                  value={item.degree}
                  onChange={(event) => onChange(index, { degree: event.target.value })}
                  placeholder="e.g. B.Tech, BCA, BS, MCA"
                  required
                />
              </Field>

              <Field htmlFor={`${prefix}-discipline`} label="Discipline / branch">
                <input
                  id={`${prefix}-discipline`}
                  className="input"
                  value={item.discipline}
                  onChange={(event) => onChange(index, { discipline: event.target.value })}
                  placeholder="e.g. Computer Science, IT"
                />
              </Field>

              <Field htmlFor={`${prefix}-cgpa`} label="CGPA / percentage">
                <input
                  id={`${prefix}-cgpa`}
                  className="input mono"
                  type="number"
                  inputMode="decimal"
                  step="0.01"
                  min="0"
                  value={item.cgpa ?? ""}
                  onChange={(event) =>
                    onChange(index, {
                      cgpa: event.target.value === "" ? null : Number(event.target.value),
                    })
                  }
                  placeholder="e.g. 8.5"
                />
              </Field>

              <Field htmlFor={`${prefix}-scale`} label="Grading scale">
                <select
                  id={`${prefix}-scale`}
                  className="select mono"
                  value={item.cgpa_scale}
                  onChange={(event) =>
                    onChange(index, { cgpa_scale: Number(event.target.value) })
                  }
                >
                  <option value={4}>4.0 scale</option>
                  <option value={10}>10.0 scale</option>
                  <option value={100}>100% scale</option>
                </select>
              </Field>

              <Field htmlFor={`${prefix}-graduation`} label="Graduation year">
                <input
                  id={`${prefix}-graduation`}
                  className="input mono"
                  value={item.graduation_date ?? ""}
                  onChange={(event) => onChange(index, { graduation_date: event.target.value })}
                  placeholder="e.g. 2025"
                />
              </Field>

              <Field htmlFor={`${prefix}-semester`} label="Current semester">
                <input
                  id={`${prefix}-semester`}
                  className="input mono"
                  type="number"
                  inputMode="numeric"
                  min="1"
                  max="20"
                  value={item.current_semester ?? ""}
                  onChange={(event) =>
                    onChange(index, {
                      current_semester:
                        event.target.value === "" ? null : Number(event.target.value),
                    })
                  }
                  placeholder="e.g. 6"
                />
              </Field>
            </div>
          </div>
        );
      })}
    </section>
  );
}
