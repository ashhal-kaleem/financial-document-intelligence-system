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

import { getAccessToken, getSupabase } from "@/lib/supabase";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class AuthRequiredError extends Error {
  constructor() {
    super("Sign in to continue.");
    this.name = "AuthRequiredError";
  }
}

/** Authorization header from the live Supabase session. Throws if nobody is signed in. */
async function authHeaders(
  extra: Record<string, string> = {},
): Promise<Record<string, string>> {
  const token = await getAccessToken();
  if (!token) throw new AuthRequiredError();
  return { ...extra, Authorization: `Bearer ${token}` };
}

export async function fetchDocuments(): Promise<DocumentItem[]> {
  // Bound both session lookup and the complete HTTP/body read. A stalled request
  // must become a retryable error, never an endless loading or empty-library result.
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout>;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => {
      controller.abort();
      reject(new Error("Documents request timed out. Retry to check your library."));
    }, 45000);
  });
  const request = async () => {
    const token = await getAccessToken();
    if (!token) throw new AuthRequiredError();
    if (controller.signal.aborted) throw new Error("Documents request timed out.");
    const res = await fetch(`${API_BASE}/documents`, {
      cache: "no-store",
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    });
    if (!res.ok)
      throw new Error(
        res.status === 401
          ? "Your session expired. Sign in again."
          : "Documents could not load. Retry to check your library.",
      );
    const json = await res.json();
    if (!Array.isArray(json.data))
      throw new Error("Documents returned an invalid response. Retry to check your library.");
    return json.data as DocumentItem[];
  };
  try {
    return await Promise.race([request(), timeout]);
  } finally {
    clearTimeout(timer!);
  }
}

// Keep in sync with the backend MAX_UPLOAD_SIZE_BYTES for this deployment (4 MB).
export const MAX_UPLOAD_BYTES = 4 * 1024 * 1024;

async function readApiError(res: Response, fallback: string): Promise<Error> {
  const err = await res.json().catch(() => ({}));
  return new Error(err?.error?.message || err?.detail || fallback);
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  // Serverless path: the PDF goes straight from the browser to private Supabase
  // storage on a per-object signed URL; the backend then processes it from
  // storage. Large request bodies never pass through the API host.
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new Error("PDF must be 4 MB or smaller.");
  }
  const headers = await authHeaders();
  const createRes = await fetch(`${API_BASE}/documents/upload-url`, {
    method: "POST",
    headers: { ...headers, "Content-Type": "application/json" },
    body: JSON.stringify({ filename: file.name, size: file.size }),
  });
  if (!createRes.ok) throw await readApiError(createRes, "Upload failed.");
  const created = (await createRes.json()).data;

  const supabase = getSupabase();
  if (!supabase) throw new Error("Sign-in is not configured for this deployment.");
  const put = await supabase.storage
    .from(created.bucket)
    .uploadToSignedUrl(created.path, created.token, file, {
      contentType: "application/pdf",
    });
  if (put.error) throw new Error("Upload to storage failed. Please retry.");

  const ingestRes = await fetch(
    `${API_BASE}/documents/${created.document_id}/ingest`,
    { method: "POST", headers },
  );
  if (!ingestRes.ok) throw await readApiError(ingestRes, "Upload failed.");
  const json = await ingestRes.json();
  return json.data;
}

export async function deleteDocument(id: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/documents/${id}`, {
    method: "DELETE",
    headers: await authHeaders(),
  });
  if (!res.ok)
    throw new Error(
      res.status === 409
        ? "Document is busy processing. Wait and retry deletion."
        : res.status === 401
          ? "Your session expired. Sign in again before retrying deletion."
          : "Delete failed. Please retry. The document has not been confirmed deleted.",
    );
  return true;
}

/** Fetches the PDF with the user's token and returns a local blob URL (iframes cannot send headers). */
export async function fetchDocumentPdfBlobUrl(
  documentId: string,
): Promise<string> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/pdf`, {
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error("Could not load this document.");
  return URL.createObjectURL(await res.blob());
}

export async function fetchDocumentChunks(
  documentId: string,
): Promise<DocumentChunkItem[]> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/chunks`, {
    cache: "no-store",
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch chunks.");
  const json = await res.json();
  return json.data || [];
}

/** Grounded answer from the server: MiniLM retrieval + free Groq model. No browser AI account. */
export async function askAI(
  question: string,
  documentIds: string[],
  onEvent: (event: StreamEventPayload) => void,
  signal: AbortSignal,
): Promise<void> {
  const token = await getAccessToken();
  if (!token) throw new AuthRequiredError();
  const res = await fetch(`${API_BASE}/ask/answer`, {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      question,
      document_ids: documentIds.length ? documentIds : null,
    }),
  });
  if (!res.ok) throw await readApiError(res, "Answer failed. Retry.");
  const data = (await res.json()).data;
  if (typeof data?.answer !== "string")
    throw new Error("Answer returned an invalid response. Retry.");
  onEvent({ event: "citations", citations: data.citations || [] });
  onEvent({ event: "token", token: data.answer });
  onEvent({ event: "done" });
}

/** Deletes every document and the guest identity itself, server-side. */
export async function endSession(): Promise<{
  documents_deleted: number;
  documents_failed: number;
  identity_removed: boolean;
}> {
  const res = await fetch(`${API_BASE}/session`, {
    method: "DELETE",
    headers: await authHeaders(),
  });
  if (!res.ok)
    throw await readApiError(
      res,
      "Session cleanup failed. Retry before leaving this device.",
    );
  return (await res.json()).data;
}

export async function fetchHealth(): Promise<{
  status: string;
  latency_ms: number;
}> {
  try {
    const t0 = performance.now();
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    const t1 = performance.now();
    return {
      status: res.ok ? "healthy" : "degraded",
      latency_ms: Math.round(t1 - t0),
    };
  } catch {
    return { status: "offline", latency_ms: 0 };
  }
}
