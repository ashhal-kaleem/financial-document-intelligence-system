"use client"

import { motion } from "framer-motion"
import { FileText } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface CitationCardProps {
  citation: string
  score: number
  index: number
}

export function CitationCard({ citation, score, index }: CitationCardProps) {
  const scorePercent = Math.round(score * 100)
  const scoreColor =
    score >= 0.8
      ? "text-emerald-400"
      : score >= 0.65
        ? "text-amber-400"
        : "text-zinc-400"

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.06, duration: 0.25 }}
      className="flex items-start gap-3 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2.5 text-sm"
    >
      <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded bg-violet-500/15 text-violet-400">
        <FileText className="h-3 w-3" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs text-zinc-300">{citation}</p>
      </div>
      <Badge
        variant="outline"
        className={`shrink-0 border-zinc-700 text-xs font-mono ${scoreColor}`}
      >
        {scorePercent}%
      </Badge>
    </motion.div>
  )
}
