"""Offline stand-in for the real LLM.

It reads the same prompts the real model gets (Task ID + tagged sections) and answers
with deterministic, keyword-based JSON. This lets the whole app - and the test suite -
run without an API key or network access.
"""

import json
import re

from app.prompts import TASK_BULLET_REWRITE, TASK_GAP_ANALYSIS, TASK_JD_EXTRACTION

# Canonical skill name -> extra aliases to look for (the canonical name is always searched).
SKILL_VOCABULARY: dict[str, list[str]] = {
    "Python": [],
    "JavaScript": ["JS", "ES6"],
    "TypeScript": ["TS"],
    "React": ["React.js", "ReactJS"],
    "Next.js": ["NextJS"],
    "Node.js": ["NodeJS", "Node"],
    "HTML": ["HTML5"],
    "CSS": ["CSS3"],
    "FastAPI": [],
    "Django": [],
    "Flask": [],
    "REST APIs": ["REST", "RESTful"],
    "GraphQL": [],
    "SQL": [],
    "PostgreSQL": ["Postgres"],
    "MySQL": [],
    "MongoDB": ["Mongo"],
    "Redis": [],
    "SQLAlchemy": [],
    "Docker": [],
    "Kubernetes": ["K8s"],
    "AWS": ["Amazon Web Services"],
    "GCP": ["Google Cloud"],
    "Azure": [],
    "CI/CD": ["GitHub Actions", "Jenkins"],
    "Git": ["GitHub", "GitLab"],
    "Testing": ["pytest", "Jest", "Vitest", "unit tests", "unit testing"],
    "Generative AI": ["Gen AI", "GenAI"],
    "LLMs": ["LLM", "large language models", "GPT", "Gemini", "OpenAI", "Claude"],
    "Prompt Engineering": ["prompt design", "prompting"],
    "RAG": ["retrieval-augmented generation", "retrieval augmented generation"],
    "LangChain": [],
    "Vector Databases": ["vector database", "vector DB", "Pinecone", "pgvector", "FAISS", "Chroma"],
    "Machine Learning": ["ML"],
    "Pandas": [],
    "Agile": ["Scrum"],
    "Microservices": [],
    "Tailwind CSS": ["Tailwind"],
    "Redux": [],
}

_NICE_TO_HAVE_MARKERS = re.compile(r"nice[- ]to[- ]have|bonus|preferred|a plus|plus:|optional", re.IGNORECASE)
_ROLE_PATTERN = re.compile(
    r"\b((?:senior|junior|lead|staff|principal|mid[- ]level)?\s*"
    r"(?:[A-Z][\w.+#/-]*\s+){0,3}(?:developer|engineer|architect|scientist|analyst))\b",
    re.IGNORECASE,
)
_BULLET_PREFIX = re.compile(r"^\s*(?:[-*•▪‣]|\d+[.)])\s+")
_ACTION_VERBS = ("Built", "Delivered", "Engineered", "Led", "Designed", "Shipped")


def _section(prompt: str, tag: str) -> str:
    # Tags are anchored to line starts so mentions of them inside instructions don't match.
    match = re.search(rf"^<{tag}>\n(.*?)\n</{tag}>$", prompt, re.DOTALL | re.MULTILINE)
    return match.group(1) if match else ""


def _mentions(text: str, skill: str) -> bool:
    for term in (skill, *SKILL_VOCABULARY.get(skill, [])):
        # Custom boundaries so names like "C++", "Node.js" and "CI/CD" still match.
        if re.search(rf"(?<![\w]){re.escape(term)}(?![\w])", text, re.IGNORECASE):
            return True
    return False


def _role_title(jd: str) -> str:
    # JDs usually open with the title, so prefer a short first line that names a role.
    first_line = next((line.strip() for line in jd.splitlines() if line.strip()), "")
    if len(first_line) <= 80 and _ROLE_PATTERN.search(first_line):
        return first_line
    role = _ROLE_PATTERN.search(jd)
    return " ".join(role.group(1).split()).title() if role else "Software Developer"


def _improve_bullet(original: str, verb: str, skills: list[str], role_title: str) -> tuple[str, str]:
    body = original.rstrip(". ")
    first_word = body.split(" ", 1)[0]
    if not first_word.endswith("ed") and first_word not in {"Led", "Built", "Ran", "Drove", "Wrote", "Grew"}:
        body = f"{verb} {body[0].lower()}{body[1:]}"  # add an action verb only if one is missing
    if skills:
        return (
            f"{body}, showcasing {' and '.join(skills)} skills central to the {role_title} role.",
            f"Keeps the original achievement and foregrounds {' and '.join(skills)}, which the JD asks for.",
        )
    return (
        f"{body}, delivering measurable impact for the team.",
        "Leads with an action verb and frames the work around outcomes rather than tasks.",
    )


class MockClient:
    async def generate(self, prompt: str) -> str:
        task = re.search(r"Task ID:\s*(\w+)", prompt)
        task_id = task.group(1) if task else ""

        if task_id == TASK_JD_EXTRACTION:
            result = self._extract_requirements(_section(prompt, "job_description"))
        elif task_id == TASK_GAP_ANALYSIS:
            result = self._gap_analysis(_section(prompt, "resume"), json.loads(_section(prompt, "requirements")))
        elif task_id == TASK_BULLET_REWRITE:
            result = self._rewrite_bullets(_section(prompt, "resume"), json.loads(_section(prompt, "requirements")))
        else:
            result = {"error": "unknown task"}
        return json.dumps(result)

    # ----- Step 1 -----

    def _extract_requirements(self, jd: str) -> dict:
        role_title = _role_title(jd)
        required: list[str] = []
        nice: list[str] = []
        in_nice_section = False

        for line in jd.splitlines():
            if _NICE_TO_HAVE_MARKERS.search(line):
                in_nice_section = True
            elif line.strip().endswith(":") and not _NICE_TO_HAVE_MARKERS.search(line):
                in_nice_section = False  # a new heading like "Requirements:" ends the nice-to-have block
            for skill in SKILL_VOCABULARY:
                if skill in required or skill in nice or not _mentions(line, skill):
                    continue
                (nice if in_nice_section else required).append(skill)

        return {"role_title": role_title, "required_skills": required, "nice_to_have_skills": nice}

    # ----- Step 2 -----

    def _gap_analysis(self, resume: str, req: dict) -> dict:
        required, nice = req["required_skills"], req["nice_to_have_skills"]
        matched_required = [s for s in required if _mentions(resume, s)]
        matched_nice = [s for s in nice if _mentions(resume, s)]
        missing = [s for s in required if s not in matched_required]

        required_ratio = len(matched_required) / len(required) if required else 1.0
        nice_ratio = len(matched_nice) / len(nice) if nice else 0.0
        score = round(100 * (0.85 * required_ratio + 0.15 * nice_ratio))

        strengths = [f"Hands-on experience with {s}, which the role explicitly asks for." for s in matched_required[:3]]
        if not strengths:
            strengths = ["Transferable engineering experience that could be reframed for this role."]

        summary = (
            f"The candidate covers {len(matched_required)} of {len(required)} required skills for the "
            f"{req['role_title']} role."
        )
        summary += f" Key gaps: {', '.join(missing[:3])}." if missing else " No major skill gaps were found."

        return {
            "match_score": max(0, min(100, score)),
            "matched_skills": matched_required + matched_nice,
            "missing_skills": missing,
            "strengths": strengths,
            "summary": summary,
        }

    # ----- Step 3 -----

    def _rewrite_bullets(self, resume: str, req: dict) -> dict:
        lines = [line.strip() for line in resume.splitlines() if line.strip()]
        bullets = [_BULLET_PREFIX.sub("", line) for line in lines if _BULLET_PREFIX.match(line)]
        if len(bullets) < 3:
            # No bullet formatting - fall back to the longest sentences.
            sentences = re.split(r"(?<=[.!?])\s+", " ".join(lines))
            bullets = sorted((s for s in sentences if len(s) > 30), key=len, reverse=True)

        skills = req["required_skills"] + req["nice_to_have_skills"]
        rewrites = []
        for i, original in enumerate(bullets[:5]):
            relevant = [s for s in skills if _mentions(original, s)][:2]
            verb = _ACTION_VERBS[i % len(_ACTION_VERBS)]
            improved, reason = _improve_bullet(original, verb, relevant, req["role_title"])
            rewrites.append({"original": original, "improved": improved, "reason": reason})

        if not rewrites:
            rewrites.append(
                {
                    "original": lines[0] if lines else "Experience summary",
                    "improved": "Add 3-5 bullet points describing concrete achievements with measurable results.",
                    "reason": "The resume has no bullet points to tailor.",
                }
            )
        return {"bullets": rewrites}
