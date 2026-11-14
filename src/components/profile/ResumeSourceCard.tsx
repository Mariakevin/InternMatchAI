import { useState } from "react";
import { FileText, Upload } from "lucide-react";

import { Alert } from "../ui/Alert";
import { Field } from "../ui/Field";
import { ProgressBar } from "../ui/ProgressBar";
import { Spinner } from "../ui/Spinner";
import { formatFileSize } from "../../lib/format";

type ResumeSourceCardProps = {
  resumeText: string;
  fileName: string;
  fileSize: number | null;
  resumeBusy: boolean;
  parsingText: boolean;
  resumeError: string;
  parseNotice: string;
  onUpload: (file: File) => void;
  onTextChange: (text: string) => void;
};

export function ResumeSourceCard({
  resumeText,
  fileName,
  fileSize,
  resumeBusy,
  parsingText,
  resumeError,
  parseNotice,
  onUpload,
  onTextChange,
}: ResumeSourceCardProps) {
  const [dragActive, setDragActive] = useState(false);

  return (
    <section className="card resume-card" aria-labelledby="resume-card-title">
      <div className="card__head">
        <span className="card__icon" aria-hidden="true">
          <FileText size={18} />
        </span>
        <div>
          <h3 className="card__title" id="resume-card-title">
            Your resume source
          </h3>
          <p className="card__subtitle">
            Upload a PDF, DOCX, or TXT file (up to 5 MB) or paste plain text.
          </p>
        </div>
      </div>

      <label
        className={`upload-zone${dragActive ? " is-dragging" : ""}${
          resumeBusy ? " is-busy" : ""
        }`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragActive(false);
          const file = event.dataTransfer.files?.[0];
          if (file) onUpload(file);
        }}
      >
        <input
          className="sr-only"
          type="file"
          accept=".txt,.pdf,.docx"
          aria-describedby="resume-file-help"
          disabled={resumeBusy}
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (file) onUpload(file);
          }}
        />
        <span className="upload-zone__icon" aria-hidden="true">
          {resumeBusy ? <Spinner size={19} /> : <Upload size={19} />}
        </span>
        <span className="upload-zone__copy">
          <strong className="upload-zone__name">
            {resumeBusy
              ? "Extracting text and profile…"
              : fileName || "Click to browse or drop a resume file"}
          </strong>
          <span className="upload-zone__help" id="resume-file-help">
            {fileName && !resumeBusy ? (
              <>
                <span className="mono">{fileName}</span>
                {fileSize !== null ? (
                  <span className="mono upload-zone__size"> · {formatFileSize(fileSize)}</span>
                ) : null}
                <span> · replace by choosing another file</span>
              </>
            ) : (
              <span>PDF, DOCX, or UTF-8 TXT · 5 MB maximum</span>
            )}
          </span>
          {resumeBusy ? (
            <ProgressBar
              value={null}
              indeterminate
              label="Extracting resume"
              tone="accent"
            />
          ) : null}
        </span>
        <span className="upload-zone__action" aria-hidden="true">
          {fileName ? "Replace file" : "Browse file"}
        </span>
      </label>

      {resumeError ? (
        <Alert tone="fail" title="Resume could not be processed" className="resume-alert">
          {resumeError}
        </Alert>
      ) : null}

      <div className="or-divider" aria-hidden="true">
        <span />
        <em>OR PASTE RESUME TEXT</em>
        <span />
      </div>

      <Field
        htmlFor="resume-text"
        label="Paste resume text"
        action={
          parsingText ? (
            <span className="field__inline-status mono">
              <Spinner size={12} /> PARSING
            </span>
          ) : parseNotice ? (
            <span className="field__inline-status field__inline-status--ok mono">
              {parseNotice}
            </span>
          ) : null
        }
        help="Parsed automatically about half a second after you stop typing. Your preference choices are preserved."
      >
        <textarea
          id="resume-text"
          className="textarea resume-textarea"
          value={resumeText}
          onChange={(event) => onTextChange(event.target.value)}
          placeholder="Paste education, degree, CGPA, graduation year, skills, projects, and work experience…"
          rows={5}
          maxLength={60000}
          aria-describedby="resume-text-help"
        />
      </Field>
    </section>
  );
}
