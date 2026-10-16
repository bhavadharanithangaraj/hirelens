// Mirrors the Pydantic response models in backend/app/schemas.py.

export interface BulletRewrite {
  original: string;
  improved: string;
  reason: string;
}

export interface Analysis {
  id: number;
  created_at: string;
  role_title: string;
  required_skills: string[];
  nice_to_have_skills: string[];
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  strengths: string[];
  summary: string;
  bullets: BulletRewrite[];
}

export interface HistoryItem {
  id: number;
  role_title: string;
  match_score: number;
  created_at: string;
}

export interface ExtractTextResponse {
  filename: string;
  pages: number;
  text: string;
}
