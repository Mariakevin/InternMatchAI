from __future__ import annotations

import re


from api.models import (
    GapItem,
    GapReport,
    SkillEvidenceState,
    SkillMatchItem,
    SkillProvenance,
    StudentProfile,
)
from api.taxonomy import normalize_skill, skill_aliases


def match_skills(
    required_skills: list[str],
    preferred_skills: list[str],
    profile: StudentProfile,
) -> tuple[list[SkillMatchItem], GapReport]:
    items: list[SkillMatchItem] = []
    gaps: list[GapItem] = []
    questions: list[str] = []

    # Map candidate's skills by normalized name. Normalize both the stored
    # normalized name and the display name so e.g. "react.js" matches "react".
    cand_skills_map: dict[str, SkillProvenance] = {}
    for skill in profile.skills:
        for term in (skill.normalized_name, skill.name):
            cand_skills_map.setdefault(normalize_skill(term), skill)

    # Helper to check if skill is evidenced in projects, experience, coursework,
    # or certifications, honouring every alias for the canonical skill.
    def find_evidence_in_profile(skill_norm: str) -> tuple[str, str]:
        aliases = skill_aliases(skill_norm)
        alternation = "|".join(re.escape(alias) for alias in aliases)
        pattern = rf"(?<!\w)(?:{alternation})(?!\w)"
        # Search projects
        for p in profile.projects:
            text = f"{p.title} {p.description} {' '.join(p.technologies)}"
            if re.search(pattern, text, re.IGNORECASE):
                return "projects", f"Project '{p.title}': {p.description[:120]}"

        # Search experience
        for exp in profile.experience:
            text = f"{exp.role} {exp.organization} {exp.description} {' '.join(exp.technologies)}"
            if re.search(pattern, text, re.IGNORECASE):
                return (
                    "experience",
                    f"Experience at '{exp.organization or exp.role}': {exp.description[:120]}",
                )

        # Search coursework
        for cw in profile.coursework:
            if re.search(pattern, cw, re.IGNORECASE):
                return "coursework", f"Coursework: {cw}"

        # Search certifications
        for cert in profile.certifications:
            if re.search(pattern, cert, re.IGNORECASE):
                return "certifications", f"Certification: {cert}"

        return "", ""

    # Process required skills
    for req in required_skills:
        norm = normalize_skill(req)
        cand_sp = cand_skills_map.get(norm)

        if cand_sp and cand_sp.is_confirmed_gap:
            items.append(
                SkillMatchItem(
                    internship_skill=req,
                    normalized_skill=norm,
                    status=SkillEvidenceState.CONFIRMED_GAP,
                    is_required=True,
                    matched_student_skill=cand_sp.name,
                    evidence_source="student_confirmed",
                    supporting_excerpt="Student confirmed they do not currently have this skill.",
                    confidence=1.0,
                )
            )
            gaps.append(
                GapItem(
                    skill_or_requirement=req,
                    category="confirmed_gap",
                    guidance=f"Prioritize learning fundamentals of {req} or completing a hands-on tutorial.",
                    priority="high",
                )
            )
        elif cand_sp:
            # Candidate has the skill! Check evidence
            source, excerpt = find_evidence_in_profile(norm)
            if not source and "resume_demonstrated" in cand_sp.source:
                source = "resume_projects_or_experience"
                excerpt = f"Demonstrated in resume sections ({', '.join(cand_sp.evidence_refs)})"

            state = (
                SkillEvidenceState.DEMONSTRATED
                if source
                else SkillEvidenceState.SELF_REPORTED
            )
            items.append(
                SkillMatchItem(
                    internship_skill=req,
                    normalized_skill=norm,
                    status=state,
                    is_required=True,
                    matched_student_skill=cand_sp.name,
                    evidence_source=source or "self_reported",
                    supporting_excerpt=excerpt
                    or "Listed in skills section without detailed project evidence.",
                    confidence=cand_sp.confidence,
                )
            )
            if state == SkillEvidenceState.SELF_REPORTED:
                gaps.append(
                    GapItem(
                        skill_or_requirement=req,
                        category="missing_proof",
                        guidance=f"You listed {req}, but no project or work excerpt mentions it. If you have built something with it, consider adding a brief bullet point to your resume.",
                        priority="medium",
                    )
                )
        else:
            # Not found in resume
            items.append(
                SkillMatchItem(
                    internship_skill=req,
                    normalized_skill=norm,
                    status=SkillEvidenceState.NOT_FOUND_IN_RESUME,
                    is_required=True,
                    matched_student_skill=None,
                    evidence_source="none",
                    supporting_excerpt="Not mentioned in supplied resume text.",
                    confidence=1.0,
                )
            )
            gaps.append(
                GapItem(
                    skill_or_requirement=req,
                    category="missing_required",
                    guidance=f"Required skill '{req}' was not found in your resume. If you know it, add it to your profile. If not, plan a small project using {req}.",
                    priority="high",
                )
            )
            questions.append(
                f"What level of proficiency in {req} is expected for this role?"
            )

    # Process preferred skills
    for pref in preferred_skills:
        norm = normalize_skill(pref)
        cand_sp = cand_skills_map.get(norm)

        if cand_sp and cand_sp.is_confirmed_gap:
            items.append(
                SkillMatchItem(
                    internship_skill=pref,
                    normalized_skill=norm,
                    status=SkillEvidenceState.CONFIRMED_GAP,
                    is_required=False,
                    matched_student_skill=cand_sp.name,
                    evidence_source="student_confirmed",
                    supporting_excerpt="Student confirmed they do not currently have this skill.",
                    confidence=1.0,
                )
            )
            gaps.append(
                GapItem(
                    skill_or_requirement=pref,
                    category="confirmed_gap",
                    guidance=f"{pref} is a nice-to-have skill. Familiarity is beneficial but not mandatory.",
                    priority="low",
                )
            )
        elif cand_sp:
            source, excerpt = find_evidence_in_profile(norm)
            state = (
                SkillEvidenceState.DEMONSTRATED
                if source
                else SkillEvidenceState.SELF_REPORTED
            )
            items.append(
                SkillMatchItem(
                    internship_skill=pref,
                    normalized_skill=norm,
                    status=state,
                    is_required=False,
                    matched_student_skill=cand_sp.name,
                    evidence_source=source or "self_reported",
                    supporting_excerpt=excerpt or "Listed in resume skills.",
                    confidence=cand_sp.confidence,
                )
            )
        else:
            items.append(
                SkillMatchItem(
                    internship_skill=pref,
                    normalized_skill=norm,
                    status=SkillEvidenceState.NOT_FOUND_IN_RESUME,
                    is_required=False,
                    matched_student_skill=None,
                    evidence_source="none",
                    supporting_excerpt="Preferred skill not mentioned in resume.",
                    confidence=1.0,
                )
            )
            gaps.append(
                GapItem(
                    skill_or_requirement=pref,
                    category="missing_preferred",
                    guidance=f"Preferred skill '{pref}' is a bonus. You can apply even without it.",
                    priority="low",
                )
            )

    return items, GapReport(gaps=gaps, questions_for_employer=questions)
