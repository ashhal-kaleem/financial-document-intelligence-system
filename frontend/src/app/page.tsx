"use client"

import { useEffect, useRef } from "react"
import { Sidebar } from "@/components/sidebar/Sidebar"
import { MessageBubble } from "@/components/chat/MessageBubble"
import { ChatInput } from "@/components/chat/ChatInput"
import { EmptyState } from "@/components/chat/EmptyState"
import { useChat } from "@/hooks/useChat"

export default function Home() {
  const {
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
  } = useChat()

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100">
      <Sidebar
        model={model}
        onModelChange={setModel}
        bankFilter={bankFilter}
        onBankChange={setBankFilter}
        documentIds={documentIds}
        onDocumentIdsChange={setDocumentIds}
        topK={topK}
        onTopKChange={setTopK}
        onClear={clearMessages}
        isLoading={isLoading}
      />

      {/* Main chat area */}
      <main className="flex flex-1 flex-col overflow-hidden">
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6">
          <div className="mx-auto max-w-2xl space-y-6">
            {messages.length === 0 ? (
              <EmptyState />
            ) : (
              messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input */}
        <div className="border-t border-zinc-800 px-4 py-4">
          <div className="mx-auto max-w-2xl">
            <ChatInput
              onSend={sendMessage}
              isLoading={isLoading}
            />
            <p className="mt-2 text-center text-xs text-zinc-700">
              Enter para enviar · Shift+Enter para nueva línea
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
