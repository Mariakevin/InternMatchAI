import type { ReactNode } from "react";

export function SectionHeading({
  id,
  index,
  title,
  description,
  action,
}: {
  id?: string;
  index: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="section-heading">
      <div className="section-heading__text">
        <span className="section-heading__index mono">{index} —</span>
        <h2 id={id}>{title}</h2>
        {description ? <p className="section-heading__desc">{description}</p> : null}
      </div>
      {action ? <div className="section-heading__action">{action}</div> : null}
    </div>
  );
}
