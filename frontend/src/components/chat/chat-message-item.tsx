/**
 * @source shadcn/ui Card + Badge + Avatar + Button (registry-fetched)
 * @audio Puter.js Audio TTS Briefing Engine
 * @icons Lucide React
 * @invariant tabular-nums font-mono
 * @invariant strictly < 150 lines
 */
"use client";

import { Copy, Check, ExternalLink, Volume2, VolumeX, Brain } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { UserAvatar } from "@/components/ui/user-avatar";
import { useFDISStore, Citation } from "@/store/useFDISStore";
import { speakFinancialBriefing } from "@/lib/puter";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timestamp?: string;
  model?: string;
}

interface ChatMessageItemProps {
  message: ChatMessage;
  onCitationClick?: (citation: Citation) => void;
}

export function ChatMessageItem({ message, onCitationClick }: ChatMessageItemProps) {
  const [copied, setCopied] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const openPdfViewer = useFDISStore((s) => s.openPdfViewer);
  const currentUser = useFDISStore((s) => s.currentUser);

  const getModelDisplayName = (modelName?: string) => {
    if (!modelName) return "FDIS Intelligence (Claude 3.5 Sonnet)";
    if (modelName.toLowerCase().includes("gpt-4")) return "FDIS Intelligence (GPT-4o)";
    if (modelName.toLowerCase().includes("claude")) return "FDIS Intelligence (Claude 3.5 Sonnet)";
    return "FDIS Intelligence (" + (modelName || "AI") + ")";
  };
  const isAssistant = message.role === "assistant";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSpeak = async () => {
    if (isPlayingAudio) return;
    setIsPlayingAudio(true);
    await speakFinancialBriefing(message.content);
    setIsPlayingAudio(false);
  };

  return (
    <div className={`group flex gap-3 px-4 py-3 ${isAssistant ? "bg-card/30" : ""}`}>
      {isAssistant ? (
        <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary border border-primary/25">
          <Brain className="size-3.5 text-primary" />
        </div>
      ) : (
        <UserAvatar name={currentUser?.name || "You"} email={currentUser?.email || ""} size="sm" />
      )}

      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium">{isAssistant ? getModelDisplayName(message.model) : (currentUser?.name || "You")}</span>
          {message.timestamp && (
            <span className="text-[10px] text-muted-foreground font-mono tabular-nums">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
        </div>

        <div className="prose prose-sm prose-invert max-w-none text-sm leading-relaxed text-foreground/90">
          {message.content}
        </div>

        {/* Citations Badges */}
        {isAssistant && message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {message.citations.map((c, i) => (
              <Badge
                key={`${c.document}-${c.page}-${i}`}
                variant="secondary"
                className="cursor-pointer gap-1 text-[10px] font-mono tabular-nums transition-colors hover:bg-primary/20 hover:text-primary active:scale-[0.98]"
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
                title={`Click to inspect Page ${c.page} in PDF Viewer`}
              >
                [{i + 1}] p.{c.page}
                <span className="text-muted-foreground">({Math.round(c.relevance * 100)}%)</span>
                <ExternalLink className="size-2.5 opacity-60 ml-0.5" />
              </Badge>
            ))}
          </div>
        )}

        {/* Action bar: Audio Voice Briefing + Copy */}
        {isAssistant && (
          <div className="flex items-center gap-1.5 opacity-0 transition-opacity group-hover:opacity-100 mt-0.5">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-[11px] gap-1 text-muted-foreground hover:text-foreground active:scale-[0.98]"
              onClick={handleSpeak}
              title="Listen to Financial Briefing (Puter Audio TTS)"
            >
              {isPlayingAudio ? <VolumeX className="size-3 text-primary animate-pulse" /> : <Volume2 className="size-3" />}
              <span>{isPlayingAudio ? "Playing..." : "Listen"}</span>
            </Button>

            <Button
              variant="ghost"
              size="icon"
              className="size-6 active:scale-[0.98]"
              onClick={handleCopy}
              aria-label="Copy response"
            >
              {copied ? <Check className="size-3 text-primary" /> : <Copy className="size-3 text-muted-foreground" />}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
