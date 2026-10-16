import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ScoreRing, scoreBand } from "../ScoreRing";

describe("ScoreRing", () => {
  it("exposes the score as an accessible meter", () => {
    render(<ScoreRing score={82} />);

    const meter = screen.getByRole("meter", { name: "Match score" });
    expect(meter).toHaveAttribute("aria-valuenow", "82");
    expect(meter).toHaveAttribute("aria-valuetext", "82 out of 100, strong match");
    expect(screen.getByText("82")).toBeInTheDocument();
    expect(screen.getByText("Strong match")).toBeInTheDocument();
  });

  it("clamps and rounds out-of-range values", () => {
    const { rerender } = render(<ScoreRing score={142.4} />);
    expect(screen.getByRole("meter")).toHaveAttribute("aria-valuenow", "100");

    rerender(<ScoreRing score={-5} />);
    expect(screen.getByRole("meter")).toHaveAttribute("aria-valuenow", "0");

    rerender(<ScoreRing score={49.6} />);
    expect(screen.getByRole("meter")).toHaveAttribute("aria-valuenow", "50");
  });

  it("draws an arc proportional to the score", () => {
    render(<ScoreRing score={25} size={112} />);

    const arc = screen.getByTestId("score-arc");
    const circumference = Number(arc.getAttribute("stroke-dasharray"));
    const offset = Number(arc.getAttribute("stroke-dashoffset"));
    expect(offset / circumference).toBeCloseTo(0.75);
  });

  it.each([
    [90, "good"],
    [75, "good"],
    [60, "fair"],
    [49, "poor"],
  ] as const)("score %d uses the %s colour band", (score, tone) => {
    expect(scoreBand(score).tone).toBe(tone);
    render(<ScoreRing score={score} />);
    expect(screen.getByRole("meter")).toHaveClass(`score-ring--${tone}`);
  });
});
