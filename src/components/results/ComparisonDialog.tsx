import { useEffect, useRef } from "react";
import type { MouseEvent } from "react";
import { X } from "lucide-react";

import { ComparisonTable } from "./ComparisonTable";
import { Button } from "../ui/Button";
import { IconButton } from "../ui/IconButton";
import type { InternshipDetail, MatchResponse } from "../../types";

type ComparisonDialogProps = {
  open: boolean;
  result: MatchResponse;
  internships: InternshipDetail[];
  onClose: () => void;
};

export function ComparisonDialog({ open, result, internships, onClose }: ComparisonDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    return () => {
      const dialog = dialogRef.current;
      if (dialog?.open) dialog.close();
    };
  }, []);

  const handleBackdropClick = (event: MouseEvent<HTMLDialogElement>) => {
    if (event.target === dialogRef.current) onClose();
  };

  return (
    <dialog
      ref={dialogRef}
      className="comparison-dialog"
      aria-labelledby="comparison-title"
      onClose={onClose}
      onClick={handleBackdropClick}
    >
      <div className="comparison-dialog__panel">
        <header className="comparison-dialog__head">
          <div>
            <p className="mono comparison-dialog__kicker">AUDIT COMPARISON</p>
            <h2 id="comparison-title">Side-by-side opportunity comparison</h2>
            <p className="comparison-dialog__subtitle">
              Compare eligibility, score components, terms, and warnings across postings.
            </p>
          </div>
          <IconButton
            label="Close comparison"
            icon={<X size={18} />}
            onClick={onClose}
            className="comparison-dialog__close"
          />
        </header>

        <div className="comparison-dialog__body">
          <ComparisonTable result={result} internships={internships} />
        </div>

        <footer className="comparison-dialog__foot">
          <p>
            Warnings are cues to verify, not conclusions about an organisation. Press Escape or
            close to return to the matchboard.
          </p>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close comparison
          </Button>
        </footer>
      </div>
    </dialog>
  );
}
