"use client"

import { KeyboardEvent, useRef, useState } from "react"
import { motion } from "framer-motion"
import { ArrowUp, Square } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"

interface ChatInputProps {
  onSend: (question: string) => void
  isLoading: boolean
  onStop?: () => void
}

const SUGGESTIONS = [
  "What was Interbank's net profit in 2024?",
  "What digital strategy did Scotiabank implement?",
  "What is Interbank's dividend policy?",
  "How do the Peruvian banks manage credit risk?",
]

export function ChatInput({ onSend, isLoading, onStop }: ChatInputProps) {
  const [value, setValue] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    if (!value.trim() || isLoading) return
    onSend(value.trim())
    setValue("")
    textareaRef.current?.focus()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="space-y-3">
      <div className="relative flex items-end gap-2 rounded-2xl border border-zinc-800 bg-zinc-900 p-2 focus-within:border-zinc-700 transition-colors">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the bank annual reports..."
          rows={1}
          className="max-h-40 min-h-[2.5rem] resize-none border-0 bg-transparent p-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus-visible:ring-0 focus-visible:ring-offset-0"
          disabled={isLoading}
        />
        <motion.button
          whileTap={{ scale: 0.92 }}
          onClick={isLoading ? onStop : handleSend}
          disabled={!isLoading && !value.trim()}
          className={`mb-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl transition-colors disabled:opacity-30 ${
            isLoading
              ? "bg-zinc-700 text-zinc-300 hover:bg-zinc-600"
              : "bg-violet-600 text-white hover:bg-violet-500 disabled:hover:bg-violet-600"
          }`}
        >
          {isLoading ? (
            <Square className="h-3.5 w-3.5 fill-current" />
          ) : (
            <ArrowUp className="h-4 w-4" />
          )}
        </motion.button>
      </div>

      {/* Suggestion chips */}
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => { setValue(s); textareaRef.current?.focus() }}
            disabled={isLoading}
            className="rounded-full border border-zinc-800 bg-zinc-900/60 px-3 py-1 text-xs text-zinc-500 transition-colors hover:border-zinc-700 hover:text-zinc-300 disabled:opacity-40"
          >
            {s.length > 42 ? s.slice(0, 42) + "…" : s}
          </button>
        ))}
      </div>
    </div>
  )
}
