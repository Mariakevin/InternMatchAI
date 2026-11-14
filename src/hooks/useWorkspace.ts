import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type {
  InternshipDetail,
  MatchResponse,
  SkillProvenance,
  StudentProfile,
} from "../types";
import {
  extractInternship,
  extractResume,
  getErrorMessage,
  isAbortError,
  match as matchApi,
  parseResumeText,
  reanalyze as reanalyzeApi,
} from "../lib/api";
import { createDefaultProfile, createDemoInternships, createEmptyInternship } from "../lib/defaults";
import { countMatches, filterMatches, type MatchTab } from "../lib/matchFilters";

export type ExtractionMeta = {
  attempted: boolean;
  stale: boolean;
};

export type SkillCorrectionAction = "self_report" | "confirm_gap";

const TEXT_PARSE_DEBOUNCE_MS = 500;

function isMatchable(item: InternshipDetail): boolean {
  return item.title.trim().length > 0 && item.description.trim().length > 0;
}

function postingLabel(item: InternshipDetail): string {
  return item.title.trim() ? `“${item.title.trim()}”` : "an untitled role";
}

function mergeExtraction(base: InternshipDetail, extracted: InternshipDetail): InternshipDetail {
  return {
    ...extracted,
    id: base.id,
    title: base.title || extracted.title,
    company: base.company,
    description: base.description,
  };
}

function clearDerivedFields(item: InternshipDetail, description: string): InternshipDetail {
  return {
    ...item,
    description,
    domain: "",
    responsibilities: [],
    work_mode: "any",
    location: "",
    duration_months: null,
    start_date: null,
    end_date: null,
    weekly_hours: null,
    stipend_amount: null,
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

function hasExtractedFacts(item: InternshipDetail): boolean {
  return (
    item.eligibility_conditions.length > 0 ||
    item.required_skills.length > 0 ||
    item.preferred_skills.length > 0 ||
    item.work_mode !== "any" ||
    item.stipend_amount !== null ||
    item.is_unpaid
  );
}

export function useWorkspace() {
  const [resumeText, setResumeTextState] = useState("");
  const [fileName, setFileName] = useState("");
  const [fileSize, setFileSize] = useState<number | null>(null);
  const [profile, setProfileState] = useState<StudentProfile>(() => createDefaultProfile());
  const [internships, setInternshipsState] = useState<InternshipDetail[]>(() =>
    createDemoInternships(),
  );

  const [analysisResult, setAnalysisResultState] = useState<MatchResponse | null>(null);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});
  const [activeTab, setActiveTab] = useState<MatchTab>("all");
  const [showComparison, setShowComparison] = useState(false);
  const [editingInternshipId, setEditingInternshipId] = useState<string | null>(null);
  const [profileEditorOpen, setProfileEditorOpen] = useState(false);
  const [newSkillInput, setNewSkillInput] = useState("");

  const [resumeBusy, setResumeBusy] = useState(false);
  const [parsingText, setParsingText] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [extractingIds, setExtractingIds] = useState<Record<string, boolean>>({});
  const [extractionMeta, setExtractionMeta] = useState<Record<string, ExtractionMeta>>({});
  const [extractionErrors, setExtractionErrors] = useState<Record<string, string>>({});

  const [error, setError] = useState("");
  const [resumeError, setResumeError] = useState("");
  const [parseNotice, setParseNotice] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  const [textRevision, setTextRevision] = useState(0);

  const profileRef = useRef(profile);
  const internshipsRef = useRef(internships);
  const analysisRef = useRef(analysisResult);
  const resumeTextRef = useRef(resumeText);
  const extractionMetaRef = useRef(extractionMeta);

  profileRef.current = profile;
  internshipsRef.current = internships;
  analysisRef.current = analysisResult;
  resumeTextRef.current = resumeText;
  extractionMetaRef.current = extractionMeta;

  const uploadSeq = useRef(0);
  const uploadAbort = useRef<AbortController | null>(null);
  const parseSeq = useRef(0);
  const parseAbort = useRef<AbortController | null>(null);
  const analysisSeq = useRef(0);
  const analysisAbort = useRef<AbortController | null>(null);
  const extractAborts = useRef<Record<string, AbortController>>({});
  const internshipCounter = useRef(0);

  const invalidateAnalysis = useCallback(() => {
    analysisSeq.current += 1;
    analysisAbort.current?.abort();
    analysisAbort.current = null;
    analysisRef.current = null;
    setAnalysisResultState(null);
    setAnalyzing(false);
    setReanalyzing(false);
    setError("");
  }, []);

  const runReanalysis = useCallback(async (nextProfile: StudentProfile) => {
    const postings = internshipsRef.current.filter(isMatchable);
    if (postings.length === 0) return;

    const requestId = ++analysisSeq.current;
    analysisAbort.current?.abort();
    const controller = new AbortController();
    analysisAbort.current = controller;

    setReanalyzing(true);
    setError("");
    setStatusMessage("Re-analyzing with your skill correction…");

    try {
      const data = await reanalyzeApi({ profile: nextProfile, internships: postings }, controller.signal);
      if (requestId !== analysisSeq.current) return;
      analysisRef.current = data;
      setAnalysisResultState(data);
      setExpandedCards((prev) => {
        const firstId = data.matches?.[0]?.internship_id;
        if (!firstId || prev[firstId]) return prev;
        return { ...prev, [firstId]: true };
      });
      setStatusMessage(
        `Re-analysis complete — ${data.matches.length} posting${
          data.matches.length === 1 ? "" : "s"
        } re-evaluated.`,
      );
    } catch (err) {
      if (requestId !== analysisSeq.current || isAbortError(err)) return;
      setError(getErrorMessage(err));
      setStatusMessage("Re-analysis failed — existing results were cleared.");
    } finally {
      if (requestId === analysisSeq.current) setReanalyzing(false);
    }
  }, []);

  const commitProfile = useCallback(
    (next: StudentProfile, mode: "invalidate" | "reanalyze" = "invalidate") => {
      const hadAnalysis = analysisRef.current !== null;
      invalidateAnalysis();
      setProfileState(next);
      profileRef.current = next;
      setParseNotice("");
      if (mode === "reanalyze" && hadAnalysis) {
        void runReanalysis(next);
      }
    },
    [invalidateAnalysis, runReanalysis],
  );

  const updateProfile = useCallback(
    (updater: (prev: StudentProfile) => StudentProfile) => {
      setProfileState((prev) => {
        const next = updater(prev);
        profileRef.current = next;
        return next;
      });
      invalidateAnalysis();
      setParseNotice("");
    },
    [invalidateAnalysis],
  );

  const updateResumeText = useCallback(
    (text: string) => {
      setResumeTextState(text);
      resumeTextRef.current = text;
      setResumeError("");
      setParseNotice("");
      setTextRevision((value) => value + 1);
      invalidateAnalysis();
    },
    [invalidateAnalysis],
  );

  const uploadResume = useCallback(
    async (file: File) => {
      const requestId = ++uploadSeq.current;
      uploadAbort.current?.abort();
      const controller = new AbortController();
      uploadAbort.current = controller;

      parseAbort.current?.abort();
      parseSeq.current += 1;
      setParsingText(false);

      setResumeBusy(true);
      setResumeError("");
      setError("");
      setParseNotice("");
      setStatusMessage(`Extracting ${file.name}…`);

      try {
        const data = await extractResume(file, controller.signal);
        if (requestId !== uploadSeq.current) return;

        const text = data.text ?? "";
        setResumeTextState(text);
        resumeTextRef.current = text;
        setFileName(data.filename || file.name);
        setFileSize(file.size);

        if (data.structured_profile) {
          const parsed = data.structured_profile;
          setProfileState((prev) => {
            const next: StudentProfile = {
              ...parsed,
              preferences: prev.preferences,
            };
            profileRef.current = next;
            return next;
          });
        }

        invalidateAnalysis();
        setStatusMessage(
          "Resume parsed. Review the profile snapshot and correct anything the parser missed.",
        );
      } catch (err) {
        if (requestId !== uploadSeq.current || isAbortError(err)) return;
        setResumeError(getErrorMessage(err));
        setStatusMessage("Resume upload failed. Your existing profile was kept.");
      } finally {
        if (requestId === uploadSeq.current) setResumeBusy(false);
      }
    },
    [invalidateAnalysis],
  );

  useEffect(() => {
    if (textRevision === 0) return;

    const text = resumeTextRef.current;
    if (!text.trim()) {
      parseAbort.current?.abort();
      parseSeq.current += 1;
      setParsingText(false);
      return;
    }

    const requestId = ++parseSeq.current;
    parseAbort.current?.abort();
    const controller = new AbortController();
    parseAbort.current = controller;

    const timer = window.setTimeout(() => {
      setParsingText(true);
      setResumeError("");
      setStatusMessage("Parsing resume text…");

      void (async () => {
        try {
          const data = await parseResumeText(text, controller.signal);
          if (requestId !== parseSeq.current) return;
          if (data.structured_profile) {
            const parsed = data.structured_profile;
            setProfileState((prev) => {
              const next: StudentProfile = {
                ...parsed,
                preferences: prev.preferences,
              };
              profileRef.current = next;
              return next;
            });
            invalidateAnalysis();
            setParseNotice("Re-parsed · preferences preserved");
            setStatusMessage("Resume text re-parsed. Review the profile snapshot.");
          }
        } catch (err) {
          if (requestId !== parseSeq.current || isAbortError(err)) return;
          setResumeError(getErrorMessage(err));
          setParseNotice("");
          setStatusMessage("Resume text could not be parsed.");
        } finally {
          if (requestId === parseSeq.current) setParsingText(false);
        }
      })();
    }, TEXT_PARSE_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [textRevision, invalidateAnalysis]);

  const updateEducation = useCallback(
    (index: number, patch: Partial<StudentProfile["education"][number]>) => {
      updateProfile((prev) => ({
        ...prev,
        education: prev.education.map((item, itemIndex) =>
          itemIndex === index ? { ...item, ...patch } : item,
        ),
      }));
    },
    [updateProfile],
  );

  const updatePreferences = useCallback(
    (patch: Partial<StudentProfile["preferences"]>) => {
      updateProfile((prev) => ({
        ...prev,
        preferences: { ...prev.preferences, ...patch },
      }));
    },
    [updateProfile],
  );

  const addCustomSkill = useCallback(() => {
    const raw = newSkillInput.trim();
    if (!raw) return;
    const normalized = raw.toLowerCase();
    const current = profileRef.current;

    setNewSkillInput("");
    if (current.skills.some((skill) => skill.normalized_name === normalized)) return;

    const nextSkill: SkillProvenance = {
      name: raw,
      normalized_name: normalized,
      source: "student_added",
      evidence_refs: ["user_input"],
      student_confirmed: true,
      is_confirmed_gap: false,
      confidence: 1,
    };

    commitProfile(
      { ...current, skills: [...current.skills, nextSkill] },
      "reanalyze",
    );
  }, [commitProfile, newSkillInput]);

  const removeSkill = useCallback(
    (normalizedName: string) => {
      const current = profileRef.current;
      commitProfile(
        {
          ...current,
          skills: current.skills.filter((skill) => skill.normalized_name !== normalizedName),
        },
        "reanalyze",
      );
    },
    [commitProfile],
  );

  const correctSkill = useCallback(
    (skillName: string, action: SkillCorrectionAction) => {
      const current = profileRef.current;
      const normalized = skillName.trim().toLowerCase();
      const updatedSkills = [...current.skills];
      const existingIndex = updatedSkills.findIndex(
        (skill) => skill.normalized_name === normalized,
      );

      if (action === "confirm_gap") {
        if (existingIndex >= 0) {
          updatedSkills[existingIndex] = {
            ...updatedSkills[existingIndex],
            is_confirmed_gap: true,
            student_confirmed: true,
            source: "student_confirmed",
          };
        } else {
          updatedSkills.push({
            name: skillName,
            normalized_name: normalized,
            source: "student_confirmed",
            evidence_refs: ["student_declaration"],
            student_confirmed: true,
            is_confirmed_gap: true,
            confidence: 1,
          });
        }
      } else if (existingIndex >= 0) {
        updatedSkills[existingIndex] = {
          ...updatedSkills[existingIndex],
          is_confirmed_gap: false,
          student_confirmed: true,
          source: "student_confirmed",
        };
      } else {
        updatedSkills.push({
          name: skillName,
          normalized_name: normalized,
          source: "student_confirmed",
          evidence_refs: ["student_declaration"],
          student_confirmed: true,
          is_confirmed_gap: false,
          confidence: 0.8,
        });
      }

      commitProfile({ ...current, skills: updatedSkills }, "reanalyze");
    },
    [commitProfile],
  );

  const updateInternshipField = useCallback(
    (
      id: string,
      field: keyof InternshipDetail,
      value: InternshipDetail[keyof InternshipDetail],
    ) => {
      const current = internshipsRef.current.find((item) => item.id === id);

      setInternshipsState((prev) => {
        const next = prev.map((item) => {
          if (item.id !== id) return item;
          if (field === "description") {
            return clearDerivedFields(item, String(value));
          }
          return { ...item, [field]: value } as InternshipDetail;
        });
        internshipsRef.current = next;
        return next;
      });

      if (field === "description" && current) {
        const attempted = extractionMetaRef.current[id]?.attempted ?? false;
        if (attempted || hasExtractedFacts(current)) {
          const nextMeta = {
            ...extractionMetaRef.current,
            [id]: { attempted: true, stale: true },
          };
          extractionMetaRef.current = nextMeta;
          setExtractionMeta(nextMeta);
        }
        setExtractionErrors((prev) => {
          if (!(id in prev)) return prev;
          const next = { ...prev };
          delete next[id];
          return next;
        });
      }

      invalidateAnalysis();
    },
    [invalidateAnalysis],
  );

  const addInternship = useCallback(() => {
    const current = internshipsRef.current;
    if (current.length >= 20) return;
    internshipCounter.current += 1;
    const id = `intern_${Date.now()}_${internshipCounter.current}`;
    const next = [...current, createEmptyInternship(id)];
    internshipsRef.current = next;
    setInternshipsState(next);
    invalidateAnalysis();
  }, [invalidateAnalysis]);

  const removeInternship = useCallback(
    (id: string) => {
      if (internshipsRef.current.length <= 1) return;
      extractAborts.current[id]?.abort();
      delete extractAborts.current[id];

      const next = internshipsRef.current.filter((item) => item.id !== id);
      internshipsRef.current = next;
      setInternshipsState(next);
      setExtractingIds((prev) => {
        if (!(id in prev)) return prev;
        const copy = { ...prev };
        delete copy[id];
        return copy;
      });
      setExtractionErrors((prev) => {
        if (!(id in prev)) return prev;
        const copy = { ...prev };
        delete copy[id];
        return copy;
      });
      setEditingInternshipId((prev) => (prev === id ? null : prev));
      invalidateAnalysis();
    },
    [invalidateAnalysis],
  );

  const extractInternshipCriteria = useCallback(
    async (id: string) => {
      const target = internshipsRef.current.find((item) => item.id === id);
      if (!target) return;
      if (!target.description.trim()) {
        setExtractionErrors((prev) => ({
          ...prev,
          [id]: "Add a job description before extracting criteria.",
        }));
        return;
      }

      extractAborts.current[id]?.abort();
      const controller = new AbortController();
      extractAborts.current[id] = controller;

      setExtractingIds((prev) => ({ ...prev, [id]: true }));
      setExtractionErrors((prev) => {
        if (!(id in prev)) return prev;
        const copy = { ...prev };
        delete copy[id];
        return copy;
      });
      setStatusMessage(`Extracting criteria for ${postingLabel(target)}…`);

      try {
        const data = await extractInternship(
          {
            title: target.title || "Internship Position",
            company: target.company,
            description: target.description,
          },
          controller.signal,
        );

        if (extractAborts.current[id] !== controller) return;

        if (data.internship) {
          setInternshipsState((prev) => {
            const next = prev.map((item) =>
              item.id === id ? mergeExtraction(item, data.internship as InternshipDetail) : item,
            );
            internshipsRef.current = next;
            return next;
          });
          const nextMeta = {
            ...extractionMetaRef.current,
            [id]: { attempted: true, stale: false },
          };
          extractionMetaRef.current = nextMeta;
          setExtractionMeta(nextMeta);
          invalidateAnalysis();
          setEditingInternshipId(id);
          setStatusMessage(
            `Criteria extracted for ${postingLabel(target)}. Review the ledger before analyzing.`,
          );
        }
      } catch (err) {
        if (isAbortError(err)) return;
        setExtractionErrors((prev) => ({ ...prev, [id]: getErrorMessage(err) }));
        setStatusMessage(`Could not extract criteria for ${postingLabel(target)}.`);
      } finally {
        if (extractAborts.current[id] === controller) {
          delete extractAborts.current[id];
          setExtractingIds((prev) => {
            const copy = { ...prev };
            delete copy[id];
            return copy;
          });
        }
      }
    },
    [invalidateAnalysis],
  );

  const toggleInternshipEditor = useCallback((id: string) => {
    setEditingInternshipId((prev) => (prev === id ? null : id));
  }, []);

  const analyze = useCallback(async () => {
    const currentInternships = internshipsRef.current;
    const actionable = currentInternships.filter(isMatchable);

    if (actionable.length === 0) {
      setError("Add a role title and job description for at least one posting before analyzing.");
      return;
    }

    const requestId = ++analysisSeq.current;
    analysisAbort.current?.abort();
    const controller = new AbortController();
    analysisAbort.current = controller;

    setAnalyzing(true);
    setError("");
    setAnalysisResultState(null);
    analysisAbort.current = controller;
    analysisRef.current = null;
    setStatusMessage(
      `Analyzing ${actionable.length} posting${actionable.length === 1 ? "" : "s"}…`,
    );

    const failures: string[] = [];
    const autoExtracted: string[] = [];
    const structuredMap = new Map<string, InternshipDetail>();

    try {
      await Promise.all(
        actionable.map(async (item) => {
          if (item.eligibility_conditions.length > 0 || item.required_skills.length > 0) {
            structuredMap.set(item.id, item);
            return;
          }
          try {
            const data = await extractInternship(
              { title: item.title, company: item.company, description: item.description },
              controller.signal,
            );
            if (data.internship) {
              structuredMap.set(item.id, mergeExtraction(item, data.internship));
              autoExtracted.push(item.id);
            } else {
              structuredMap.set(item.id, item);
            }
          } catch (err) {
            if (isAbortError(err)) throw err;
            failures.push(postingLabel(item));
            structuredMap.set(item.id, item);
          }
        }),
      );

      if (requestId !== analysisSeq.current) return;

      const nextInternships = currentInternships.map(
        (item) => structuredMap.get(item.id) ?? item,
      );
      internshipsRef.current = nextInternships;
      setInternshipsState(nextInternships);

      if (autoExtracted.length > 0) {
        const nextMeta = { ...extractionMetaRef.current };
        for (const id of autoExtracted) {
          nextMeta[id] = { attempted: true, stale: false };
        }
        extractionMetaRef.current = nextMeta;
        setExtractionMeta(nextMeta);
      }

      const postings = nextInternships.filter(isMatchable);
      const data = await matchApi(
        { profile: profileRef.current, internships: postings },
        controller.signal,
      );

      if (requestId !== analysisSeq.current) return;

      analysisRef.current = data;
      setAnalysisResultState(data);
      setActiveTab("all");
      setExpandedCards(
        data.matches?.[0] ? { [data.matches[0].internship_id]: true } : {},
      );

      if (failures.length > 0) {
        setError(
          `Could not auto-extract criteria for ${failures.join(", ")}. Those postings were matched from the description as entered.`,
        );
        setStatusMessage(
          `Analysis complete with ${failures.length} extraction issue${
            failures.length === 1 ? "" : "s"
          }.`,
        );
      } else {
        setStatusMessage(
          `Analysis complete — ${data.matches.length} posting${
            data.matches.length === 1 ? "" : "s"
          } evaluated.`,
        );
      }
    } catch (err) {
      if (requestId !== analysisSeq.current || isAbortError(err)) return;
      setError(getErrorMessage(err));
      setStatusMessage("Analysis failed. Check the service and try again.");
    } finally {
      if (requestId === analysisSeq.current) setAnalyzing(false);
    }
  }, []);

  const toggleExpandCard = useCallback((id: string) => {
    setExpandedCards((prev) => ({ ...prev, [id]: !prev[id] }));
  }, []);

  const openComparison = useCallback(() => {
    if ((analysisRef.current?.matches.length ?? 0) >= 2) setShowComparison(true);
  }, []);

  const closeComparison = useCallback(() => setShowComparison(false), []);

  useEffect(() => {
    if (!analysisResult) setShowComparison(false);
  }, [analysisResult]);

  const matchableCount = internships.filter(isMatchable).length;
  const hasProfileSignal = resumeText.trim().length > 0 || profile.skills.length > 0;
  const isReadyToAnalyze = hasProfileSignal && matchableCount > 0;
  const analyzeBlockedReason = !hasProfileSignal
    ? "Add resume text or at least one skill so there is a profile to evaluate."
    : matchableCount === 0
      ? "Add a role title and job description for at least one posting."
      : "";

  const filteredMatches = useMemo(
    () => filterMatches(analysisResult?.matches ?? [], activeTab),
    [analysisResult, activeTab],
  );

  const tabCounts = useMemo(
    () => ({
      all: countMatches(analysisResult?.matches ?? [], "all"),
      eligible: countMatches(analysisResult?.matches ?? [], "ELIGIBLE"),
      needsConfirmation: countMatches(analysisResult?.matches ?? [], "NEEDS_CONFIRMATION"),
      notEligible: countMatches(analysisResult?.matches ?? [], "NOT_ELIGIBLE"),
    }),
    [analysisResult],
  );

  return {
    resumeText,
    fileName,
    fileSize,
    profile,
    internships,
    analysisResult,
    expandedCards,
    activeTab,
    showComparison,
    editingInternshipId,
    profileEditorOpen,
    newSkillInput,

    resumeBusy,
    parsingText,
    analyzing,
    reanalyzing,
    extractingIds,
    extractionMeta,
    extractionErrors,

    error,
    resumeError,
    parseNotice,
    statusMessage,

    matchableCount,
    isReadyToAnalyze,
    analyzeBlockedReason,
    filteredMatches,
    tabCounts,

    setActiveTab,
    setNewSkillInput,
    setProfileEditorOpen,
    toggleInternshipEditor,

    uploadResume,
    updateResumeText,
    updateProfile,
    updateEducation,
    updatePreferences,
    addCustomSkill,
    removeSkill,
    correctSkill,
    updateInternshipField,
    addInternship,
    removeInternship,
    extractInternshipCriteria,
    analyze,
    toggleExpandCard,
    openComparison,
    closeComparison,
  };
}

export type Workspace = ReturnType<typeof useWorkspace>;
