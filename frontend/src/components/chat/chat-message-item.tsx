"use client";

import { useState } from "react";
import { Copy, Check, ArrowUpRight } from "lucide-react";
import { Orb } from "@/components/shell/orbs";
import { AvatarCircle } from "@/components/shell/app-chrome";
import { useFDISStore, Citation } from "@/store/useFDISStore";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timestamp?: string;
}

interface ChatMessageItemProps {
  message: ChatMessage;
  onCitationClick?: (citation: Citation) => void;
}

export function ChatMessageItem({ message, onCitationClick }: ChatMessageItemProps) {
  const [copied, setCopied] = useState(false);
  const openPdfViewer = useFDISStore((s) => s.openPdfViewer);
  const currentUser = useFDISStore((s) => s.currentUser);
  const isAssistant = message.role === "assistant";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isAssistant) {
    return (
      <div className="flex items-start justify-end gap-3">
        <div className="max-w-[80%] rounded-2xl rounded-tr-md bg-[#141414] px-4 py-3 text-[13px] leading-relaxed text-white">
          {message.content}
        </div>
        <AvatarCircle name={currentUser?.name} className="size-8 shrink-0 text-[10px]" />
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3.5">
      <Orb kind="warm" className="mt-1 size-9 shrink-0" />
      <div className="min-w-0 flex-1">
        <div className="rounded-2xl rounded-tl-md bg-white p-5" style={{ border: "1px solid #F0EEF6", boxShadow: "0 6px 20px #4C1D9508" }}>
          <div className="whitespace-pre-wrap text-[13.5px] leading-relaxed text-[#1A1A1A]">
            {message.content}
          </div>
          {message.citations && message.citations.length > 0 && (
            <div className="mt-3.5 flex flex-wrap gap-1.5">
              {message.citations.map((c, i) => (
                <button
                  key={`${c.document}-${c.page}-${i}`}
                  onClick={() => {
                    onCitationClick?.(c);
                    openPdfViewer({
                      documentId: c.documentId,
                      filename: c.document,
                      pageNumber: c.page,
                      chunkId: c.chunk_id,
                      highlightedText: c.snippet || "",
                    });
                  }}
                  className="flex items-center gap-1 rounded-full bg-[#F1F5F9] px-2.5 py-1 text-[10px] font-medium text-[#5A6474] transition-colors hover:bg-[#E4EBF3] active:scale-[0.98] tabular-nums"
                  title={`Open page ${c.page} in the PDF viewer`}
                >
                  {c.document.replace(/\.pdf$/i, "")} · p.{c.page}
                  <ArrowUpRight className="size-2.5 opacity-60" />
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="mt-1.5 flex items-center gap-2 pl-1">
          <button onClick={handleCopy} className="flex items-center gap-1 text-[10px] text-[#A999C4] hover:text-[#6D5BD0]">
            {copied ? <Check className="size-3" /> : <Copy className="size-3" />} {copied ? "Copied" : "Copy"}
          </button>
          {message.timestamp && (
            <span className="text-[10px] text-[#C7C0D6] tabular-nums">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
