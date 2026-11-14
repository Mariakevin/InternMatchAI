import io
import unittest
import asyncio
from fastapi import UploadFile, HTTPException

from api.main import (
    health,
    parse_resume_text,
    extract_internship_details,
    match,
    reanalyze,
    extract_resume,
    TextParseRequest,
    InternshipParseRequest,
    StructuredMatchRequest,
)
from api.models import StudentProfile, InternshipDetail


class ApiUnitTests(unittest.TestCase):
    def test_health_endpoint(self):
        res = health()
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["version"], "0.2.0")

    def test_extract_resume_txt(self):
        txt_content = (
            "Education\n"
            "B.Tech in Computer Science\n"
            "CGPA: 8.8/10\n"
            "Graduating in 2025\n"
            "Skills\n"
            "Python, React, SQL, Docker\n"
            "Projects\n"
            "E-commerce Web App built with React and Python FastAPI\n"
        ).encode("utf-8")

        upload_file = UploadFile(
            filename="resume.txt",
            file=io.BytesIO(txt_content),
        )

        res = asyncio.run(extract_resume(upload_file))
        self.assertIn("text", res)
        self.assertIn("structured_profile", res)
        profile = res["structured_profile"]
        self.assertEqual(profile["education"][0]["degree"], "B.Tech")
        self.assertEqual(profile["education"][0]["cgpa"], 8.8)
        self.assertTrue(any(s["normalized_name"] == "python" for s in profile["skills"]))

    def test_extract_resume_unsupported_format(self):
        upload_file = UploadFile(
            filename="malicious.exe",
            file=io.BytesIO(b"executable content"),
        )
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(extract_resume(upload_file))
        self.assertEqual(ctx.exception.status_code, 415)

    def test_parse_internship_text_endpoint(self):
        req = InternshipParseRequest(
            title="Backend Engineering Intern",
            company="Acme Corp",
            description=(
                "Work mode: remote. Stipend: $1,500/month. Duration: 6 months.\n"
                "Eligibility: Degree: B.Tech in Computer Science. Minimum CGPA of 7.5.\n"
                "Required skills: Python, FastAPI, PostgreSQL.\n"
                "Preferred: Docker, AWS.\n"
            ),
        )
        res = extract_internship_details(req)
        internship = res["internship"]
        self.assertEqual(internship["title"], "Backend Engineering Intern")
        self.assertEqual(internship["work_mode"], "remote")
        self.assertEqual(internship["stipend_amount"], 1500.0)
        self.assertEqual(internship["duration_months"], 6)
        self.assertIn("python", internship["required_skills"])
        self.assertIn("docker", internship["preferred_skills"])

    def test_match_and_reanalyze_workflow(self):
        # 1. Parse resume text
        resume_text = (
            "Education\n"
            "B.Tech in Computer Science\n"
            "CGPA: 8.2/10\n"
            "Skills\n"
            "Python, React, SQL\n"
            "Projects\n"
            "Full Stack Web App using React and Python"
        )
        p_res = parse_resume_text(TextParseRequest(text=resume_text))
        profile_dict = p_res["structured_profile"]
        profile = StudentProfile.model_validate(profile_dict)

        # 2. Parse internship
        i_req = InternshipParseRequest(
            title="Software Intern",
            company="Tech Innovations",
            description="Degree: B.Tech in Computer Science. Required: Python, React. Minimum CGPA: 7.0.",
        )
        i_res = extract_internship_details(i_req)
        internship = InternshipDetail.model_validate(i_res["internship"])

        # 3. Match
        match_req = StructuredMatchRequest(profile=profile, internships=[internship])
        match_res = match(match_req)
        self.assertIn("matches", match_res)
        self.assertEqual(len(match_res["matches"]), 1)
        analysis = match_res["matches"][0]
        self.assertEqual(analysis["eligibility"]["status"], "ELIGIBLE")
        self.assertGreater(analysis["fit_score"]["score"], 60)

        # 4. Reanalyze with student-confirmed gap
        for s in profile.skills:
            if s.normalized_name == "python":
                s.is_confirmed_gap = True
                s.student_confirmed = True

        re_req = StructuredMatchRequest(profile=profile, internships=[internship])
        re_res = reanalyze(re_req)
        re_analysis = re_res["matches"][0]
        py_match = next(
            s for s in re_analysis["skill_matches"] if s["normalized_skill"] == "python"
        )
        self.assertEqual(py_match["status"], "CONFIRMED_GAP")


if __name__ == "__main__":
    unittest.main()
