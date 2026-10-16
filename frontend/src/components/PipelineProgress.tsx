import { useEffect, useState } from "react";

export const PIPELINE_STEPS = [
  { title: "Extracting job requirements", detail: "Role, required and nice-to-have skills" },
  { title: "Analyzing skill gaps", detail: "Match score, strengths and missing skills" },
  { title: "Tailoring resume bullets", detail: "Rewriting your bullets for this role" },
];

const STEP_INTERVAL_MS = 2500;

/**
 * The backend runs the pipeline in a single request, so progress here is time-based:
 * it advances through the steps and holds on the last one until the response arrives.
 */
export function PipelineProgress() {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrent((step) => Math.min(step + 1, PIPELINE_STEPS.length - 1));
    }, STEP_INTERVAL_MS);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="card progress" aria-labelledby="progress-title" aria-busy="true">
      <h2 id="progress-title">Analyzing your match…</h2>
      <ol className="progress__steps">
        {PIPELINE_STEPS.map((step, index) => {
          const state = index < current ? "done" : index === current ? "active" : "pending";
          return (
            <li key={step.title} className={`progress__step progress__step--${state}`} aria-current={state === "active" ? "step" : undefined}>
              <span className="progress__marker" aria-hidden="true">
                {state === "done" ? "✓" : index + 1}
              </span>
              <span>
                <strong>{step.title}</strong>
                <span className="progress__detail">{step.detail}</span>
              </span>
              <span className="visually-hidden">
                {state === "done" ? "(complete)" : state === "active" ? "(in progress)" : "(pending)"}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="visually-hidden" role="status" aria-live="polite">
        Step {current + 1} of {PIPELINE_STEPS.length}: {PIPELINE_STEPS[current].title}
      </p>
    </section>
  );
}
