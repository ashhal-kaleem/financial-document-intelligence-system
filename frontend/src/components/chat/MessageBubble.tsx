"use client"

import { motion } from "framer-motion"
import { Bot, User, Copy, Check, AlertCircle } from "lucide-react"
import { useState } from "react"
import { CitationCard } from "./CitationCard"
import { LatencyBar } from "./LatencyBar"
import { Message } from "@/lib/types"

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === "user"
  const { response } = message

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      {/* Avatar */}
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? "bg-violet-600 text-white"
            : "bg-zinc-800 text-zinc-300"
        }`}
      >
        {isUser ? (
          <User className="h-4 w-4" />
        ) : (
          <Bot className="h-4 w-4" />
        )}
      </div>

      {/* Content */}
      <div className={`flex max-w-[82%] flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "rounded-tr-sm bg-violet-600 text-white"
              : "rounded-tl-sm bg-zinc-900 text-zinc-100 border border-zinc-800"
          }`}
        >
          {message.content || (
            <span className="flex items-center gap-1.5 text-zinc-500">
              <span className="inline-flex gap-0.5">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="h-1.5 w-1.5 rounded-full bg-zinc-500"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                  />
                ))}
              </span>
              Thinking...
            </span>
          )}

          {/* Streaming cursor */}
          {message.isStreaming && message.content && (
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.5, repeat: Infinity }}
              className="ml-0.5 inline-block h-3.5 w-0.5 bg-zinc-300"
            />
          )}
        </div>

        {/* Assistant extras */}
        {!isUser && response && (
          <div className="w-full space-y-3">
            {/* Not grounded warning */}
            {!response.is_grounded && (
              <div className="flex items-center gap-2 text-xs text-amber-400/80">
                <AlertCircle className="h-3.5 w-3.5" />
                No information found in the indexed documents
              </div>
            )}

            {/* Citations */}
            {response.citations.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-medium uppercase tracking-wider text-zinc-600">
                  Sources
                </p>
                {response.citations.map((citation, i) => (
                  <CitationCard
                    key={i}
                    citation={citation}
                    score={response.retrieval_scores[i] ?? 0}
                    index={i}
                  />
                ))}
              </div>
            )}

            {/* Latency bar */}
            <LatencyBar response={response} />
          </div>
        )}

        {/* Copy button for assistant messages */}
        {!isUser && !message.isStreaming && message.content && (
          <button
            onClick={copyToClipboard}
            className="flex items-center gap-1 text-xs text-zinc-600 transition-colors hover:text-zinc-400"
          >
            {copied ? (
              <><Check className="h-3 w-3" /> Copied</>
            ) : (
              <><Copy className="h-3 w-3" /> Copy</>
            )}
          </button>
        )}
      </div>
    </motion.div>
  )
}
