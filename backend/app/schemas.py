"""Pydantic models.

Two groups live here:
  * LLM step outputs - the contract each pipeline step's JSON must satisfy.
  * API request/response models - what the HTTP layer accepts and returns.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

MIN_TEXT_LENGTH = 50
MAX_TEXT_LENGTH = 20_000
MAX_BULLETS = 5


def _clean_skill_list(values: list[str]) -> list[str]:
    """Strip blanks and drop case-insensitive duplicates while keeping order."""
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        skill = value.strip()
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            cleaned.append(skill)
    return cleaned


# ---------- LLM step outputs ----------


class JDRequirements(BaseModel):
    """Step 1 output: what the job actually asks for."""

    role_title: str = Field(min_length=1, max_length=200)
    required_skills: list[str]
    nice_to_have_skills: list[str] = []

    clean_skills = field_validator("required_skills", "nice_to_have_skills")(_clean_skill_list)


class GapAnalysis(BaseModel):
    """Step 2 output: how the resume compares with the requirements."""

    match_score: int = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    summary: str = Field(min_length=1)

    clean_skills = field_validator("matched_skills", "missing_skills")(_clean_skill_list)


class BulletRewrite(BaseModel):
    original: str = Field(min_length=1)
    improved: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class BulletRewrites(BaseModel):
    """Step 3 output: resume bullets tailored to the JD."""

    bullets: list[BulletRewrite] = Field(min_length=1)

    @field_validator("bullets")
    @classmethod
    def _cap_bullets(cls, bullets: list[BulletRewrite]) -> list[BulletRewrite]:
        # Models sometimes return a few extra; trimming beats failing the whole request.
        return bullets[:MAX_BULLETS]


# ---------- API models ----------


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    resume_text: str = Field(min_length=MIN_TEXT_LENGTH, max_length=MAX_TEXT_LENGTH)
    jd_text: str = Field(min_length=MIN_TEXT_LENGTH, max_length=MAX_TEXT_LENGTH)


class AnalysisResult(BaseModel):
    """Combined output of the three pipeline steps."""

    role_title: str
    required_skills: list[str]
    nice_to_have_skills: list[str]
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    summary: str
    bullets: list[BulletRewrite]


class AnalysisResponse(AnalysisResult):
    id: int
    created_at: datetime


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role_title: str
    match_score: int
    created_at: datetime


class ExtractTextResponse(BaseModel):
    filename: str
    pages: int
    text: str


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
