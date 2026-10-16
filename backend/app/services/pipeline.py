"""The 3-step Gen AI pipeline.

  1. JD extraction   - JD text -> role title, required & nice-to-have skills
  2. Gap analysis    - resume + step-1 output -> score, matched/missing, strengths, summary
  3. Bullet rewrite  - resume + step-1 output -> tailored bullets

Splitting the work into small, focused prompts gives more reliable output than one giant
prompt, and each step is validated independently. Steps 2 and 3 only depend on step 1,
so they run concurrently.
"""

import asyncio

from app import prompts
from app.llm import LLMClient, complete_json
from app.schemas import AnalysisResult, BulletRewrites, GapAnalysis, JDRequirements


async def run_analysis(llm: LLMClient, resume_text: str, jd_text: str) -> AnalysisResult:
    requirements = await complete_json(llm, prompts.jd_extraction_prompt(jd_text), JDRequirements)

    gap, rewrites = await asyncio.gather(
        complete_json(llm, prompts.gap_analysis_prompt(resume_text, requirements), GapAnalysis),
        complete_json(llm, prompts.bullet_rewrite_prompt(resume_text, requirements), BulletRewrites),
    )

    return AnalysisResult(
        role_title=requirements.role_title,
        required_skills=requirements.required_skills,
        nice_to_have_skills=requirements.nice_to_have_skills,
        **gap.model_dump(),
        bullets=rewrites.bullets,
    )
