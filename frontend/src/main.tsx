import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./index.css";

// Feeds the pointer position to the hovered `.spotlight` card so its CSS glow can follow the cursor.
document.addEventListener("pointermove", (event) => {
  const card = (event.target as Element | null)?.closest?.<HTMLElement>(".spotlight");
  if (!card) return;
  const rect = card.getBoundingClientRect();
  card.style.setProperty("--mx", `${event.clientX - rect.left}px`);
  card.style.setProperty("--my", `${event.clientY - rect.top}px`);
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
