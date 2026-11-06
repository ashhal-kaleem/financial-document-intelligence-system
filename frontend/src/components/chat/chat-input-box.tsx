"use client";

import { useCallback } from "react";
import { ArrowUp, Loader2, Sparkles, FileText } from "lucide-react";
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

export function ChatInputBox({
  onSend,
  isStreaming,
  disabled = false,
  onDocumentUploaded,
  draft,
  setDraft,
  hero = false,
}: ChatInputBoxProps) {
  const selectedDocument = useFDISStore((s) => s.selectedDocument);

  const handleSubmit = useCallback(() => {
    const trimmed = draft.trim();
    if (!trimmed || isStreaming || disabled) return;
    onSend(trimmed);
  }, [draft, isStreaming, disabled, onSend]);

  return (
    <div className={cn("w-full", hero && "max-w-3xl")}>
      <div
        className="rounded-[22px] bg-white p-2.5"
        style={{
          border: "1px solid #ECE8F6",
          boxShadow: hero ? "0 12px 40px #4C1D9514" : "0 6px 20px #4C1D9508",
        }}
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
          placeholder={
            selectedDocument
              ? `Ask about ${selectedDocument.filename}...`
              : "Ask about your filings..."
          }
          rows={hero ? 2 : 1}
          disabled={disabled || isStreaming}
          className="max-h-32 w-full resize-none bg-transparent px-3 py-2 text-[13.5px] text-[#0A0A0A] placeholder:text-[#A999C4] focus:outline-none"
        />
        <div className="flex flex-wrap items-center justify-between gap-2 px-1.5 pb-0.5">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <span className="flex items-center gap-1.5 rounded-full bg-[#F1EDF8] px-3 py-1.5 text-[11px] font-medium text-[#6D5BD0]">
              <Sparkles className="size-3" /> Document Q&A
            </span>
            {selectedDocument && (
              <span className="flex items-center gap-1.5 rounded-full bg-[#F1EDF8] px-2.5 py-1.5 text-[10px] font-medium text-[#6D5BD0]">
                <FileText className="size-3" />
                <span className="max-w-[130px] truncate">
                  {selectedDocument.filename}
                </span>
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleSubmit}
              disabled={!draft.trim() || isStreaming || disabled}
              className="flex size-9 items-center justify-center rounded-full text-white transition-all active:scale-[0.95] disabled:opacity-40"
              style={{
                background: "radial-gradient(closest-side,#C9B6F2,#A284EC)",
              }}
              aria-label="Send message"
            >
              {isStreaming ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <ArrowUp className="size-4" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
