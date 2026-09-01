import { TrendingUp } from "lucide-react"

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-500/10 text-violet-400">
        <TrendingUp className="h-7 w-7" />
      </div>
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-zinc-200">
          Financial RAG Assistant
        </h2>
        <p className="max-w-sm text-sm text-zinc-500">
          Consulta las memorias anuales de Interbank y Scotiabank Perú 2025.
          Las respuestas incluyen citas exactas con número de página.
        </p>
      </div>
      <div className="flex gap-3 text-xs text-zinc-600">
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-violet-500" />
          Interbank 2025
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-sky-500" />
          Scotiabank Perú 2025
        </span>
      </div>
    </div>
  )
}
