"use client"

import { useState, useEffect, useCallback } from "react"
import { DocumentItem } from "@/lib/types"
import { fetchDocuments, uploadDocument, deleteDocument as apiDeleteDocument } from "@/lib/api"

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  const loadDocuments = useCallback(async () => {
    try {
      const res = await fetchDocuments()
      setDocuments(res.documents)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDocuments()
  }, [loadDocuments])

  // Poll for documents that are processing
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === "processing")
    if (!hasProcessing) return

    const interval = setInterval(() => {
      loadDocuments()
    }, 3000) // Poll every 3 seconds

    return () => clearInterval(interval)
  }, [documents, loadDocuments])

  const upload = async (file: File) => {
    if (file.type !== "application/pdf") {
      throw new Error("Only PDF files are allowed")
    }
    if (file.size > 50 * 1024 * 1024) {
      throw new Error("File size must be less than 50MB")
    }

    setIsUploading(true)
    setError(null)
    try {
      await uploadDocument(file)
      await loadDocuments()
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Upload failed"
      setError(msg)
      throw err
    } finally {
      setIsUploading(false)
    }
  }

  const removeDocument = async (id: string) => {
    try {
      await apiDeleteDocument(id)
      setDocuments((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete document")
      throw err
    }
  }

  return {
    documents,
    isLoading,
    error,
    isUploading,
    upload,
    removeDocument,
    refresh: loadDocuments,
  }
}
