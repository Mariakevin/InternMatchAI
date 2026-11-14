import { ArrowRight, ListChecks } from "lucide-react";

import { Spinner } from "./ui/Spinner";

type AnalyzeBarProps = {
  ready: boolean;
  analyzing: boolean;
  blockedReason: string;
  statusMessage: string;
  onAnalyze: () => void;
};

export function AnalyzeBar({
  ready,
  analyzing,
  blockedReason,
  statusMessage,
  onAnalyze,
}: AnalyzeBarProps) {
  return (
    <div className="analyze-bar">
      <div className="analyze-bar__info">
        <p className="analyze-bar__note">
          <ListChecks size={15} aria-hidden="true" />
          <span>Auditable, transparent evaluations — never a black-box probability.</span>
        </p>
        <p className="analyze-bar__reason" id="analyze-help">
          {ready
            ? "Runs eligibility, fit, evidence, gaps, and listing checks across every posting."
            : blockedReason}
        </p>
      </div>

      <div className="analyze-bar__action">
        <p
          className="status-region mono"
          id="analyze-status"
          role="status"
          aria-live="polite"
        >
          {statusMessage}
        </p>
        <button
          type="button"
          className="btn btn--primary analyze-cta"
          onClick={onAnalyze}
          disabled={!ready || analyzing}
          aria-describedby="analyze-help analyze-status"
          aria-busy={analyzing}
        >
          {analyzing ? (
            <>
              <Spinner size={17} />
              <span>Analyzing…</span>
            </>
          ) : (
            <>
              <span>Analyze eligibility &amp; fit</span>
              <ArrowRight size={17} aria-hidden="true" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
