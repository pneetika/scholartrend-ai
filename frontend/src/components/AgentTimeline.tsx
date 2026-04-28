import SectionCard from "./SectionCard";
import type { AgentTrace } from "../types/api";
import { durationLabel } from "../utils/format";

type AgentTimelineProps = {
  traces: AgentTrace[];
};

function AgentTimeline({ traces }: AgentTimelineProps) {
  return (
    <SectionCard eyebrow="Agent Trace" title="Pipeline activity">
      <div className="timeline">
        {traces.length === 0 ? (
          <p className="muted-copy">Run a workflow to inspect the agent chain.</p>
        ) : (
          traces.map((trace) => (
            <article key={`${trace.name}-${trace.started_at}`} className="timeline-item">
              <div className="timeline-item__header">
                <strong>{trace.name}</strong>
                <span>{durationLabel(trace.started_at, trace.completed_at)}</span>
              </div>
              <p>{trace.summary}</p>
              <ul>
                {trace.steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ul>
            </article>
          ))
        )}
      </div>
    </SectionCard>
  );
}

export default AgentTimeline;

