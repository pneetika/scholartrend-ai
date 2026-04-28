import type {
  DocumentRecord,
  MemoryEntry,
  RecentRun,
  ResearchRequest,
  ResearchResponse,
} from "../types/api";

const API_BASE = __APP_API_BASE__;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  const payload = await request<{ documents: DocumentRecord[] }>("/documents");
  return payload.documents;
}

export async function uploadDocument(file: File): Promise<DocumentRecord> {
  const formData = new FormData();
  formData.append("file", file);

  const payload = await request<{ document: DocumentRecord }>("/documents/upload", {
    method: "POST",
    body: formData,
  });

  return payload.document;
}

export async function runResearch(payload: ResearchRequest): Promise<ResearchResponse> {
  return request<ResearchResponse>("/research/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function getMemory(sessionId: string): Promise<MemoryEntry[]> {
  return request<MemoryEntry[]>(`/memory/${sessionId}`);
}

export async function listRecentRuns(): Promise<RecentRun[]> {
  return request<RecentRun[]>("/memory/runs/recent");
}

