import { useEffect, useId, useState, type CSSProperties } from "react";

interface ScoreRingProps {
  score: number;
  size?: number;
}

const STROKE = 12;
const COUNT_UP_MS = 1400;

export function scoreBand(score: number): { label: string; tone: "good" | "fair" | "poor" } {
  if (score >= 75) return { label: "Strong match", tone: "good" };
  if (score >= 50) return { label: "Moderate match", tone: "fair" };
  return { label: "Weak match", tone: "poor" };
}

function prefersMotion() {
  return typeof window.matchMedia === "function" && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Counts up from 0 to `target` with an ease-out curve; returns the target immediately when motion is off. */
function useCountUp(target: number) {
  const [shown, setShown] = useState(() => (prefersMotion() ? 0 : target));

  useEffect(() => {
    if (!prefersMotion()) {
      setShown(target);
      return;
    }
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / COUNT_UP_MS);
      setShown(Math.round(target * (1 - Math.pow(1 - t, 4))));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target]);

  return shown;
}

/** Circular progress ring. The visible arc is an SVG circle with a dash offset proportional to the score. */
export function ScoreRing({ score, size = 148 }: ScoreRingProps) {
  const value = Math.round(Math.min(100, Math.max(0, Number.isFinite(score) ? score : 0)));
  const radius = (size - STROKE) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value / 100);
  const band = scoreBand(value);
  const shown = useCountUp(value);
  const gradientId = `ring-${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;

  return (
    <div
      className={`score-ring score-ring--${band.tone}`}
      role="meter"
      aria-label="Match score"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={value}
      aria-valuetext={`${value} out of 100, ${band.label.toLowerCase()}`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" style={{ stopColor: "var(--ring-color)" }} />
            <stop offset="100%" style={{ stopColor: "var(--cyan)" }} />
          </linearGradient>
        </defs>
        <circle className="score-ring__track" cx={size / 2} cy={size / 2} r={radius} strokeWidth={STROKE} />
        <circle
          className="score-ring__arc"
          data-testid="score-arc"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={`url(#${gradientId})`}
          strokeWidth={STROKE}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ "--circumference": circumference } as CSSProperties}
        />
      </svg>
      <div className="score-ring__center" aria-hidden="true">
        <span className="score-ring__value">{shown}</span>
        <span className="score-ring__label">{band.label}</span>
      </div>
    </div>
  );
}
