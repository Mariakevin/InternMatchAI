import { Edit3 } from "lucide-react";

import { AnalyzeBar } from "./components/AnalyzeBar";
import { InternshipList } from "./components/internships/InternshipList";
import { Hero } from "./components/layout/Hero";
import { SectionHeading } from "./components/layout/SectionHeading";
import { SiteFooter } from "./components/layout/SiteFooter";
import { SiteHeader } from "./components/layout/SiteHeader";
import { SkipLink } from "./components/layout/SkipLink";
import { ProfileEditor } from "./components/profile/ProfileEditor";
import { ProfileSnapshot } from "./components/profile/ProfileSnapshot";
import { ResumeSourceCard } from "./components/profile/ResumeSourceCard";
import { ComparisonDialog } from "./components/results/ComparisonDialog";
import { ResultsSection } from "./components/results/ResultsSection";
import { Alert } from "./components/ui/Alert";
import { Button } from "./components/ui/Button";
import { useWorkspace } from "./hooks/useWorkspace";

export default function App() {
  const workspace = useWorkspace();

  return (
    <div id="top">
      <SkipLink />
      <SiteHeader />

      <main id="main" className="page">
        <Hero />

        <div className="shell">
          <section className="workspace-section" aria-labelledby="profile-heading">
            <SectionHeading
              id="profile-heading"
              index="01"
              title="Your profile & constraints"
              description="Upload or paste a resume, then audit the facts and preferences every decision will use."
              action={
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<Edit3 size={14} />}
                  onClick={() => workspace.setProfileEditorOpen(!workspace.profileEditorOpen)}
                  aria-expanded={workspace.profileEditorOpen}
                  aria-controls="profile-editor"
                >
                  {workspace.profileEditorOpen ? "Close profile editor" : "Review & edit profile"}
                </Button>
              }
            />

            <div className="profile-grid">
              <ResumeSourceCard
                resumeText={workspace.resumeText}
                fileName={workspace.fileName}
                fileSize={workspace.fileSize}
                resumeBusy={workspace.resumeBusy}
                parsingText={workspace.parsingText}
                resumeError={workspace.resumeError}
                parseNotice={workspace.parseNotice}
                onUpload={(file) => {
                  void workspace.uploadResume(file);
                }}
                onTextChange={workspace.updateResumeText}
              />
              <ProfileSnapshot
                profile={workspace.profile}
                editorOpen={workspace.profileEditorOpen}
                onToggleEditor={() => workspace.setProfileEditorOpen(!workspace.profileEditorOpen)}
              />
            </div>

            <ProfileEditor
              open={workspace.profileEditorOpen}
              profile={workspace.profile}
              newSkillInput={workspace.newSkillInput}
              onEducationChange={workspace.updateEducation}
              onPreferencesChange={workspace.updatePreferences}
              onNewSkillChange={workspace.setNewSkillInput}
              onAddSkill={workspace.addCustomSkill}
              onRemoveSkill={workspace.removeSkill}
            />
          </section>

          <section className="workspace-section" aria-labelledby="roles-heading">
            <SectionHeading
              id="roles-heading"
              index="02"
              title="Internship opportunities"
              description="Paste each posting. Auto-extraction turns prose into auditable conditions and skills."
              action={<span className="section-note mono">UP TO 20 POSTINGS</span>}
            />

            <InternshipList
              internships={workspace.internships}
              extractingIds={workspace.extractingIds}
              extractionMeta={workspace.extractionMeta}
              extractionErrors={workspace.extractionErrors}
              editingId={workspace.editingInternshipId}
              onFieldChange={workspace.updateInternshipField}
              onExtract={(id) => {
                void workspace.extractInternshipCriteria(id);
              }}
              onRemove={workspace.removeInternship}
              onToggleEditor={workspace.toggleInternshipEditor}
              onAdd={workspace.addInternship}
            />
          </section>

          {workspace.error ? (
            <Alert tone="fail" title="Analysis issue" className="workspace-alert">
              {workspace.error}
            </Alert>
          ) : null}

          <AnalyzeBar
            ready={workspace.isReadyToAnalyze}
            analyzing={workspace.analyzing}
            blockedReason={workspace.analyzeBlockedReason}
            statusMessage={workspace.statusMessage}
            onAnalyze={() => {
              void workspace.analyze();
            }}
          />
        </div>

        {workspace.analysisResult ? (
          <div className="shell">
            <ResultsSection
              result={workspace.analysisResult}
              internships={workspace.internships}
              activeTab={workspace.activeTab}
              filteredMatches={workspace.filteredMatches}
              counts={workspace.tabCounts}
              expandedCards={workspace.expandedCards}
              correcting={workspace.reanalyzing || workspace.analyzing}
              onTabChange={workspace.setActiveTab}
              onToggleCard={workspace.toggleExpandCard}
              onCorrect={workspace.correctSkill}
              onOpenComparison={workspace.openComparison}
            />
          </div>
        ) : null}
      </main>

      <SiteFooter />

      {workspace.analysisResult ? (
        <ComparisonDialog
          open={workspace.showComparison}
          result={workspace.analysisResult}
          internships={workspace.internships}
          onClose={workspace.closeComparison}
        />
      ) : null}
    </div>
  );
}
