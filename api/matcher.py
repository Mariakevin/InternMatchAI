import re
from dataclasses import dataclass
from typing import Any

from api.models import StudentProfile
from api.orchestrator import orchestrate_matching
from api.resume_parser import parse_resume
from api.internship_parser import parse_internship

SKILLS = (
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "html",
    "css",
    "sql",
    "postgresql",
    "mongodb",
    "fastapi",
    "django",
    "flask",
    "rest api",
    "git",
    "docker",
    "aws",
    "azure",
    "machine learning",
    "data analysis",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "excel",
    "power bi",
    "tableau",
    "figma",
    "ui/ux",
    "communication",
    "project management",
    "research",
    "c++",
    "c#",
    "go",
    "rust",
)

SECTION_HEADINGS = {
    "education": ("education", "academic background"),
    "experience": ("experience", "work experience", "employment"),
    "projects": ("projects", "personal projects", "project experience"),
}
HEADING_PATTERN = re.compile(
    r"(?im)^[ \t]*(education|academic background|experience|work experience|"
    r"employment|projects|personal projects|project experience)[ \t]*:?[ \t]*$"
)


@dataclass(frozen=True)
class Eligibility:
    status: str
    detail: str


def _find_skills(text: str) -> list[str]:
    normalized = text.casefold()
    found = []
    for skill in SKILLS:
        pattern = rf"(?<!\w){re.escape(skill.casefold())}(?!\w)"
        if re.search(pattern, normalized):
            found.append(skill)
    return found


def _extract_sections(text: str) -> dict[str, str]:
    headings = list(HEADING_PATTERN.finditer(text))
    sections: dict[str, str] = {}
    for index, heading in enumerate(headings):
        label = heading.group(1).casefold()
        section_name = next(
            name
            for name, aliases in SECTION_HEADINGS.items()
            if label in aliases
        )
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        content = text[heading.end() : end].strip()
        if content:
            sections[section_name] = content
    return sections


def extract_profile(resume_text: str) -> dict[str, object]:
    skills = _find_skills(resume_text)
    sections = _extract_sections(resume_text)
    return {
        "skills": skills,
        "education": sections.get("education", ""),
        "experience": sections.get("experience", ""),
        "projects": sections.get("projects", ""),
    }


def _check_eligibility(resume_text: str, description: str) -> Eligibility:
    minimum_gpa = re.search(
        r"(?:minimum\s+)?gpa\s*(?:of|:|>=|at least)?\s*([0-4](?:\.\d{1,2})?)",
        description,
        re.IGNORECASE,
    )
    if not minimum_gpa:
        return Eligibility(
            "needs_review",
            "Review the listing's academic, location, and work-authorization requirements.",
        )

    candidate_gpa = re.search(
        r"\bgpa\s*[:=]?\s*([0-4](?:\.\d{1,2})?)",
        resume_text,
        re.IGNORECASE,
    )
    required = float(minimum_gpa.group(1))
    if not candidate_gpa:
        return Eligibility(
            "needs_review",
            f"The listing specifies a {required:.1f} GPA minimum; no GPA was found in the resume.",
        )

    achieved = float(candidate_gpa.group(1))
    if achieved >= required:
        return Eligibility(
            "meets_known_requirements",
            f"Resume GPA {achieved:.2f} meets the listed {required:.1f} minimum. Review other requirements.",
        )
    return Eligibility(
        "does_not_meet_known_requirements",
        f"Resume GPA {achieved:.2f} is below the listed {required:.1f} minimum.",
    )


def rank_internships(
    resume_text: str, internships: list[dict[str, str]]
) -> dict[str, object]:
    legacy_profile = extract_profile(resume_text)
    candidate_skills = set(legacy_profile["skills"])
    results = []

    # Also run advanced orchestrator for structured matching
    profile_model = parse_resume(resume_text)
    internship_models = [
        parse_internship(
            title=internship.get("title", ""),
            description=internship.get("description", ""),
            company=internship.get("company", ""),
            internship_id=str(i),
        )
        for i, internship in enumerate(internships)
    ]
    orchestrated = orchestrate_matching(profile_model, internship_models)
    analysis_by_id = {a.internship_id: a for a in orchestrated.matches}

    for index, internship in enumerate(internships):
        description = internship["description"]
        required_skills = _find_skills(description)
        matched = [skill for skill in required_skills if skill in candidate_skills]
        missing = [skill for skill in required_skills if skill not in candidate_skills]
        score = round(len(matched) / len(required_skills) * 100) if required_skills else 0
        eligibility = _check_eligibility(resume_text, description)

        analysis = analysis_by_id.get(str(index))
        results.append(
            {
                "id": str(index),
                "title": internship["title"],
                "company": internship.get("company", "").strip() or "Company not specified",
                "score": score,
                "matched_skills": matched,
                "missing_skills": missing,
                "eligibility": {
                    "status": eligibility.status,
                    "detail": eligibility.detail,
                },
                "requirements_found": bool(required_skills),
                "structured_analysis": analysis.model_dump() if analysis else None,
            }
        )

    results.sort(key=lambda result: (-int(result["score"]), result["title"].casefold()))
    return {
        "profile": legacy_profile,
        "structured_profile": profile_model.model_dump(),
        "matches": results,
    }
