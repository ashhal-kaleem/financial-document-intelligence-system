import { TrendingUp } from "lucide-react"

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-500/10 text-violet-400">
        <TrendingUp className="h-7 w-7" />
      </div>
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-zinc-200">
          Financial Document Intelligence System
        </h2>
        <p className="max-w-sm text-sm text-zinc-500">
          Query the 2025 annual reports for Interbank and Scotiabank Peru.
          Answers include exact citations with page numbers.
        </p>
      </div>
      <div className="flex gap-3 text-xs text-zinc-600">
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-violet-500" />
          Interbank 2025
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-sky-500" />
          Scotiabank Peru 2025
        </span>
      </div>
    </div>
  )
}
