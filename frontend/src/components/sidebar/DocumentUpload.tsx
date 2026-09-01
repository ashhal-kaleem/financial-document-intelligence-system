"use client"

import { useState, useRef } from "react"
import { Upload, Loader2 } from "lucide-react"

interface DocumentUploadProps {
  onUpload: (file: File) => Promise<void>
  isUploading: boolean
}

export function DocumentUpload({ onUpload, isUploading }: DocumentUploadProps) {
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setError(null)
    try {
      await onUpload(file)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed")
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <input
        type="file"
        ref={fileInputRef}
        accept="application/pdf"
        className="hidden"
        onChange={handleFileChange}
        disabled={isUploading}
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading}
        className="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-zinc-700 p-4 text-sm text-zinc-400 transition-colors hover:border-zinc-500 hover:bg-zinc-900 hover:text-zinc-300 disabled:opacity-50 disabled:hover:border-zinc-700 disabled:hover:bg-transparent"
      >
        {isUploading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Subiendo...</span>
          </>
        ) : (
          <>
            <Upload className="h-4 w-4" />
            <span>+ Upload PDF</span>
          </>
        )}
      </button>
      {error && (
        <div className="text-xs text-red-500 bg-red-500/10 p-2 rounded-md border border-red-500/20">
          {error}
        </div>
      )}
    </div>
  )
}
