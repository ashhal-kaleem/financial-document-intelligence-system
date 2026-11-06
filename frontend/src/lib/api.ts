export interface DocumentItem {
  id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  status: "uploaded" | "queued" | "processing" | "deleting" | "ready" | "error";
  error_message?: string | null;
  is_sample?: boolean;
  created_at: string;
}

export interface CitationItem {
  citation_id: number;
  document_id: string;
  filename: string;
  page: number;
  chunk_index: number;
  total_chunks: number;
  similarity: number;
  snippet: string;
}

export interface DocumentChunkItem {
  id?: number;
  document_id: string;
  content: string;
  source: string;
  page: number;
  chunk_index: number;
  total_chunks: number;
  metadata?: Record<string, any>;
  similarity?: number;
}

export interface StreamEventPayload {
  event: "stage" | "citations" | "token" | "done" | "error";
  stage?: string;
  detail?: string;
  citations?: CitationItem[];
  token?: string;
  finish_reason?: string;
  stream_chunks?: number;
  citations_count?: number;
}

import { getAccessToken } from "@/lib/supabase";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class AuthRequiredError extends Error {
  constructor() {
    super("Sign in to continue.");
    this.name = "AuthRequiredError";
  }
}

/** Authorization header from the live Supabase session. Throws if nobody is signed in. */
async function authHeaders(extra: Record<string, string> = {}): Promise<Record<string, string>> {
  const token = await getAccessToken();
  if (!token) throw new AuthRequiredError();
  return { ...extra, Authorization: `Bearer ${token}` };
}

export async function fetchDocuments(): Promise<DocumentItem[]> {
  if (!(await getAccessToken())) return [];
  const res = await fetch(`${API_BASE}/documents`, { cache: "no-store", headers: await authHeaders() });
  if (!res.ok) throw new Error(res.status === 401 ? "Your session expired. Sign in again." : "Documents could not load. The Free server may be waking up; retry shortly.");
  const json = await res.json();
  return json.data || [];
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/documents`, { method: "POST", body: formData, headers: await authHeaders() });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || err?.detail || "Upload failed.");
  }
  const json = await res.json();
  return json.data;
}

export async function deleteDocument(id: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/documents/${id}`, { method: "DELETE", headers: await authHeaders() });
  if (!res.ok) throw new Error(res.status === 409 ? "Document is busy processing. Wait and retry deletion." : res.status === 401 ? "Your session expired. Sign in again before retrying deletion." : "Delete failed. Please retry. The document has not been confirmed deleted.");
  return true;
}

/** Fetches the PDF with the user's token and returns a local blob URL (iframes cannot send headers). */
export async function fetchDocumentPdfBlobUrl(documentId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/pdf`, { headers: await authHeaders() });
  if (!res.ok) throw new Error("Could not load this document.");
  return URL.createObjectURL(await res.blob());
}

export async function fetchDocumentChunks(documentId: string): Promise<DocumentChunkItem[]> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/chunks`, { cache: "no-store", headers: await authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch chunks.");
  const json = await res.json();
  return json.data || [];
}

export async function fetchAskContext(
  question: string,
  documentIds?: string[]
): Promise<{ messages: Array<{ role: string; content: string }>; citations: CitationItem[]; chunks_count: number }> {
  const res = await fetch(`${API_BASE}/ask/context`, {
    method: "POST",
    headers: await authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ question, document_ids: documentIds && documentIds.length > 0 ? documentIds : null }),
  });
  if (!res.ok) throw new Error("Failed to fetch ask context.");
  const json = await res.json();
  return json.data;
}

export async function streamQuestion(
  question: string,
  documentIds: string[],
  model?: string,
  onEvent?: (event: StreamEventPayload) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE}/ask/stream`, {
    method: "POST",
    headers: await authHeaders({ "Content-Type": "application/json", Accept: "text/event-stream" }),
    body: JSON.stringify({ question, document_ids: documentIds.length > 0 ? documentIds : null, model: model || null }),
    signal,
  });

  if (!response.ok || !response.body) throw new Error(`Stream failed: ${response.status}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  let completed = false;
  try {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";
    for (const block of lines) {
      const trimmed = block.trim();
      if (!trimmed || !trimmed.startsWith("data: ")) continue;
      const dataStr = trimmed.slice(6).trim();
      if (dataStr === "[DONE]") {
        if (!completed) throw new Error("Answer stream ended before completion.");
        return;
      }
      let parsed: StreamEventPayload;
      try { parsed = JSON.parse(dataStr); }
      catch { throw new Error("Invalid answer stream."); }
      if (parsed.event === "error") throw new Error(parsed.detail || "Answer failed.");
      if (parsed.event === "done") completed = true;
      if (onEvent) onEvent(parsed);

    }
  }
  throw new Error("Answer stream was interrupted. Please retry.");
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
}

export async function fetchHealth(): Promise<{ status: string; latency_ms: number }> {
  try {
    const t0 = performance.now();
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    const t1 = performance.now();
    return { status: res.ok ? "healthy" : "degraded", latency_ms: Math.round(t1 - t0) };
  } catch {
    return { status: "offline", latency_ms: 0 };
  }
}
