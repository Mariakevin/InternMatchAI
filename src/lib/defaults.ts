import type { InternshipDetail, StudentPreferences, StudentProfile } from "../types";

export function createDefaultPreferences(): StudentPreferences {
  return {
    preferred_work_modes: ["remote", "hybrid", "on-site"],
    preferred_locations: [],
    willing_to_relocate: false,
    available_hours_per_week: 40,
    preferred_duration_months: 3,
    minimum_stipend: null,
    stipend_currency: "USD",
    stipend_period: "monthly",
    unpaid_acceptable: true,
  };
}

export function createDefaultProfile(): StudentProfile {
  return {
    id: "student_1",
    education: [
      {
        level: "undergraduate",
        degree: "B.Tech",
        discipline: "Computer Science",
        institution: "",
        current_year: 3,
        current_semester: 6,
        enrolment_status: "enrolled",
        graduation_date: "2025",
        cgpa: 8.2,
        cgpa_scale: 10.0,
      },
    ],
    skills: [],
    projects: [],
    experience: [],
    certifications: [],
    coursework: [],
    preferences: createDefaultPreferences(),
    raw_text: "",
  };
}

export function createEmptyInternship(id = "intern_draft"): InternshipDetail {
  return {
    id,
    title: "",
    company: "",
    description: "",
    domain: "",
    responsibilities: [],
    work_mode: "any",
    location: "",
    duration_months: null,
    start_date: null,
    end_date: null,
    weekly_hours: null,
    stipend_amount: null,
    stipend_currency: "USD",
    stipend_period: "monthly",
    stipend_disclosed: true,
    is_unpaid: false,
    application_deadline: null,
    eligibility_conditions: [],
    required_skills: [],
    preferred_skills: [],
    tools_and_tech: [],
    has_contradictions: false,
    contradiction_details: [],
  };
}

export function createDemoInternships(): InternshipDetail[] {
  return [
    {
      ...createEmptyInternship("intern_1"),
      title: "Frontend Engineering Intern",
      company: "Acme Tech Studio",
      description:
        "We are looking for a Frontend Engineering Intern. Work mode: remote. Duration: 3 months. Stipend: $1,200/month.\nQualifications: Degree: B.Tech or BCA in Computer Science or IT. Minimum CGPA of 7.0.\nRequired skills: React, TypeScript, HTML, CSS, Git.\nPreferred: Next.js, Tailwind CSS.",
    },
  ];
}
