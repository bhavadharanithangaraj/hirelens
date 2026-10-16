interface SkillChipsProps {
  title: string;
  skills: string[];
  variant: "matched" | "missing";
  emptyText: string;
}

export function SkillChips({ title, skills, variant, emptyText }: SkillChipsProps) {
  const headingId = `skills-${variant}`;
  return (
    <section className="card" aria-labelledby={headingId}>
      <h3 id={headingId}>
        {title} <span className="count">{skills.length}</span>
      </h3>
      {skills.length === 0 ? (
        <p className="muted">{emptyText}</p>
      ) : (
        <ul className="chips">
          {skills.map((skill) => (
            <li key={skill} className={`chip chip--${variant}`}>
              <span aria-hidden="true">{variant === "matched" ? "✓" : "✕"}</span> {skill}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
