import unittest

from api.matcher import extract_profile, rank_internships


class MatcherTests(unittest.TestCase):
    def test_extracts_skills_and_resume_sections(self) -> None:
        profile = extract_profile(
            "Education\nBSc Computer Science\n"
            "Projects\nBuilt a React app with Python\n"
            "Experience\nData analysis using pandas"
        )

        self.assertEqual(profile["skills"], ["python", "react", "data analysis", "pandas"])
        self.assertEqual(profile["education"], "BSc Computer Science")
        self.assertEqual(profile["projects"], "Built a React app with Python")
        self.assertEqual(profile["experience"], "Data analysis using pandas")

    def test_ranks_by_skill_overlap_and_reports_missing_skills(self) -> None:
        matches = rank_internships(
            "Python and React developer",
            [
                {"title": "B role", "company": "", "description": "Python, React, SQL"},
                {"title": "A role", "company": "", "description": "Python"},
            ],
        )["matches"]

        self.assertEqual([match["title"] for match in matches], ["A role", "B role"])
        self.assertEqual(matches[0]["score"], 100)
        self.assertEqual(matches[1]["matched_skills"], ["python", "react"])
        self.assertEqual(matches[1]["missing_skills"], ["sql"])
        self.assertEqual(matches[1]["eligibility"]["status"], "needs_review")

    def test_marks_explicit_gpa_requirement_without_gpa_as_review(self) -> None:
        match = rank_internships(
            "Python developer",
            [{"title": "Intern", "description": "Python. Minimum GPA of 3.0 required."}],
        )["matches"][0]

        self.assertEqual(match["eligibility"]["status"], "needs_review")
        self.assertIn("no GPA", match["eligibility"]["detail"])

    def test_flags_only_explicitly_unmet_gpa_requirement(self) -> None:
        match = rank_internships(
            "GPA: 2.8, Python developer",
            [{"title": "Intern", "description": "Python. Minimum GPA of 3.0 required."}],
        )["matches"][0]

        self.assertEqual(
            match["eligibility"]["status"], "does_not_meet_known_requirements"
        )


if __name__ == "__main__":
    unittest.main()
