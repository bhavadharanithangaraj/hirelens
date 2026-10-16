import type { CSSProperties } from "react";

/** Sets the CSS stagger index (`--i`) used by `.reveal`, `.chip` and other entrance animations. */
export function stagger(index: number): CSSProperties {
  return { "--i": index } as CSSProperties;
}
