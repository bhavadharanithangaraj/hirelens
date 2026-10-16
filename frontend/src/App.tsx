import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "./api";
import { AnalyzeForm } from "./components/AnalyzeForm";
import { HistorySidebar } from "./components/HistorySidebar";
import { PipelineProgress } from "./components/PipelineProgress";
import { Results } from "./components/Results";
import type { Analysis, HistoryItem } from "./types";

export default function App() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const resultsHeadingRef = useRef<HTMLHeadingElement>(null);
  // Each request gets an id; responses from superseded requests are ignored.
  const latestRequest = useRef(0);

  const refreshHistory = useCallback(async () => {
    try {
      setHistory(await api.listHistory());
      setHistoryError(null);
    } catch (err) {
      setHistoryError(err instanceof Error ? err.message : "Could not load history.");
    }
  }, []);

  useEffect(() => {
    void refreshHistory();
  }, [refreshHistory]);

  useEffect(() => {
    if (analysis) resultsHeadingRef.current?.focus();
  }, [analysis]);

  async function run<T>(task: () => Promise<T>, onSuccess: (value: T) => void) {
    const requestId = ++latestRequest.current;
    setError(null);
    try {
      const value = await task();
      if (requestId === latestRequest.current) onSuccess(value);
    } catch (err) {
      if (requestId === latestRequest.current) setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      if (requestId === latestRequest.current) setLoading(false);
    }
  }

  function handleAnalyze(resumeText: string, jdText: string) {
    setLoading(true);
    setAnalysis(null);
    void run(
      () => api.analyze(resumeText, jdText),
      (result) => {
        setAnalysis(result);
        void refreshHistory();
      },
    );
  }

  function handleSelectHistory(id: number) {
    setLoading(false);
    void run(() => api.getAnalysis(id), setAnalysis);
  }

  return (
    <div className="app">
      <div className="backdrop" aria-hidden="true">
        <div className="backdrop__grid" />
        <div className="backdrop__orb backdrop__orb--1" />
        <div className="backdrop__orb backdrop__orb--2" />
        <div className="backdrop__orb backdrop__orb--3" />
      </div>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className="app-header">
        <div className="brand">
          <span className="brand__logo" aria-hidden="true" />
          <span className="brand__name">HireLens</span>
        </div>
        <p className="brand__tagline">
          <span className="status-dot" aria-hidden="true" />
          AI resume &amp; job-match assistant
        </p>
      </header>

      <div className="layout">
        <HistorySidebar items={history} activeId={analysis?.id ?? null} error={historyError} onSelect={handleSelectHistory} />

        <main id="main" className="content">
          <section className="hero" aria-labelledby="hero-title">
            <span className="hero__badge">✦ Powered by Gen AI</span>
            <h1 id="hero-title" className="hero__title">
              See how well you <span className="gradient-text">match the role</span>
            </h1>
            <p className="hero__subtitle">
              Paste your resume and a job description. HireLens scores the fit, finds your skill gaps and rewrites your bullets for
              the role.
            </p>
          </section>

          <AnalyzeForm onSubmit={handleAnalyze} loading={loading} />

          {error && (
            <div className="alert" role="alert">
              <strong>Analysis failed.</strong> {error}
              <button type="button" className="alert__close" onClick={() => setError(null)} aria-label="Dismiss error">
                ×
              </button>
            </div>
          )}

          {loading && <PipelineProgress />}
          {!loading && analysis && <Results ref={resultsHeadingRef} analysis={analysis} />}
        </main>
      </div>
    </div>
  );
}
