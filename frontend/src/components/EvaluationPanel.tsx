import SectionCard from "./SectionCard";
import type { EvaluationMetrics } from "../types/api";
import { formatScore } from "../utils/format";

type EvaluationPanelProps = {
  evaluation: EvaluationMetrics | null;
};

function EvaluationBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="evaluation-bar">
      <div className="evaluation-bar__copy">
        <span>{label}</span>
        <strong>{formatScore(value)}</strong>
      </div>
      <div className="evaluation-bar__track">
        <div className="evaluation-bar__fill" style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  );
}

function EvaluationPanel({ evaluation }: EvaluationPanelProps) {
  return (
    <SectionCard eyebrow="Evaluation" title="Quality signals">
      {!evaluation ? (
        <p className="muted-copy">Evaluation metrics will populate after a research run.</p>
      ) : (
        <div className="evaluation-stack">
          <EvaluationBar label="Overall score" value={evaluation.overall_score} />
          <EvaluationBar label="Citation density" value={evaluation.citation_density} />
          <EvaluationBar label="Evidence coverage" value={evaluation.evidence_coverage} />
          <EvaluationBar label="Critique strength" value={evaluation.critique_score} />
          <ul className="detail-list">
            {evaluation.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      )}
    </SectionCard>
  );
}

export default EvaluationPanel;

