import { useEffect, useState } from "react";

import type { BulletRewrite } from "../types";

export function BulletCard({ bullet, index }: { bullet: BulletRewrite; index: number }) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");

  useEffect(() => {
    if (copyState === "idle") return;
    const timer = setTimeout(() => setCopyState("idle"), 2000);
    return () => clearTimeout(timer);
  }, [copyState]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(bullet.improved);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
  }

  return (
    <article className="card bullet" aria-label={`Bullet ${index + 1}`}>
      <div className="bullet__compare">
        <div className="bullet__before">
          <h4>Before</h4>
          <p>{bullet.original}</p>
        </div>
        <div className="bullet__after">
          <h4>After</h4>
          <p>{bullet.improved}</p>
        </div>
      </div>
      <div className="bullet__footer">
        <p className="bullet__reason">
          <strong>Why:</strong> {bullet.reason}
        </p>
        <button type="button" className="btn btn--ghost btn--small" onClick={copy} aria-label={`Copy improved bullet ${index + 1}`}>
          {copyState === "copied" ? "Copied!" : copyState === "failed" ? "Copy failed" : "Copy"}
        </button>
        <span className="visually-hidden" role="status" aria-live="polite">
          {copyState === "copied" ? "Improved bullet copied to clipboard" : ""}
        </span>
      </div>
    </article>
  );
}
