import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import SectionCard from "./SectionCard";
import type { ResearchResponse } from "../types/api";

type ReportPanelProps = {
  result: ResearchResponse | null;
};

function ReportPanel({ result }: ReportPanelProps) {
  return (
    <SectionCard eyebrow="Final Brief" title="Report output" className="report-panel">
      {!result ? (
        <p className="muted-copy">
          Your final brief will appear here after the Planner, Researcher, Critic, and Writer
          finish mapping the recent NLP landscape.
        </p>
      ) : (
        <div className="report-content">
          <p className="lead-summary">{result.executive_summary}</p>
          {result.topic_map.length ? (
            <div className="topic-grid">
              {result.topic_map.map((topic) => (
                <article key={`${topic.topic}-${topic.trend_signal}`} className="topic-card">
                  <div className="topic-card__header">
                    <h3>{topic.topic}</h3>
                    <span>{topic.trend_signal}</span>
                  </div>
                  <p>{topic.summary}</p>
                </article>
              ))}
            </div>
          ) : null}
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.report_markdown}</ReactMarkdown>
        </div>
      )}
    </SectionCard>
  );
}

export default ReportPanel;
