interface ScoreRingProps {
  score: number;
  size?: number;
}

const STROKE = 12;

export function scoreBand(score: number): { label: string; tone: "good" | "fair" | "poor" } {
  if (score >= 75) return { label: "Strong match", tone: "good" };
  if (score >= 50) return { label: "Moderate match", tone: "fair" };
  return { label: "Weak match", tone: "poor" };
}

/** Circular progress ring. The visible arc is an SVG circle with a dash offset proportional to the score. */
export function ScoreRing({ score, size = 148 }: ScoreRingProps) {
  const value = Math.round(Math.min(100, Math.max(0, Number.isFinite(score) ? score : 0)));
  const radius = (size - STROKE) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value / 100);
  const band = scoreBand(value);

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
        <circle className="score-ring__track" cx={size / 2} cy={size / 2} r={radius} strokeWidth={STROKE} />
        <circle
          className="score-ring__arc"
          data-testid="score-arc"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={STROKE}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="score-ring__center" aria-hidden="true">
        <span className="score-ring__value">{value}</span>
        <span className="score-ring__label">{band.label}</span>
      </div>
    </div>
  );
}
