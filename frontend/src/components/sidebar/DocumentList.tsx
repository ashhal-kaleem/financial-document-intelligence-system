"use client"

import { Loader2, Trash2, AlertCircle } from "lucide-react"
import { DocumentItem } from "@/lib/types"

interface DocumentListProps {
  documents: DocumentItem[]
  selectedIds: string[] | null
  onSelectionChange: (ids: string[] | null) => void
  onDelete: (id: string) => void
}

export function DocumentList({
  documents,
  selectedIds,
  onSelectionChange,
  onDelete,
}: DocumentListProps) {
  // Filter out samples to show in "Uploaded Documents" section if we want
  const uploadedDocs = documents.filter((d) => !d.is_sample)
  
  if (uploadedDocs.length === 0) {
    return null
  }

  const toggleSelection = (id: string) => {
    let newSelection: string[]
    if (selectedIds === null) {
      // If currently "All" is selected, selecting a document switches to only that document
      newSelection = [id]
    } else {
      if (selectedIds.includes(id)) {
        newSelection = selectedIds.filter((selId) => selId !== id)
      } else {
        newSelection = [...selectedIds, id]
      }
    }
    
    // If we deselected the last one, go back to "All" (null)
    if (newSelection.length === 0) {
      onSelectionChange(null)
    } else {
      onSelectionChange(newSelection)
    }
  }

  return (
    <div className="flex flex-col gap-1.5 mt-2">
      {uploadedDocs.map((doc) => {
        const isSelected = selectedIds !== null && selectedIds.includes(doc.id)
        
        return (
          <div
            key={doc.id}
            className={`group relative flex items-center gap-3 rounded-lg border px-3 py-2 transition-colors ${
              isSelected
                ? "border-violet-500/30 bg-violet-500/10"
                : "border-transparent hover:bg-zinc-900"
            }`}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => toggleSelection(doc.id)}
              disabled={doc.status !== "ready"}
              className="h-4 w-4 rounded border-zinc-700 bg-zinc-900 accent-violet-500 focus:ring-violet-500/30"
            />
            
            <div className="flex min-w-0 flex-1 flex-col">
              <span className="truncate text-sm font-medium text-zinc-200" title={doc.filename}>
                {doc.filename}
              </span>
              
              <div className="flex items-center gap-1.5 text-xs">
                {doc.status === "processing" && (
                  <span className="flex items-center gap-1 text-sky-400">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Procesando...
                  </span>
                )}
                {doc.status === "error" && (
                  <span className="flex items-center gap-1 text-red-400" title={doc.error_message || ""}>
                    <AlertCircle className="h-3 w-3" />
                    Error
                  </span>
                )}
                {doc.status === "ready" && (
                  <span className="text-zinc-500">
                    {doc.page_count ? `${doc.page_count} páginas` : "Listo"}
                  </span>
                )}
              </div>
            </div>

            <button
              onClick={() => onDelete(doc.id)}
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-zinc-500 opacity-0 transition-all hover:bg-red-500/20 hover:text-red-400 group-hover:opacity-100"
              title="Delete document"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
