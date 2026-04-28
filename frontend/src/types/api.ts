export type DocumentRecord = {
  document_id: string;
  filename: string;
  content_type: string;
  uploaded_at: string;
  chunk_count: number;
};

export type MemoryEntry = {
  role: string;
  content: string;
  created_at: string;
};

export type ResearchSource = {
  source_id: string;
  title: string;
  snippet: string;
  url?: string | null;
  source_type: string;
  provider: string;
  authors: string[];
  venue?: string | null;
  published_at?: string | null;
  citation_count?: number | null;
  doi?: string | null;
  paper_id?: string | null;
  relevance_score?: number | null;
  keywords: string[];
};

export type TopicInsight = {
  topic: string;
  trend_signal: string;
  summary: string;
  supporting_source_ids: string[];
};

export type AgentTrace = {
  name: string;
  status: string;
  summary: string;
  steps: string[];
  started_at: string;
  completed_at: string;
};

export type EvaluationMetrics = {
  citation_density: number;
  evidence_coverage: number;
  critique_score: number;
  overall_score: number;
  notes: string[];
};

export type ResearchRequest = {
  session_id?: string;
  query: string;
  goals: string[];
  context?: string;
  include_web_search: boolean;
  top_k: number;
  recency_days: number;
};

export type ResearchResponse = {
  run_id: string;
  session_id: string;
  executive_summary: string;
  report_markdown: string;
  plan: string[];
  topic_map: TopicInsight[];
  key_findings: string[];
  risks: string[];
  next_steps: string[];
  sources: ResearchSource[];
  agent_traces: AgentTrace[];
  evaluation: EvaluationMetrics;
  memory_snapshot: MemoryEntry[];
};

export type RecentRun = {
  run_id: string;
  session_id: string;
  query: string;
  executive_summary: string;
  created_at: string;
};
