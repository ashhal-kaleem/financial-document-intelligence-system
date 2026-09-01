export interface ConversationMessage {
  role: "user" | "assistant"
  content: string
}

export interface AskRequest {
  question: string
  top_k?: number
  source_filter?: string | null
  document_ids?: string[] | null
  model?: string
  history?: ConversationMessage[]
}

export interface AskResponse {
  answer: string
  query: string
  citations: string[]
  retrieval_scores: number[]
  chunks_used: number
  model: string
  retrieval_ms: number
  generation_ms: number
  total_ms: number
  is_grounded: boolean
}

export interface HealthResponse {
  status: string
  model: string
  store_chunks: number
  store_path: string
}

export interface ModelsResponse {
  available: string[]
  current: string
}

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  response?: AskResponse
  isStreaming?: boolean
}

export type BankFilter = "all" | "interbank" | "scotiabank"

export interface DocumentItem {
  id: string
  filename: string
  status: "processing" | "ready" | "error"
  is_sample: boolean
  chunk_count: number | null
  page_count: number | null
  error_message: string | null
  created_at: string
}

export interface DocumentListResponse {
  documents: DocumentItem[]
}

export interface UploadResponse {
  document_id: string
  filename: string
  status: string
}
