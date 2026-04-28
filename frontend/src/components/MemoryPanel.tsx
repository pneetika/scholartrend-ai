import SectionCard from "./SectionCard";
import type { MemoryEntry, RecentRun } from "../types/api";
import { formatDate } from "../utils/format";

type MemoryPanelProps = {
  memory: MemoryEntry[];
  recentRuns: RecentRun[];
};

function MemoryPanel({ memory, recentRuns }: MemoryPanelProps) {
  return (
    <SectionCard eyebrow="Memory" title="Session memory & history">
      <div className="memory-grid">
        <div>
          <h3>Session memory</h3>
          <div className="list-stack">
            {memory.length === 0 ? (
              <p className="muted-copy">No active session memory yet.</p>
            ) : (
              memory.map((item) => (
                <article key={`${item.role}-${item.created_at}`} className="memory-bubble">
                  <span>{item.role}</span>
                  <p>{item.content}</p>
                </article>
              ))
            )}
          </div>
        </div>

        <div>
          <h3>Recent runs</h3>
          <div className="list-stack">
            {recentRuns.length === 0 ? (
              <p className="muted-copy">No research runs yet.</p>
            ) : (
              recentRuns.map((run) => (
                <article key={run.run_id} className="list-row list-row--stacked">
                  <div>
                    <strong>{run.query}</strong>
                    <p>{run.executive_summary}</p>
                  </div>
                  <time>{formatDate(run.created_at)}</time>
                </article>
              ))
            )}
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

export default MemoryPanel;

