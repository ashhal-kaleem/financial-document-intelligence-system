"use client"

import { Cpu, Database, SlidersHorizontal, Trash2 } from "lucide-react"
import { Separator } from "@/components/ui/separator"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { BankFilter } from "@/lib/types"
import { useDocuments } from "@/hooks/useDocuments"
import { DocumentUpload } from "./DocumentUpload"
import { DocumentList } from "./DocumentList"

const MODELS = [
  { value: "qwen3:4b", label: "Qwen3 4B", note: "Fast" },
  { value: "qwen3:8b", label: "Qwen3 8B", note: "Balanced" },
  { value: "qwen3:14b", label: "Qwen3 14B", note: "High quality" },
  { value: "mistral:latest", label: "Mistral 7B", note: "Alternative" },
  { value: "qwen2.5-coder:32b", label: "Qwen2.5 32B", note: "Max power" },
]

const BANKS: { value: BankFilter; label: string; color: string }[] = [
  { value: "all", label: "All banks", color: "bg-zinc-500" },
  { value: "interbank", label: "Interbank", color: "bg-violet-500" },
  { value: "scotiabank", label: "Scotiabank", color: "bg-sky-500" },
]

interface SidebarProps {
  model: string
  onModelChange: (m: string) => void
  bankFilter: BankFilter
  onBankChange: (b: BankFilter) => void
  documentIds: string[] | null
  onDocumentIdsChange: (ids: string[] | null) => void
  topK: number
  onTopKChange: (k: number) => void
  onClear: () => void
  isLoading: boolean
}

export function Sidebar({
  model,
  onModelChange,
  bankFilter,
  onBankChange,
  documentIds,
  onDocumentIdsChange,
  topK,
  onTopKChange,
  onClear,
  isLoading,
}: SidebarProps) {
  const { documents, isUploading, upload, removeDocument } = useDocuments()

  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950 p-4">
      {/* Logo */}
      <div className="mb-6 flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600">
          <Database className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-zinc-100">FinRAG</p>
          <p className="text-xs text-zinc-600">Peru Banking AI</p>
        </div>
      </div>

      <Separator className="mb-5 bg-zinc-800" />

      {/* Controls */}
      <div className="flex flex-1 flex-col gap-5">

        {/* Model */}
        <div className="space-y-2">
          <label className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-zinc-600">
            <Cpu className="h-3.5 w-3.5" /> Model
          </label>
          <Select value={model} onValueChange={(v) => v && onModelChange(v)} disabled={isLoading}>
            <SelectTrigger className="border-zinc-800 bg-zinc-900 text-zinc-200 text-sm focus:ring-violet-500/30">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="border-zinc-800 bg-zinc-900">
              {MODELS.map((m) => (
                <SelectItem
                  key={m.value}
                  value={m.value}
                  className="text-zinc-200 focus:bg-zinc-800"
                >
                  <span className="flex items-center justify-between gap-3 w-full">
                    <span>{m.label}</span>
                    <span className="text-xs text-zinc-500">{m.note}</span>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Bank Filter / Search Scope */}
        <div className="space-y-4">
          <label className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-zinc-600">
            <SlidersHorizontal className="h-3.5 w-3.5" /> Scope
          </label>
          
          <div className="flex flex-col gap-1">
            <button
              onClick={() => {
                onBankChange("all")
                onDocumentIdsChange(null)
              }}
              disabled={isLoading}
              className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors ${
                bankFilter === "all" && documentIds === null
                  ? "bg-zinc-800 text-zinc-100"
                  : "text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300"
              }`}
            >
              <span className={`h-2 w-2 rounded-full bg-zinc-500`} />
              All Documents
            </button>
          </div>

          {documents.filter((d) => !d.is_sample).length > 0 && (
            <div className="flex flex-col gap-1.5 mt-2">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 px-3">
                Uploaded Documents
              </span>
              <DocumentList 
                documents={documents}
                selectedIds={documentIds}
                onSelectionChange={(ids) => {
                  onBankChange("all") // Reset bank filter if custom docs selected
                  onDocumentIdsChange(ids)
                }}
                onDelete={removeDocument}
              />
            </div>
          )}

          <div className="flex flex-col gap-1.5 mt-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 px-3">
              Sample Reports
            </span>
            {BANKS.filter(b => b.value !== "all").map((b) => (
              <button
                key={b.value}
                onClick={() => {
                  onDocumentIdsChange(null)
                  onBankChange(b.value)
                }}
                disabled={isLoading}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors ${
                  bankFilter === b.value && documentIds === null
                    ? "bg-zinc-800 text-zinc-100"
                    : "text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300"
                }`}
              >
                <span className={`h-2 w-2 rounded-full ${b.color}`} />
                {b.label}
              </button>
            ))}
          </div>

          <div className="mt-4">
            <DocumentUpload onUpload={upload} isUploading={isUploading} />
          </div>
        </div>

        {/* Top K */}
        <div className="space-y-2">
          <label className="flex items-center justify-between text-xs font-medium uppercase tracking-wider text-zinc-600">
            <span>Chunks to Retrieve</span>
            <span className="font-mono text-zinc-400">{topK}</span>
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={topK}
            onChange={(e) => onTopKChange(Number(e.target.value))}
            disabled={isLoading}
            className="w-full accent-violet-500"
          />
          <div className="flex justify-between text-xs text-zinc-700">
            <span>1</span>
            <span>10</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-auto pt-4">
        <Separator className="mb-4 bg-zinc-800" />
        <button
          onClick={onClear}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-zinc-600 transition-colors hover:bg-zinc-900 hover:text-zinc-400"
        >
          <Trash2 className="h-4 w-4" />
          Clear conversation
        </button>
      </div>
    </aside>
  )
}
