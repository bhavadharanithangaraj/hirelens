import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => ({
  // GitHub Pages serves the site from /<repo>/, so asset URLs need that prefix.
  base: mode === "pages" ? "/hirelens/" : "/",
  plugins: [react()],
  server: { port: 5173 },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/setupTests.ts"],
    // userEvent typing tests can exceed the 5s default on a cold first run.
    testTimeout: 15_000,
  },
}));
