import { useState } from "react";

import SectionCard from "./SectionCard";
import type { ResearchRequest } from "../types/api";

type ResearchFormProps = {
  activeSessionId?: string;
  isLoading: boolean;
  onSubmit: (payload: ResearchRequest) => Promise<void>;
};

function ResearchForm({ activeSessionId, isLoading, onSubmit }: ResearchFormProps) {
  const [query, setQuery] = useState(
    "What recent topics are researchers actively exploring in NLP around reasoning, tool use, and retrieval-augmented generation?",
  );
  const [goals, setGoals] = useState(
    "Identify the strongest recent subtopics\nHighlight representative papers\nSummarize open problems",
  );
  const [context, setContext] = useState(
    "Target audience: hiring managers and NLP researchers reviewing a portfolio project about LLMs, RAG, and multi-agent systems.",
  );
  const [includeWebSearch, setIncludeWebSearch] = useState(true);
  const [topK, setTopK] = useState(4);
  const [recencyDays, setRecencyDays] = useState(365);

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSubmit({
      session_id: activeSessionId,
      query,
      goals: goals
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean),
      context,
      include_web_search: includeWebSearch,
      top_k: topK,
      recency_days: recencyDays,
    });
  };

  return (
    <SectionCard eyebrow="Research Run" title="Launch a brief">
      <form className="stack-form" onSubmit={submit}>
        <label>
          Research Question
          <textarea value={query} onChange={(event) => setQuery(event.target.value)} rows={4} />
        </label>

        <label>
          Goals
          <textarea
            value={goals}
            onChange={(event) => setGoals(event.target.value)}
            rows={3}
            placeholder="One objective per line"
          />
        </label>

        <label>
          Context
          <textarea
            value={context}
            onChange={(event) => setContext(event.target.value)}
            rows={3}
          />
        </label>

        <div className="inline-controls">
          <label className="toggle">
            <input
              type="checkbox"
              checked={includeWebSearch}
              onChange={(event) => setIncludeWebSearch(event.target.checked)}
            />
            Search scholarly APIs
          </label>

          <label className="slider-control">
            Retrieval depth
            <input
              type="range"
              min={2}
              max={8}
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
            <span>{topK}</span>
          </label>
        </div>

        <label>
          Recency window (days)
          <input
            className="number-input"
            type="number"
            min={30}
            max={3650}
            value={recencyDays}
            onChange={(event) => setRecencyDays(Number(event.target.value) || 365)}
          />
        </label>

        <button className="primary-button" type="submit" disabled={isLoading}>
          {isLoading ? "Researching..." : "Run NLP Research Workflow"}
        </button>
      </form>
    </SectionCard>
  );
}

export default ResearchForm;
