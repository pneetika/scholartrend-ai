import { useEffect, useState } from "react";

import {
  getMemory,
  listDocuments,
  listRecentRuns,
  runResearch,
  uploadDocument,
} from "./api/client";
import AgentTimeline from "./components/AgentTimeline";
import DocumentLibrary from "./components/DocumentLibrary";
import EvaluationPanel from "./components/EvaluationPanel";
import Header from "./components/Header";
import MemoryPanel from "./components/MemoryPanel";
import ReportPanel from "./components/ReportPanel";
import ResearchForm from "./components/ResearchForm";
import UploadPanel from "./components/UploadPanel";
import type { DocumentRecord, MemoryEntry, RecentRun, ResearchRequest, ResearchResponse } from "./types/api";

function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [recentRuns, setRecentRuns] = useState<RecentRun[]>([]);
  const [memory, setMemory] = useState<MemoryEntry[]>([]);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    if (!result?.session_id) {
      return;
    }
    void hydrateMemory(result.session_id);
  }, [result?.session_id]);

  async function bootstrap() {
    try {
      const [docs, runs] = await Promise.all([listDocuments(), listRecentRuns()]);
      setDocuments(docs);
      setRecentRuns(runs);
    } catch (caughtError) {
      setError(getMessage(caughtError));
    }
  }

  async function hydrateMemory(sessionId: string) {
    try {
      const snapshot = await getMemory(sessionId);
      setMemory(snapshot);
    } catch (caughtError) {
      setError(getMessage(caughtError));
    }
  }

  async function handleUpload(file: File) {
    setError(null);
    setIsUploading(true);
    try {
      const document = await uploadDocument(file);
      setDocuments((current) => [document, ...current]);
    } catch (caughtError) {
      setError(getMessage(caughtError));
    } finally {
      setIsUploading(false);
    }
  }

  async function handleResearch(payload: ResearchRequest) {
    setError(null);
    setIsLoading(true);
    try {
      const nextResult = await runResearch(payload);
      setResult(nextResult);
      const runs = await listRecentRuns();
      setRecentRuns(runs);
    } catch (caughtError) {
      setError(getMessage(caughtError));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="background-orbit background-orbit--left" />
      <div className="background-orbit background-orbit--right" />

      <main className="page">
        <Header
          documentCount={documents.length}
          runCount={recentRuns.length}
          latestScore={result?.evaluation.overall_score}
        />

        {error ? <div className="error-banner">{error}</div> : null}

        <div className="dashboard-grid">
          <div className="dashboard-column">
            <ResearchForm
              activeSessionId={result?.session_id}
              isLoading={isLoading}
              onSubmit={handleResearch}
            />
            <UploadPanel isUploading={isUploading} onUpload={handleUpload} />
            <DocumentLibrary documents={documents} />
          </div>

          <div className="dashboard-column dashboard-column--wide">
            <ReportPanel result={result} />
            <AgentTimeline traces={result?.agent_traces ?? []} />
          </div>

          <div className="dashboard-column">
            <EvaluationPanel evaluation={result?.evaluation ?? null} />
            <MemoryPanel memory={memory} recentRuns={recentRuns} />
          </div>
        </div>
      </main>
    </div>
  );
}

function getMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong while talking to the API.";
}

export default App;

