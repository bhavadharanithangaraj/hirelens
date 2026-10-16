import { forwardRef } from "react";

import type { Analysis } from "../types";
import { BulletCard } from "./BulletCard";
import { ScoreRing } from "./ScoreRing";
import { SkillChips } from "./SkillChips";
import { stagger } from "./stagger";

/** The heading receives focus when new results arrive, so keyboard and screen-reader users land on them. */
export const Results = forwardRef<HTMLHeadingElement, { analysis: Analysis }>(function Results({ analysis }, headingRef) {
  return (
    <section className="results" aria-labelledby="results-title">
      <div className="card results__hero reveal spotlight" style={stagger(0)}>
        <ScoreRing score={analysis.match_score} />
        <div>
          <p className="eyebrow">Match report</p>
          <h2 id="results-title" ref={headingRef} tabIndex={-1}>
            {analysis.role_title}
          </h2>
          <p className="results__summary">{analysis.summary}</p>
        </div>
      </div>

      <div className="results__grid reveal" style={stagger(1)}>
        <SkillChips title="Matched skills" skills={analysis.matched_skills} variant="matched" emptyText="No matching skills found." />
        <SkillChips title="Missing skills" skills={analysis.missing_skills} variant="missing" emptyText="No required skills missing. Nice!" />
      </div>

      {analysis.strengths.length > 0 && (
        <section className="card reveal spotlight" style={stagger(2)} aria-labelledby="strengths-title">
          <h3 id="strengths-title">Strengths</h3>
          <ul className="strengths">
            {analysis.strengths.map((strength) => (
              <li key={strength}>{strength}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="reveal" style={stagger(3)} aria-labelledby="bullets-title">
        <h3 id="bullets-title" className="section-title">
          Tailored resume bullets
        </h3>
        <div className="bullets">
          {analysis.bullets.map((bullet, index) => (
            <BulletCard key={`${analysis.id}-${index}`} bullet={bullet} index={index} />
          ))}
        </div>
      </section>
    </section>
  );
});
