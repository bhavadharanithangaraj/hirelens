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
        <div className="panel field">
          <div className="field__header">
            <label htmlFor="resume-input">Your resume</label>
            <button
              type="button"
              className="btn btn--ghost"
              onClick={() => fileRef.current?.click()}
              disabled={loading || uploadStatus.kind === "busy"}
            >
              Upload PDF
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
          <textarea
            id="resume-input"
            ref={resumeRef}
            value={resume}
            onChange={(e) => setResume(e.target.value)}
            placeholder="Paste your resume here, or upload a PDF…"
            aria-invalid={Boolean(errors.resume)}
            aria-describedby="resume-hint resume-error"
            rows={14}
          />
          <FieldFooter id="resume" length={resume.trim().length} error={errors.resume} />
          <p className={`upload-status upload-status--${uploadStatus.kind}`} role="status" aria-live="polite">
            {uploadStatus.message}
          </p>
        </div>

        <div className="panel field">
          <div className="field__header">
            <label htmlFor="jd-input">Job description</label>
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
        <button type="submit" className="btn btn--primary" disabled={loading}>
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
      <span id={`${id}-hint`} className="field__hint">
        {length} chars{length < MIN_TEXT_LENGTH ? ` · min ${MIN_TEXT_LENGTH}` : ""}
      </span>
    </div>
  );
}
