import asyncio
import unittest
from io import BytesIO
from unittest.mock import patch

from docx import Document
from fastapi import HTTPException
from pypdf import PdfWriter

from api.eligibility_engine import evaluate_single_condition
from api.fit_scorer import calculate_fit_score, calculate_practical_fit
from api.internship_parser import analyze_listing_risks, parse_internship
from api.main import (
    InternshipInput,
    LegacyMatchRequest,
    StructuredMatchRequest,
    extract_resume,
    match,
    parse_resume_text,
    TextParseRequest,
)
from api.models import (
    ConditionStatus,
    EducationItem,
    EligibilityCondition,
    InternshipDetail,
    OverallEligibility,
    ProjectItem,
    SkillEvidenceState,
    SkillMatchItem,
    SkillProvenance,
    StudentPreferences,
    StudentProfile,
    WorkMode,
)
from api.resume_parser import extract_file_text, parse_resume
from api.skill_matcher import match_skills


class _MockUpload:
    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self._content = content
        self._size: int | None = None

    async def read(self, size: int = -1) -> bytes:
        self._size = size
        if size is None or size < 0:
            return self._content
        return self._content[:size]


class StipendParsingTests(unittest.TestCase):
    def test_fee_amount_is_not_a_stipend(self) -> None:
        internship = parse_internship(
            title="Program", description="Application fee of $49 is required. Python."
        )
        self.assertIsNone(internship.stipend_amount)

    def test_monthly_currency_stipend_is_parsed(self) -> None:
        internship = parse_internship(
            title="Intern", description="Stipend: $2,000 per month. Python."
        )
        self.assertEqual(internship.stipend_amount, 2000.0)
        self.assertEqual(internship.stipend_period, "monthly")

    def test_bare_amount_without_currency_is_not_a_year_or_stipend(self) -> None:
        internship = parse_internship(
            title="Intern", description="Stipend 2000/month. Python."
        )
        self.assertIsNone(internship.stipend_amount)
        self.assertFalse(
            any(c.condition_type == "year" for c in internship.eligibility_conditions)
        )


class RiskFlagTests(unittest.TestCase):
    def test_application_fee_still_fires(self) -> None:
        risks = analyze_listing_risks("Application fee of $49 is required.")
        self.assertTrue(any(r.category == "application_fee" for r in risks))

    def test_negated_application_fee_does_not_fire(self) -> None:
        risks = analyze_listing_risks("No application fee required for this role.")
        self.assertFalse(any(r.category == "application_fee" for r in risks))

    def test_negated_deposit_and_training_fees_do_not_fire(self) -> None:
        deposit_risks = analyze_listing_risks("There is no security deposit.")
        self.assertFalse(any(r.category == "security_deposit" for r in deposit_risks))
        training_risks = analyze_listing_risks("No training fee is required.")
        self.assertFalse(any(r.category == "paid_training" for r in training_risks))

    def test_short_post_with_facts_is_not_vague(self) -> None:
        text = "Remote Python intern for 3rd year students with $1000/month."
        risks = analyze_listing_risks(text)
        self.assertFalse(any(r.category == "vague_identity" for r in risks))

    def test_short_empty_post_is_still_vague(self) -> None:
        risks = analyze_listing_risks("Join us now!")
        self.assertTrue(any(r.category == "vague_identity" for r in risks))


class HoursAndWorkModeTests(unittest.TestCase):
    def test_weekly_hours_range_takes_upper_bound(self) -> None:
        internship = parse_internship(
            title="Intern", description="Requires 20-25 hours per week."
        )
        self.assertEqual(internship.weekly_hours, 25)

    def test_weekly_hours_variants(self) -> None:
        self.assertEqual(
            parse_internship(title="A", description="20 hours/week").weekly_hours, 20
        )
        self.assertEqual(
            parse_internship(title="B", description="20 hours a week").weekly_hours, 20
        )

    def test_office_hours_do_not_produce_weekly_hours(self) -> None:
        internship = parse_internship(title="Intern", description="Office hours 9-5.")
        self.assertIsNone(internship.weekly_hours)

    def test_remote_with_occasional_office_is_remote(self) -> None:
        internship = parse_internship(
            title="Intern", description="This is remote with occasional office visits."
        )
        self.assertEqual(internship.work_mode, WorkMode.REMOTE)

    def test_onsite_with_remote_fridays_is_onsite(self) -> None:
        internship = parse_internship(
            title="Intern", description="Work on-site with remote Fridays."
        )
        self.assertEqual(internship.work_mode, WorkMode.ONSITE)

    def test_hybrid_wins(self) -> None:
        internship = parse_internship(
            title="Intern", description="Hybrid role, remote or on-site."
        )
        self.assertEqual(internship.work_mode, WorkMode.HYBRID)


class YearConditionTests(unittest.TestCase):
    def test_contract_duration_is_not_an_academic_year(self) -> None:
        internship = parse_internship(
            title="Intern", description="This is a 2 year contract position."
        )
        self.assertFalse(
            any(c.condition_type == "year" for c in internship.eligibility_conditions)
        )

    def test_third_year_students_is_an_academic_year(self) -> None:
        internship = parse_internship(
            title="Intern", description="Open to 3rd year students."
        )
        year_conditions = [
            c for c in internship.eligibility_conditions if c.condition_type == "year"
        ]
        self.assertEqual(len(year_conditions), 1)
        self.assertEqual(year_conditions[0].value, 3)


class ResumeExtractionTests(unittest.TestCase):
    def test_percentage_remote_is_not_cgpa(self) -> None:
        profile = parse_resume(
            "Education\nB.Tech in Computer Science\nThis role is 100% remote."
        )
        self.assertEqual(len(profile.education), 1)
        self.assertIsNone(profile.education[0].cgpa)

    def test_cgpa_is_parsed(self) -> None:
        profile = parse_resume("Education\nB.Tech in Computer Science\nCGPA: 8.5/10")
        self.assertEqual(profile.education[0].cgpa, 8.5)
        self.assertEqual(profile.education[0].cgpa_scale, 10.0)

    def test_percentage_marks_are_parsed(self) -> None:
        profile = parse_resume("Education\nB.Tech in Computer Science\n85% marks")
        self.assertEqual(profile.education[0].cgpa, 85.0)
        self.assertEqual(profile.education[0].cgpa_scale, 100.0)

    def test_enrolment_defaults_to_unknown_without_evidence(self) -> None:
        profile = parse_resume("Education\nB.Tech in Computer Science")
        self.assertEqual(profile.education[0].enrolment_status, "")

    def test_semester_establishes_enrolment(self) -> None:
        profile = parse_resume("Education\nB.Tech in Computer Science\nSemester 6")
        self.assertEqual(profile.education[0].enrolment_status, "enrolled")

    def test_graduated_wording_establishes_graduation(self) -> None:
        profile = parse_resume("Education\nB.Tech in Computer Science\nGraduated")
        self.assertEqual(profile.education[0].enrolment_status, "graduated")

    def test_non_utf8_text_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            extract_file_text("resume.txt", b"\xff\xfe\x00\x00")
        self.assertEqual(ctx.exception.status_code, 400)


class EligibilityRobustnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = StudentProfile(
            education=[EducationItem(cgpa=7.5, cgpa_scale=10.0)]
        )

    def test_marks_condition_with_zero_scale_is_unknown(self) -> None:
        condition = EligibilityCondition(
            condition_id="marks",
            condition_type="marks",
            operator=">=",
            value={"min_value": 7, "scale": 0},
        )
        result = evaluate_single_condition(condition, self.profile)
        self.assertEqual(result.status, ConditionStatus.UNKNOWN)

    def test_marks_condition_with_non_numeric_value_is_unknown(self) -> None:
        condition = EligibilityCondition(
            condition_id="marks",
            condition_type="marks",
            operator=">=",
            value="high",
        )
        result = evaluate_single_condition(condition, self.profile)
        self.assertEqual(result.status, ConditionStatus.UNKNOWN)

    def test_graduation_date_with_month_prefix_is_evaluated(self) -> None:
        profile = StudentProfile(education=[EducationItem(graduation_date="05/2025")])
        equals = EligibilityCondition(
            condition_id="grad-eq",
            condition_type="graduation_date",
            operator="==",
            value=2025,
        )
        between = EligibilityCondition(
            condition_id="grad-between",
            condition_type="graduation_date",
            operator="between",
            value=[2024, 2026],
        )
        self.assertEqual(
            evaluate_single_condition(equals, profile).status, ConditionStatus.PASS
        )
        self.assertEqual(
            evaluate_single_condition(between, profile).status, ConditionStatus.PASS
        )


class SkillNormalizationTests(unittest.TestCase):
    def test_react_js_profile_skill_matches_react(self) -> None:
        profile = StudentProfile(
            skills=[SkillProvenance(name="react.js", normalized_name="react.js")]
        )
        matches, _ = match_skills(["react"], [], profile)
        self.assertNotEqual(matches[0].status, SkillEvidenceState.NOT_FOUND_IN_RESUME)

    def test_alias_evidence_is_found_in_projects(self) -> None:
        profile = StudentProfile(
            skills=[SkillProvenance(name="React", normalized_name="react")],
            projects=[
                ProjectItem(
                    title="Web app",
                    description="Built with ReactJS and FastAPI",
                )
            ],
        )
        matches, _ = match_skills(["react"], [], profile)
        self.assertEqual(matches[0].status, SkillEvidenceState.DEMONSTRATED)
        self.assertEqual(matches[0].evidence_source, "projects")


class StipendComparisonTests(unittest.TestCase):
    def test_currency_mismatch_is_not_compared(self) -> None:
        profile = StudentProfile(
            preferences=StudentPreferences(
                minimum_stipend=1000.0,
                stipend_currency="USD",
                stipend_period="monthly",
            )
        )
        fit, _ = calculate_practical_fit(
            profile,
            WorkMode.ANY,
            "",
            None,
            None,
            20000.0,
            False,
            stipend_currency="INR",
            stipend_period="monthly",
        )
        self.assertIsNone(fit.stipend_match)
        self.assertTrue(any("direct comparison not possible" in d for d in fit.details))

    def test_matching_currency_monthly_stipend_passes(self) -> None:
        profile = StudentProfile(
            preferences=StudentPreferences(
                minimum_stipend=1000.0,
                stipend_currency="USD",
                stipend_period="monthly",
            )
        )
        fit, _ = calculate_practical_fit(
            profile,
            WorkMode.ANY,
            "",
            None,
            None,
            1200.0,
            False,
            stipend_currency="USD",
            stipend_period="monthly",
        )
        self.assertTrue(fit.stipend_match)

    def test_matching_currency_inr_stipend_passes(self) -> None:
        profile = StudentProfile(
            preferences=StudentPreferences(
                minimum_stipend=15000.0,
                stipend_currency="INR",
                stipend_period="monthly",
            )
        )
        fit, _ = calculate_practical_fit(
            profile,
            WorkMode.ANY,
            "",
            None,
            None,
            20000.0,
            False,
            stipend_currency="INR",
            stipend_period="monthly",
        )
        self.assertTrue(fit.stipend_match)

    def test_hourly_stipend_is_converted_to_monthly(self) -> None:
        profile = StudentProfile(
            preferences=StudentPreferences(
                minimum_stipend=1000.0,
                stipend_currency="USD",
                stipend_period="monthly",
            )
        )
        fit, _ = calculate_practical_fit(
            profile,
            WorkMode.ANY,
            "",
            None,
            None,
            10.0,
            False,
            stipend_currency="USD",
            stipend_period="hourly",
        )
        self.assertTrue(fit.stipend_match)


class FitScorerTests(unittest.TestCase):
    def test_digital_is_not_a_relevant_discipline(self) -> None:
        score = calculate_fit_score(
            [],
            StudentProfile(education=[EducationItem(discipline="Digital Media")]),
            OverallEligibility.ELIGIBLE,
            practical_score=None,
        )
        self.assertEqual(score.breakdown.education_relevance, 60.0)

    def test_information_technology_is_relevant(self) -> None:
        score = calculate_fit_score(
            [],
            StudentProfile(
                education=[EducationItem(discipline="Information Technology")]
            ),
            OverallEligibility.ELIGIBLE,
            practical_score=None,
        )
        self.assertEqual(score.breakdown.education_relevance, 90.0)

    def test_custom_weights_missing_keys_fall_back_to_defaults(self) -> None:
        profile = StudentProfile(
            education=[EducationItem(discipline="Computer Science")]
        )
        skill_matches = [
            SkillMatchItem(
                internship_skill="python",
                normalized_skill="python",
                status=SkillEvidenceState.DEMONSTRATED,
                is_required=True,
            )
        ]
        score = calculate_fit_score(
            skill_matches,
            profile,
            OverallEligibility.ELIGIBLE,
            practical_score=50.0,
            weights={"required_skills": 0.5},
        )
        self.assertIsNotNone(score.score)


class FileExtractionSafetyTests(unittest.TestCase):
    def test_encrypted_pdf_returns_400(self) -> None:
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("secret")
        buffer = BytesIO()
        writer.write(buffer)

        with self.assertRaises(HTTPException) as ctx:
            extract_file_text("resume.pdf", buffer.getvalue())
        self.assertEqual(ctx.exception.status_code, 400)

    def test_corrupt_pdf_returns_400(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            extract_file_text("resume.pdf", b"not a real pdf")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_pdf_page_limit_returns_422(self) -> None:
        writer = PdfWriter()
        for _ in range(101):
            writer.add_blank_page(width=100, height=100)
        buffer = BytesIO()
        writer.write(buffer)

        with self.assertRaises(HTTPException) as ctx:
            extract_file_text("resume.pdf", buffer.getvalue())
        self.assertEqual(ctx.exception.status_code, 422)

    def test_corrupt_docx_returns_400(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            extract_file_text("resume.docx", b"garbage, not a zip")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_docx_success_path(self) -> None:
        document = Document()
        document.add_paragraph("Education")
        document.add_paragraph("B.Tech in Computer Science")
        document.add_paragraph("CGPA: 8.5/10")
        buffer = BytesIO()
        document.save(buffer)

        text = extract_file_text("resume.docx", buffer.getvalue())
        self.assertIn("B.Tech in Computer Science", text)

    def test_oversized_extracted_text_returns_422(self) -> None:
        content = ("a" * 60001).encode("utf-8")
        upload = _MockUpload("resume.txt", content)
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(extract_resume(upload))
        self.assertEqual(ctx.exception.status_code, 422)

    def test_unsupported_extension_returns_415(self) -> None:
        upload = _MockUpload("resume.exe", b"binary")
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(extract_resume(upload))
        self.assertEqual(ctx.exception.status_code, 415)

    def test_oversized_upload_returns_413(self) -> None:
        content = b"x" * (5 * 1024 * 1024 + 1)
        upload = _MockUpload("resume.txt", content)
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(extract_resume(upload))
        self.assertEqual(ctx.exception.status_code, 413)


class ErrorBoundaryTests(unittest.TestCase):
    def test_parse_text_unexpected_error_becomes_422(self) -> None:
        with patch("api.main.parse_resume", side_effect=RuntimeError("boom")):
            with self.assertRaises(HTTPException) as ctx:
                parse_resume_text(TextParseRequest(text="Education\nB.Tech"))
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(
            ctx.exception.detail, "Could not parse the provided resume text."
        )

    def test_match_unexpected_error_becomes_500(self) -> None:
        request = StructuredMatchRequest(
            profile=StudentProfile(),
            internships=[InternshipDetail(title="Intern", description="Python")],
        )
        with patch("api.main.orchestrate_matching", side_effect=RuntimeError("boom")):
            with self.assertRaises(HTTPException) as ctx:
                match(request)
        self.assertEqual(ctx.exception.status_code, 500)
        self.assertEqual(ctx.exception.detail, "Could not complete matching.")


class LegacyMatchContractTests(unittest.TestCase):
    def test_legacy_match_returns_existing_keys(self) -> None:
        request = LegacyMatchRequest(
            resume_text="Python and React developer",
            internships=[
                InternshipInput(
                    title="Backend Intern",
                    company="Acme",
                    description="Python, React, SQL",
                )
            ],
        )
        result = match(request)

        self.assertEqual(
            set(result.keys()),
            {"profile", "structured_profile", "matches", "structured_response"},
        )
        self.assertEqual(len(result["matches"]), 1)
        match_item = result["matches"][0]
        self.assertEqual(
            set(match_item.keys()),
            {
                "id",
                "title",
                "company",
                "score",
                "matched_skills",
                "missing_skills",
                "eligibility",
                "requirements_found",
                "structured_analysis",
            },
        )
        self.assertIn("status", match_item["eligibility"])
        self.assertIn("detail", match_item["eligibility"])


if __name__ == "__main__":
    unittest.main()
