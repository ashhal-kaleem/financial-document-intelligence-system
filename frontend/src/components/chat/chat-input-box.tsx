"use client";

import { useState, useRef, useCallback } from "react";
import { ArrowUp, Loader2, Paperclip, Mic, Sparkles, X, FileText } from "lucide-react";
import { uploadDocument } from "@/lib/api";
import { useFDISStore } from "@/store/useFDISStore";
import { cn } from "@/lib/utils";

interface ChatInputBoxProps {
  onSend: (message: string) => void;
  isStreaming: boolean;
  disabled?: boolean;
  onDocumentUploaded?: () => void;
  draft: string;
  setDraft: (v: string) => void;
  hero?: boolean;
}

export function ChatInputBox({ onSend, isStreaming, disabled = false, onDocumentUploaded, draft, setDraft, hero = false }: ChatInputBoxProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadNote, setUploadNote] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const selectedDocument = useFDISStore((s) => s.selectedDocument);
  const setSelectedDocument = useFDISStore((s) => s.setSelectedDocument);

  const handleSubmit = useCallback(() => {
    const trimmed = draft.trim();
    if (!trimmed || isStreaming || disabled) return;
    onSend(trimmed);
    setDraft("");
  }, [draft, isStreaming, onSend, setDraft]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || file.type !== "application/pdf") return;
    const ownerId = useFDISStore.getState().currentUser?.id;
    if (!ownerId) { useFDISStore.getState().setAuthModalOpen(true); return; }
    setIsUploading(true);
    setUploadNote(null);
    try {
      const doc = await uploadDocument(file);
      if (useFDISStore.getState().currentUser?.id !== ownerId) return;
      if (doc.status === "ready") setSelectedDocument({ id: doc.id, filename: doc.filename });
      setUploadNote(doc.status === "ready" ? `Indexed ${doc.filename}` : `Uploaded ${doc.filename}. Indexing in the background; answers need it to finish.`);
      onDocumentUploaded?.();
      setTimeout(() => setUploadNote(null), 4000);
    } catch (err) {
      if (useFDISStore.getState().currentUser?.id !== ownerId) return;
      setUploadNote(err instanceof Error ? err.message : "Upload failed.");
      setTimeout(() => setUploadNote(null), 6000);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className={cn("w-full", hero && "max-w-3xl")}>
      <div
        className="rounded-[22px] bg-white p-2.5"
        style={{ border: "1px solid #ECE8F6", boxShadow: hero ? "0 12px 40px #4C1D9514" : "0 6px 20px #4C1D9508" }}
      >
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder={selectedDocument ? `Ask about ${selectedDocument.filename}...` : "Ask about your filings..."}
          rows={hero ? 2 : 1}
          disabled={disabled || isStreaming}
          className="max-h-32 w-full resize-none bg-transparent px-3 py-2 text-[13.5px] text-[#0A0A0A] placeholder:text-[#A999C4] focus:outline-none"
        />
        <div className="flex items-center justify-between px-1.5 pb-0.5">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 rounded-full bg-[#F1EDF8] px-3 py-1.5 text-[11px] font-medium text-[#6D5BD0]">
              <Sparkles className="size-3" /> Document Q&A
            </span>
            {selectedDocument && (
              <span className="flex items-center gap-1.5 rounded-full bg-[#F1EDF8] px-2.5 py-1.5 text-[10px] font-medium text-[#6D5BD0]">
                <FileText className="size-3" />
                <span className="max-w-[130px] truncate">{selectedDocument.filename}</span>
                <button onClick={() => setSelectedDocument(null)} aria-label="Clear document scope">
                  <X className="size-3" />
                </button>
              </span>
            )}
            {uploadNote && <span className="text-[10px] text-[#1F8A4C]">{uploadNote}</span>}
          </div>
          <div className="flex items-center gap-1.5">
            <input ref={fileInputRef} type="file" accept=".pdf" className="hidden" onChange={handleFileChange} />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="flex size-9 items-center justify-center rounded-full text-[#A999C4] transition-colors hover:bg-[#F1EDF8] active:scale-[0.95]"
              aria-label="Attach a PDF filing"
            >
              {isUploading ? <Loader2 className="size-4 animate-spin" /> : <Paperclip className="size-4" />}
            </button>
            <button
              onClick={handleSubmit}
              disabled={!draft.trim() || isStreaming || disabled}
              className="flex size-9 items-center justify-center rounded-full text-white transition-all active:scale-[0.95] disabled:opacity-40"
              style={{ background: "radial-gradient(closest-side,#C9B6F2,#A284EC)" }}
              aria-label="Send message"
            >
              {isStreaming ? <Loader2 className="size-4 animate-spin" /> : <ArrowUp className="size-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
