import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state__ghosts" aria-hidden="true">
        {[0, 1, 2].map((row) => (
          <span key={row} className="empty-state__ghost" />
        ))}
      </div>
      <div className="empty-state__copy">
        <strong>{title}</strong>
        <p>{description}</p>
        {action ? <div className="empty-state__action">{action}</div> : null}
      </div>
    </div>
  );
}
