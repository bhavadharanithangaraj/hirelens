import type { Analysis, ExtractTextResponse, HistoryItem } from "./types";

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** FastAPI returns `detail` as a string, or as a list of validation errors for 422s. */
function messageFromDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((err: { msg?: string }) => err.msg ?? "Invalid input").join("; ");
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError("Can't reach the HireLens server. Is the backend running?", 0);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(messageFromDetail(body?.detail, `Request failed (${response.status})`), response.status);
  }
  return response.json() as Promise<T>;
}

export const api = {
  analyze(resumeText: string, jdText: string): Promise<Analysis> {
    return request<Analysis>("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_text: resumeText, jd_text: jdText }),
    });
  },

  extractText(file: File): Promise<ExtractTextResponse> {
    const form = new FormData();
    form.append("file", file);
    return request<ExtractTextResponse>("/api/extract-text", { method: "POST", body: form });
  },

  listHistory(): Promise<HistoryItem[]> {
    return request<HistoryItem[]>("/api/history");
  },

  getAnalysis(id: number): Promise<Analysis> {
    return request<Analysis>(`/api/history/${id}`);
  },
};
