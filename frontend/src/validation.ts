// Keep in sync with MIN_TEXT_LENGTH / MAX_TEXT_LENGTH in backend/app/schemas.py.
export const MIN_TEXT_LENGTH = 50;
export const MAX_TEXT_LENGTH = 20_000;

export interface FormErrors {
  resume?: string;
  jd?: string;
}

function validateField(value: string, label: string): string | undefined {
  const length = value.trim().length;
  if (length === 0) return `${label} is required.`;
  if (length < MIN_TEXT_LENGTH) return `${label} must be at least ${MIN_TEXT_LENGTH} characters (currently ${length}).`;
  if (length > MAX_TEXT_LENGTH) return `${label} must be at most ${MAX_TEXT_LENGTH.toLocaleString()} characters.`;
  return undefined;
}

export function validateInputs(resume: string, jd: string): FormErrors {
  const errors: FormErrors = {};
  const resumeError = validateField(resume, "Resume");
  const jdError = validateField(jd, "Job description");
  if (resumeError) errors.resume = resumeError;
  if (jdError) errors.jd = jdError;
  return errors;
}
