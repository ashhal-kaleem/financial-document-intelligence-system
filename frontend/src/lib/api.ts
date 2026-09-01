import { AskRequest, AskResponse, HealthResponse, ModelsResponse, DocumentListResponse, UploadResponse } from "./types"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function ask(req: AskRequest): Promise<AskResponse> {
  const res = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }))
    throw new Error(error.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export async function askStream(
  req: AskRequest,
  onToken: (token: string) => void,
  onDone: (response: AskResponse) => void,
  onError: (err: string) => void,
): Promise<void> {
  try {
    const res = await fetch(`${BASE_URL}/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    })
    if (!res.ok || !res.body) {
      const error = await res.json().catch(() => ({ detail: "Stream error" }))
      onError(error.detail ?? `HTTP ${res.status}`)
      return
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ""

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n")
      buffer = lines.pop() ?? ""

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim()
          if (!data || data === "[DONE]") continue
          try {
            const parsed = JSON.parse(data)
            if (parsed.token !== undefined) onToken(parsed.token)
            if (parsed.done) onDone(parsed as AskResponse)
          } catch {}
        }
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err.message : "Network error")
  }
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/health`)
  return res.json()
}

export async function fetchModels(): Promise<ModelsResponse> {
  const res = await fetch(`${BASE_URL}/models`)
  return res.json()
}

export async function fetchDocuments(): Promise<DocumentListResponse> {
  const res = await fetch(`${BASE_URL}/documents`)
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`)
  }
  return res.json()
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append("file", file)
  const res = await fetch(`${BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Upload failed" }))
    throw new Error(error.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/documents/${documentId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`)
  }
}
