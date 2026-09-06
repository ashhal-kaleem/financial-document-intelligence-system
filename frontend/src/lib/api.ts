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

  const res = await fetch(`${API_BASE}/documents`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    const message = errData?.error?.message || errData?.detail || "Upload failed.";
    throw new Error(message);
  }
  const json = await res.json();
  return json.data;
}

export async function deleteDocument(id: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/documents/${id}`, {
    method: "DELETE",
  });
  return res.ok;
}

export async function streamQuestion(
  question: string,
  documentIds: string[],
  model?: string,
  onEvent?: (event: StreamEventPayload) => void
): Promise<void> {
  const response = await fetch(`${API_BASE}/ask/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "text/event-stream",
    },
    body: JSON.stringify({
      question,
      document_ids: documentIds.length > 0 ? documentIds : null,
      model: model || null,
    }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Streaming failed with status: ${response.status}`);
  }

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
      if (dataStr === "[DONE]") {
        return;
      }
      try {
        const parsed: StreamEventPayload = JSON.parse(dataStr);
        if (onEvent) onEvent(parsed);
      } catch (e) {
        console.error("Failed to parse SSE payload", e);
      }
    }
  }
}

export async function sendEmailAlert(recipient: string, documentName: string, summary: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/notify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      recipient,
      document_name: documentName,
      summary,
    }),
  });
  return res.ok;
}
