import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AnalyzeForm } from "../AnalyzeForm";

const LONG_RESUME = "Full-stack developer with 4 years of React, TypeScript and Python FastAPI experience.";
const LONG_JD = "We are hiring a React + Python developer to build Gen AI features with LLM APIs.";

function setup(props: Partial<Parameters<typeof AnalyzeForm>[0]> = {}) {
  const onSubmit = vi.fn();
  const user = userEvent.setup();
  render(<AnalyzeForm onSubmit={onSubmit} loading={false} {...props} />);
  return {
    user,
    onSubmit,
    resume: screen.getByLabelText("Your resume"),
    jd: screen.getByLabelText("Job description"),
    submit: screen.getByRole("button", { name: /^Analyz/ }),
  };
}

describe("AnalyzeForm validation", () => {
  it("shows required errors and focuses the first invalid field when empty", async () => {
    const { user, onSubmit, resume, jd, submit } = setup();

    await user.click(submit);

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText("Resume is required.")).toBeInTheDocument();
    expect(screen.getByText("Job description is required.")).toBeInTheDocument();
    expect(resume).toHaveAttribute("aria-invalid", "true");
    expect(jd).toHaveAttribute("aria-invalid", "true");
    expect(resume).toHaveFocus();
  });

  it("rejects text shorter than the minimum length", async () => {
    const { user, onSubmit, resume, jd, submit } = setup();

    await user.type(resume, LONG_RESUME);
    await user.type(jd, "Too short");
    await user.click(submit);

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/Job description must be at least 50 characters/)).toBeInTheDocument();
    expect(resume).toHaveAttribute("aria-invalid", "false");
    expect(jd).toHaveFocus();
    expect(jd).toHaveAccessibleDescription(/at least 50 characters/);
  });

  it("submits trimmed values when both fields are valid", async () => {
    const { user, onSubmit, resume, jd, submit } = setup();

    await user.type(resume, `  ${LONG_RESUME}  `);
    await user.type(jd, LONG_JD);
    await user.click(submit);

    expect(onSubmit).toHaveBeenCalledWith(LONG_RESUME, LONG_JD);
    expect(screen.queryByText(/required|at least/)).not.toBeInTheDocument();
  });

  it("disables the submit button while loading", () => {
    setup({ loading: true });
    expect(screen.getByRole("button", { name: "Analyzing…" })).toBeDisabled();
  });

  it("fills the resume from an uploaded PDF", async () => {
    const extractPdfText = vi.fn().mockResolvedValue(LONG_RESUME);
    const { user, resume } = setup({ extractPdfText });

    const file = new File(["%PDF-1.4"], "resume.pdf", { type: "application/pdf" });
    await user.upload(screen.getByTestId("pdf-input"), file);

    expect(extractPdfText).toHaveBeenCalledWith(file);
    expect(resume).toHaveValue(LONG_RESUME);
    expect(await screen.findByText("Imported text from resume.pdf.")).toBeInTheDocument();
  });
});
