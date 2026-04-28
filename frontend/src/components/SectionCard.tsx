import type { PropsWithChildren, ReactNode } from "react";

type SectionCardProps = PropsWithChildren<{
  eyebrow: string;
  title: string;
  action?: ReactNode;
  className?: string;
}>;

function SectionCard({ eyebrow, title, action, className, children }: SectionCardProps) {
  return (
    <section className={`section-card ${className ?? ""}`.trim()}>
      <div className="section-card__header">
        <div>
          <p className="section-card__eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
        {action}
      </div>
      <div className="section-card__body">{children}</div>
    </section>
  );
}

export default SectionCard;

