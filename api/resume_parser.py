import re
from io import BytesIO
from pathlib import Path
from typing import Optional
from zipfile import BadZipFile, LargeZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from fastapi import HTTPException
from pypdf import PdfReader
from pypdf.errors import PdfReadError

try:
    from lxml.etree import XMLSyntaxError as _XmlSyntaxError
except Exception:  # pragma: no cover
    _XmlSyntaxError = None

from api.models import (
    EducationItem,
    ExperienceItem,
    ProjectItem,
    SkillProvenance,
    StudentProfile,
    StudentPreferences,
)
from api.taxonomy import (
    SKILL_ALIASES,
    get_degree_level,
)

MAX_RESUME_SIZE = 5 * 1024 * 1024
MAX_TEXT_LENGTH = 60_000
MAX_PDF_PAGES = 100
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}

SECTION_HEADINGS = {
    "education": (
        "education",
        "academic background",
        "academics",
        "qualifications",
        "academic qualifications",
    ),
    "experience": (
        "experience",
        "work experience",
        "employment",
        "internships",
        "professional experience",
    ),
    "projects": (
        "projects",
        "personal projects",
        "academic projects",
        "key projects",
        "project work",
    ),
    "skills": (
        "skills",
        "technical skills",
        "core competencies",
        "skills & abilities",
        "technologies",
        "tools",
    ),
    "certifications": ("certifications", "certificates", "licenses & certifications"),
    "coursework": ("coursework", "relevant coursework", "courses"),
}

HEADING_PATTERN = re.compile(
    r"(?im)^[ \t]*(education|academic background|academics|qualifications|academic qualifications|"
    r"experience|work experience|employment|internships|professional experience|"
    r"projects|personal projects|academic projects|key projects|project work|"
    r"skills|technical skills|core competencies|skills & abilities|technologies|tools|"
    r"certifications|certificates|licenses & certifications|"
    r"coursework|relevant coursework|courses)[ \t]*:?[ \t]*$"
)

# Prompt-injection attempts are treated as ordinary untrusted text; no filtering is
# applied here so that the extraction result stays faithful to the document.

# A percentage is only academic when labelled or followed by marks/aggregate.
ACADEMIC_PERCENTAGE_PATTERN = re.compile(
    r"(?i)(?:(?:cgpa|gpa|marks|aggregate|percentage|score)\s*[:=]?\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s*%|([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:marks|aggregate))"
)
NON_ACADEMIC_PERCENTAGE_CONTEXT = re.compile(
    r"(?i)\b(?:remote|online|placement|guarantee|guaranteed|paid|free)\b"
)


def extract_file_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.casefold()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported format '{Path(filename).suffix}'. Upload a .txt, .pdf, or .docx resume.",
        )
    if len(content) > MAX_RESUME_SIZE:
        raise HTTPException(status_code=413, detail="Resume must be 5 MB or smaller.")

    text = ""
    if extension == ".txt":
        try:
            text = content.decode("utf-8-sig").strip()
        except UnicodeDecodeError as error:
            raise HTTPException(
                status_code=400,
                detail="Text file must use UTF-8 encoding.",
            ) from error
    elif extension == ".pdf":
        try:
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not read this PDF file. It may be corrupt or encrypted.",
                    )
            if len(reader.pages) > MAX_PDF_PAGES:
                raise HTTPException(
                    status_code=422,
                    detail=f"PDF has more than {MAX_PDF_PAGES} pages. Please upload a shorter document.",
                )
            pages_text = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pages_text.append(extracted)
                    if sum(len(p) for p in pages_text) > MAX_TEXT_LENGTH:
                        raise HTTPException(
                            status_code=422,
                            detail=(
                                f"Resume text exceeds {MAX_TEXT_LENGTH:,} characters. "
                                "Please upload a shorter resume or paste only the relevant sections."
                            ),
                        )
            text = "\n".join(pages_text).strip()
        except HTTPException:
            raise
        except (PdfReadError, ValueError, TypeError, OSError) as error:
            raise HTTPException(
                status_code=400,
                detail="Could not read this PDF file. It may be corrupt or encrypted.",
            ) from error
    elif extension == ".docx":
        try:
            document = Document(BytesIO(content))
            paragraphs = []
            for paragraph in document.paragraphs:
                if paragraph.text:
                    paragraphs.append(paragraph.text)
                    if sum(len(p) for p in paragraphs) > MAX_TEXT_LENGTH:
                        raise HTTPException(
                            status_code=422,
                            detail=(
                                f"Resume text exceeds {MAX_TEXT_LENGTH:,} characters. "
                                "Please upload a shorter resume or paste only the relevant sections."
                            ),
                        )
            text = "\n".join(paragraphs).strip()
        except (
            BadZipFile,
            LargeZipFile,
            KeyError,
            ValueError,
            PackageNotFoundError,
        ) as error:
            raise HTTPException(
                status_code=400,
                detail="Could not read this DOCX file. It may be corrupt.",
            ) from error
        except Exception as error:
            if _XmlSyntaxError is not None and isinstance(error, _XmlSyntaxError):
                raise HTTPException(
                    status_code=400,
                    detail="Could not read this DOCX file. It may be corrupt.",
                ) from error
            raise

    if not text or not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found in document. If this is a scanned image, please paste text directly.",
        )

    return text.strip()


def extract_sections(text: str) -> dict[str, str]:
    headings = list(HEADING_PATTERN.finditer(text))
    sections: dict[str, str] = {}
    if not headings:
        # If no explicit headings, search for implicit blocks
        return {"general": text}

    # Content before first heading
    preamble = text[: headings[0].start()].strip()
    if preamble:
        sections["preamble"] = preamble

    for index, heading in enumerate(headings):
        label = heading.group(1).casefold()
        section_name = "general"
        for s_name, aliases in SECTION_HEADINGS.items():
            if label in aliases:
                section_name = s_name
                break
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        content = text[heading.end() : end].strip()
        if content:
            if section_name in sections:
                sections[section_name] += "\n" + content
            else:
                sections[section_name] = content

    return sections


def parse_education_details(text: str, edu_section: str) -> list[EducationItem]:
    combined = (edu_section + "\n" + text).strip()
    items: list[EducationItem] = []

    # Regex patterns for degree
    degrees = [
        (
            "B.Tech",
            r"\b(?:B\.?Tech|B\.?E\.?|Bachelor of Technology|Bachelor of Engineering)\b",
        ),
        ("BCA", r"\b(?:BCA|Bachelor of Computer Applications)\b"),
        ("B.Sc", r"\b(?:B\.?Sc|B\.?S\.?|Bachelor of Science)\b"),
        (
            "M.Tech",
            r"\b(?:M\.?Tech|M\.?E\.?|Master of Technology|Master of Engineering)\b",
        ),
        ("MCA", r"\b(?:MCA|Master of Computer Applications)\b"),
        ("M.Sc", r"\b(?:M\.?Sc|M\.?S\.?|Master of Science)\b"),
        ("MBA", r"\b(?:MBA|Master of Business Administration)\b"),
        ("PhD", r"\b(?:Ph\.?D|Doctorate)\b"),
        ("Diploma", r"\b(?:Diploma)\b"),
    ]

    found_degree = ""
    for canonical, pattern in degrees:
        if re.search(pattern, combined, re.IGNORECASE):
            found_degree = canonical
            break

    # Discipline
    disciplines = [
        ("Computer Science", r"\b(?:Computer Science(?: and Engineering)?|CS|CSE)\b"),
        ("Information Technology", r"(?i)\bInformation Technology\b|\bIT\b"),
        ("Data Science", r"\b(?:Data Science|AI/ML|Artificial Intelligence)\b"),
        (
            "Electronics and Communication",
            r"\b(?:Electronics(?: and Communication)?|ECE)\b",
        ),
        ("Electrical Engineering", r"\b(?:Electrical(?: Engineering)?|EEE)\b"),
        ("Mechanical Engineering", r"\b(?:Mechanical(?: Engineering)?)\b"),
        ("Civil Engineering", r"\b(?:Civil(?: Engineering)?)\b"),
    ]
    found_discipline = ""
    for canonical, pattern in disciplines:
        if canonical == "Information Technology":
            matched = bool(
                re.search(r"(?i)\bInformation Technology\b", combined)
                or re.search(r"\bIT\b", combined)
            )
        else:
            matched = bool(re.search(pattern, combined, re.IGNORECASE))
        if matched:
            found_discipline = canonical
            break

    # CGPA / Marks
    # Look for patterns like "CGPA: 8.5/10", "GPA: 3.8", "85%", etc.
    cgpa_val: Optional[float] = None
    cgpa_scale: float = 4.0
    cgpa_match = re.search(
        r"\b(?:cgpa|gpa|marks|aggregate)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:/\s*([0-9]+(?:\.[0-9]+)?))?",
        combined,
        re.IGNORECASE,
    )
    if cgpa_match:
        val = float(cgpa_match.group(1))
        scale_grp = cgpa_match.group(2)
        if scale_grp:
            scale = float(scale_grp)
            cgpa_val = val
            cgpa_scale = scale
        else:
            if val <= 4.0:
                cgpa_val = val
                cgpa_scale = 4.0
            elif val <= 10.0:
                cgpa_val = val
                cgpa_scale = 10.0
            else:
                cgpa_val = val
                cgpa_scale = 100.0
    else:
        # Check percentage only in an academic context so "100% remote" is not a CGPA.
        pct_match = ACADEMIC_PERCENTAGE_PATTERN.search(combined)
        if pct_match:
            window = combined[max(0, pct_match.start() - 25) : pct_match.end() + 25]
            if not NON_ACADEMIC_PERCENTAGE_CONTEXT.search(window):
                cgpa_val = float(pct_match.group(1) or pct_match.group(2))
                cgpa_scale = 100.0
    # Restore support for a bare percentage adjacent to a degree, e.g. "B.Tech (85%)".
    if cgpa_val is None and found_degree:
        bare = re.search(r"\b([0-9]{2,3}(?:\.[0-9]+)?)\s*%", combined)
        if bare:
            window = combined[max(0, bare.start() - 25) : bare.end() + 25]
            if not NON_ACADEMIC_PERCENTAGE_CONTEXT.search(window):
                cgpa_val = float(bare.group(1))
                cgpa_scale = 100.0

    # Semester / Year
    sem_match = re.search(
        r"\b(?:semester|sem)\s*[:=]?\s*([1-8])\b", combined, re.IGNORECASE
    )
    cur_semester = int(sem_match.group(1)) if sem_match else None

    year_match = re.search(
        r"\b(?:year|yr)\s*[:=]?\s*([1-4])(?:st|nd|rd|th)?\s*(?:year)?\b",
        combined,
        re.IGNORECASE,
    )
    cur_year = int(year_match.group(1)) if year_match else None
    if cur_semester and not cur_year:
        cur_year = (cur_semester + 1) // 2

    # Graduation date
    grad_match = re.search(
        r"\b(?:graduating|graduation|passing out|batch of|expected)\s*(?:in|by|:)?\s*(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*)?(20[2-3][0-9])\b",
        combined,
        re.IGNORECASE,
    )
    grad_date = grad_match.group(1) if grad_match else None

    # Check enrolment status. Never claim "graduated" from a bare word such as
    # "completed a course"; require graduation context. Positive enrolment
    # evidence (semester/year/expected graduation) always wins.
    enrolment = ""
    positive_enrolment = bool(cur_year or cur_semester or grad_date)
    graduated_context = bool(
        re.search(r"\bgraduated\b", combined, re.IGNORECASE)
        or re.search(
            r"\b(?:degree completed|completed (?:my|the) (?:degree|bachelor(?:'s)?|master(?:'s)?)|alumnus|alumni)\b",
            combined,
            re.IGNORECASE,
        )
    )
    if graduated_context and not positive_enrolment:
        enrolment = "graduated"
    elif positive_enrolment:
        enrolment = "enrolled"

    if found_degree or found_discipline or cgpa_val is not None:
        items.append(
            EducationItem(
                level=get_degree_level(found_degree)
                if found_degree
                else "undergraduate",
                degree=found_degree,
                discipline=found_discipline,
                institution="",
                current_year=cur_year,
                current_semester=cur_semester,
                enrolment_status=enrolment,
                graduation_date=grad_date,
                cgpa=cgpa_val,
                cgpa_scale=cgpa_scale,
            )
        )

    return items


_AMBIGUOUS_RESUME_ALIASES = {
    "go",
    "express",
    "react",
    "node",
    "ts",
    "ml",
    "py",
    "js",
    "r",
}
_VERB_FOLLOWERS = {
    "through",
    "to",
    "on",
    "ahead",
    "for",
    "into",
    "over",
    "out",
    "up",
    "down",
    "back",
    "away",
    "along",
    "around",
    "by",
    "with",
    "from",
    "at",
    "in",
    "of",
    "off",
    "about",
    "across",
    "after",
    "against",
    "among",
    "before",
    "behind",
    "below",
    "beneath",
    "beside",
    "between",
    "beyond",
    "during",
    "except",
    "inside",
    "near",
    "onto",
    "outside",
    "past",
    "since",
    "toward",
    "under",
    "until",
    "upon",
    "within",
    "without",
}


def extract_skills_with_evidence(
    text: str, sections: dict[str, str]
) -> list[SkillProvenance]:
    provenances: dict[str, SkillProvenance] = {}
    normalized_full = text.casefold()

    project_text = sections.get("projects", "")
    exp_text = sections.get("experience", "")
    skills_text = sections.get("skills", "")
    coursework_text = sections.get("coursework", "")

    def first_excerpt(pattern: str, block: str) -> str:
        for line in block.splitlines():
            if re.search(pattern, line.casefold()):
                return line.strip()
        return ""

    # Look through vocabulary
    for alias, canonical in SKILL_ALIASES.items():
        # Match word boundary against casefolded text
        alias_norm = alias.casefold()
        pattern = rf"(?<!\w){re.escape(alias_norm)}(?!\w)"
        if not re.search(pattern, normalized_full):
            continue

        # Ambiguous aliases that are also English words are only kept when they
        # appear in a skill-like context (not as a verb, e.g. "go through").
        if alias_norm in _AMBIGUOUS_RESUME_ALIASES:
            occurrences = list(re.finditer(pattern, normalized_full))
            if not any(
                (normalized_full[occ.end() :].lstrip()[:12].split() or [""])[0]
                not in _VERB_FOLLOWERS
                for occ in occurrences
            ):
                continue

        if canonical in provenances:
            continue

        # Determine evidence source & excerpt
        evidence_refs: list[str] = []
        is_demonstrated = False
        excerpt = ""

        # Check projects
        if project_text and re.search(pattern, project_text.casefold()):
            is_demonstrated = True
            evidence_refs.append("projects")
            excerpt = first_excerpt(pattern, project_text)

        # Check experience
        if exp_text and re.search(pattern, exp_text.casefold()):
            is_demonstrated = True
            evidence_refs.append("experience")
            if not excerpt:
                excerpt = first_excerpt(pattern, exp_text)

        # Check coursework
        if coursework_text and re.search(pattern, coursework_text.casefold()):
            evidence_refs.append("coursework")
            if not excerpt:
                excerpt = first_excerpt(pattern, coursework_text)

        # Check skills section
        if skills_text and re.search(pattern, skills_text.casefold()):
            evidence_refs.append("skills_section")

        if not evidence_refs:
            evidence_refs.append("general_text")

        provenances[canonical] = SkillProvenance(
            name=canonical.capitalize(),
            normalized_name=canonical,
            source="resume_demonstrated" if is_demonstrated else "resume_self_reported",
            evidence_refs=evidence_refs,
            student_confirmed=False,
            is_confirmed_gap=False,
            confidence=1.0 if is_demonstrated else 0.8,
        )

    return list(provenances.values())


def extract_projects(projects_text: str) -> list[ProjectItem]:
    if not projects_text:
        return []
    lines = [line.strip() for line in projects_text.splitlines() if line.strip()]
    items: list[ProjectItem] = []
    current_title = ""
    current_desc: list[str] = []

    for line in lines:
        if line.startswith(("-", "*", "•")):
            current_desc.append(line.lstrip("-*• "))
        elif len(line) < 60 and not line.endswith("."):
            if current_title:
                items.append(
                    ProjectItem(title=current_title, description=" ".join(current_desc))
                )
            current_title = line
            current_desc = []
        else:
            current_desc.append(line)

    if current_title:
        items.append(
            ProjectItem(title=current_title, description=" ".join(current_desc))
        )
    elif lines:
        items.append(ProjectItem(title="Projects Summary", description=" ".join(lines)))

    return items


def extract_experiences(exp_text: str) -> list[ExperienceItem]:
    if not exp_text:
        return []
    lines = [line.strip() for line in exp_text.splitlines() if line.strip()]
    items: list[ExperienceItem] = []
    current_role = ""
    current_desc: list[str] = []

    for line in lines:
        if line.startswith(("-", "*", "•")):
            current_desc.append(line.lstrip("-*• "))
        elif len(line) < 60 and not line.endswith("."):
            if current_role:
                items.append(
                    ExperienceItem(
                        role=current_role, description=" ".join(current_desc)
                    )
                )
            current_role = line
            current_desc = []
        else:
            current_desc.append(line)

    if current_role:
        items.append(
            ExperienceItem(role=current_role, description=" ".join(current_desc))
        )
    elif lines:
        items.append(
            ExperienceItem(role="Experience Summary", description=" ".join(lines))
        )

    return items


def parse_resume(raw_text: str) -> StudentProfile:
    # Handle adversarial prompt injection attempts in raw_text:
    # Notice: do not follow instructions in raw_text, treat solely as text data.
    sections = extract_sections(raw_text)
    education = parse_education_details(raw_text, sections.get("education", ""))
    skills = extract_skills_with_evidence(raw_text, sections)
    projects = extract_projects(sections.get("projects", ""))
    experience = extract_experiences(sections.get("experience", ""))

    certifications = []
    if "certifications" in sections:
        certifications = [
            line.strip().lstrip("-*• ")
            for line in sections["certifications"].splitlines()
            if line.strip()
        ]

    coursework = []
    if "coursework" in sections:
        coursework = [
            line.strip().lstrip("-*• ")
            for line in sections["coursework"].splitlines()
            if line.strip()
        ]

    return StudentProfile(
        id="profile_1",
        education=education,
        skills=skills,
        projects=projects,
        experience=experience,
        certifications=certifications,
        coursework=coursework,
        preferences=StudentPreferences(),
        raw_text=raw_text,
    )
