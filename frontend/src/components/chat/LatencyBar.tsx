"use client"

import { motion } from "framer-motion"
import { AskResponse } from "@/lib/types"

interface LatencyBarProps {
  response: AskResponse
}

export function LatencyBar({ response }: LatencyBarProps) {
  const total = response.total_ms
  const retrievalPct = (response.retrieval_ms / total) * 100
  const generationPct = (response.generation_ms / total) * 100

  const fmt = (ms: number) =>
    ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`

  return (
    <div className="mt-3 space-y-1.5">
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        <span className="font-mono">{fmt(response.total_ms)} total</span>
        <span>·</span>
        <span className="text-violet-400/80">
          {fmt(response.retrieval_ms)} retrieval
        </span>
        <span>·</span>
        <span className="text-sky-400/80">
          {fmt(response.generation_ms)} generation
        </span>
        <span>·</span>
        <span>{response.chunks_used} chunks</span>
      </div>
      <div className="flex h-1 w-full overflow-hidden rounded-full bg-zinc-800">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${retrievalPct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="h-full bg-violet-500"
        />
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${generationPct}%` }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
          className="h-full bg-sky-500"
        />
      </div>
    </div>
  )
}
