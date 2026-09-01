"use client"

import { useCallback, useRef, useState } from "react"
import { askStream } from "@/lib/api"
import { AskResponse, BankFilter, ConversationMessage, Message } from "@/lib/types"

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [model, setModel] = useState("llama-3.1-8b-instant")
  const [bankFilter, setBankFilter] = useState<BankFilter>("all")
  const [documentIds, setDocumentIds] = useState<string[] | null>(null)
  const [topK, setTopK] = useState(5)
  const abortRef = useRef(false)

  const sendMessage = useCallback(
    async (question: string) => {
      if (!question.trim() || isLoading) return

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: question,
        timestamp: new Date(),
      }

      const assistantId = crypto.randomUUID()
      const assistantMsg: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isStreaming: true,
      }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      setIsLoading(true)
      abortRef.current = false

      // Build history from completed messages only (exclude the new streaming one)
      const history: ConversationMessage[] = messages
        .filter((m) => !m.isStreaming && m.content)
        .map((m) => ({ role: m.role, content: m.content }))

      await askStream(
        {
          question,
          top_k: topK,
          source_filter: bankFilter === "all" ? null : bankFilter,
          document_ids: documentIds,
          model,
          history,
        },
        (token) => {
          if (abortRef.current) return
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + token } : m,
            ),
          )
        },
        (response: AskResponse) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, response, isStreaming: false, content: response.answer }
                : m,
            ),
          )
          setIsLoading(false)
        },
        (err) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: `Error: ${err}`, isStreaming: false }
                : m,
            ),
          )
          setIsLoading(false)
        },
      )
    },
    [isLoading, model, bankFilter, topK, documentIds, messages],
  )

  const clearMessages = useCallback(() => {
    abortRef.current = true
    setMessages([])
    setIsLoading(false)
  }, [])

  return {
    messages,
    isLoading,
    model,
    setModel,
    bankFilter,
    setBankFilter,
    documentIds,
    setDocumentIds,
    topK,
    setTopK,
    sendMessage,
    clearMessages,
  }
}
