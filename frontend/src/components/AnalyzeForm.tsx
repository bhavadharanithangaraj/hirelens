import { useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { api } from "../api";
import { MIN_TEXT_LENGTH, validateInputs, type FormErrors } from "../validation";

interface AnalyzeFormProps {
  onSubmit: (resumeText: string, jdText: string) => void;
  loading: boolean;
  /** Injected so tests (or other callers) can replace the PDF upload request. */
  extractPdfText?: (file: File) => Promise<string>;
}

const defaultExtract = async (file: File) => (await api.extractText(file)).text;

export function AnalyzeForm({ onSubmit, loading, extractPdfText = defaultExtract }: AnalyzeFormProps) {
  const [resume, setResume] = useState("");
  const [jd, setJd] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const [uploadStatus, setUploadStatus] = useState<{ kind: "idle" | "busy" | "ok" | "error"; message: string }>({
    kind: "idle",
    message: "",
  });

  const uploading = uploadStatus.kind === "busy";

  const resumeRef = useRef<HTMLTextAreaElement>(null);
  const jdRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validateInputs(resume, jd);
    setErrors(found);
    if (found.resume) return resumeRef.current?.focus();
    if (found.jd) return jdRef.current?.focus();
    onSubmit(resume.trim(), jd.trim());
  }

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow re-selecting the same file
    if (!file) return;

    setUploadStatus({ kind: "busy", message: `Reading ${file.name}…` });
    try {
      const text = await extractPdfText(file);
      setResume(text);
      setErrors((prev) => ({ ...prev, resume: undefined }));
      setUploadStatus({ kind: "ok", message: `Imported text from ${file.name}.` });
    } catch (err) {
      setUploadStatus({ kind: "error", message: err instanceof Error ? err.message : "Could not read that PDF." });
    }
  }

  return (
    <form className="analyze-form" onSubmit={handleSubmit} noValidate aria-label="Resume and job description">
      <div className="panels">
        <div className="panel field spotlight">
          <div className="field__header">
            <div className="field__label">
              <span className="field__icon" aria-hidden="true">
                <DocIcon />
              </span>
              <label htmlFor="resume-input">Your resume</label>
            </div>
            <button
              type="button"
              className="btn btn--ghost"
              onClick={() => fileRef.current?.click()}
              disabled={loading || uploading}
              aria-busy={uploading}
            >
              {uploading ? <span className="btn__spinner btn__spinner--current" aria-hidden="true" /> : <UploadIcon />}
              {uploading ? "Uploading…" : "Upload PDF"}
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf,.pdf"
              className="visually-hidden"
              tabIndex={-1}
              aria-hidden="true"
              onChange={handleFile}
              data-testid="pdf-input"
            />
          </div>
          <div className="textarea-wrap">
            <textarea
              id="resume-input"
              ref={resumeRef}
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              placeholder="Paste your resume here, or upload a PDF…"
              aria-invalid={Boolean(errors.resume)}
              aria-describedby="resume-hint resume-error"
              rows={14}
              readOnly={uploading}
            />
            {uploading && (
              <div className="upload-overlay" aria-hidden="true">
                <span className="loader" />
                <span className="upload-overlay__text">{uploadStatus.message}</span>
                <span className="upload-overlay__sub">Extracting text from your PDF</span>
                <span className="upload-overlay__bar" />
              </div>
            )}
          </div>
          <FieldFooter id="resume" length={resume.trim().length} error={errors.resume} />
          <p className={`upload-status upload-status--${uploadStatus.kind}`} role="status" aria-live="polite">
            {uploadStatus.message}
          </p>
        </div>

        <div className="panel field spotlight">
          <div className="field__header">
            <div className="field__label">
              <span className="field__icon field__icon--cyan" aria-hidden="true">
                <BriefcaseIcon />
              </span>
              <label htmlFor="jd-input">Job description</label>
            </div>
          </div>
          <textarea
            id="jd-input"
            ref={jdRef}
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            placeholder="Paste the job description here…"
            aria-invalid={Boolean(errors.jd)}
            aria-describedby="jd-hint jd-error"
            rows={14}
          />
          <FieldFooter id="jd" length={jd.trim().length} error={errors.jd} />
        </div>
      </div>

      <div className="form-actions">
        <span className="form-actions__note">Takes about 10 seconds</span>
        <button type="submit" className="btn btn--primary" disabled={loading || uploading}>
          {loading ? <span className="btn__spinner" aria-hidden="true" /> : <SparkleIcon />}
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </div>
    </form>
  );
}

function FieldFooter({ id, length, error }: { id: string; length: number; error?: string }) {
  return (
    <div className="field__footer">
      <span id={`${id}-error`} className="field__error">
        {error}
      </span>
      <span id={`${id}-hint`} className={`field__hint${length >= MIN_TEXT_LENGTH ? " field__hint--ok" : ""}`}>
        {length} chars{length < MIN_TEXT_LENGTH ? ` · min ${MIN_TEXT_LENGTH}` : ""}
      </span>
    </div>
  );
}

const iconProps = {
  width: 16,
  height: 16,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
} as const;

function DocIcon() {
  return (
    <svg {...iconProps}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5M9 13h6M9 17h4" />
    </svg>
  );
}

function BriefcaseIcon() {
  return (
    <svg {...iconProps}>
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18" />
    </svg>
  );
}

function UploadIcon() {
  return (
    <svg {...iconProps} width={14} height={14}>
      <path d="M12 16V4M6 10l6-6 6 6M4 20h16" />
    </svg>
  );
}

function SparkleIcon() {
  return (
    <svg {...iconProps} width={18} height={18}>
      <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9zM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z" />
    </svg>
  );
}
