export interface DocumentItem {
  id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  status: "uploaded" | "processing" | "ready" | "error";
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
  total_tokens?: number;
  citations_count?: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchDocuments(): Promise<DocumentItem[]> {
  const res = await fetch(`${API_BASE}/documents`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch documents.");
  const json = await res.json();
  return json.data || [];
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/documents`, { method: "POST", body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || err?.detail || "Upload failed.");
  }
  const json = await res.json();
  return json.data;
}

export async function deleteDocument(id: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/documents/${id}`, { method: "DELETE" });
  return res.ok;
}

export function getDocumentPdfUrl(documentId: string): string {
  return `${API_BASE}/documents/${documentId}/pdf`;
}

export async function fetchDocumentChunks(documentId: string): Promise<DocumentChunkItem[]> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/chunks`, { cache: "no-store" });
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
    headers: { "Content-Type": "application/json" },
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
    headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
    body: JSON.stringify({ question, document_ids: documentIds.length > 0 ? documentIds : null, model: model || null }),
    signal,
  });

  if (!response.ok || !response.body) throw new Error(`Stream failed: ${response.status}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

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
      if (dataStr === "[DONE]") return;
      try {
        const parsed: StreamEventPayload = JSON.parse(dataStr);
        if (onEvent) onEvent(parsed);
      } catch (e) {
        console.error("SSE parse error", e);
      }
    }
  }
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
