/**
 * @source shadcn/ui Textarea + Button + Badge (registry-fetched)
 * @engine Puter.js Multi-Model Selector (Claude 3.5 Sonnet / GPT-4o / DeepSeek R1)
 * @icons Lucide React
 * @invariant active:scale-[0.98] on send button
 * @invariant strictly < 150 lines
 */
"use client";

import { useState, useRef, useCallback } from "react";
import { Send, Loader2, Sparkles, Cpu } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ChatInputBoxProps {
  onSend: (message: string, model?: string) => void;
  isStreaming: boolean;
  disabled?: boolean;
}

const PUTER_MODELS = [
  { id: "claude-3-5-sonnet", label: "Claude 3.5 Sonnet", badge: "Puter AI" },
  { id: "gpt-4o", label: "GPT-4o", badge: "Puter AI" },
  { id: "deepseek-chat", label: "DeepSeek V3", badge: "Puter AI" },
];

export function ChatInputBox({ onSend, isStreaming, disabled = false }: ChatInputBoxProps) {
  const [input, setInput] = useState("");
  const [selectedModel, setSelectedModel] = useState("claude-3-5-sonnet");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed, selectedModel);
    setInput("");
    textareaRef.current?.focus();
  }, [input, isStreaming, onSend, selectedModel]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  return (
    <div className="border-t border-border/40 bg-card/20 p-4 space-y-2">
      {/* Model Selection Bar */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-1.5">
          <Cpu className="size-3 text-primary" />
          <span className="text-[11px] font-medium text-muted-foreground">Inference Model:</span>
          <div className="flex items-center gap-1">
            {PUTER_MODELS.map((m) => (
              <Button
                key={m.id}
                variant={selectedModel === m.id ? "secondary" : "ghost"}
                size="sm"
                className={`h-6 px-2 text-[10px] active:scale-[0.98] ${
                  selectedModel === m.id ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground"
                }`}
                onClick={() => setSelectedModel(m.id)}
              >
                {m.label}
              </Button>
            ))}
          </div>
        </div>

        <Badge variant="outline" className="text-[10px] font-mono text-emerald-400 border-emerald-500/20 bg-emerald-500/5 hidden sm:inline-flex">
          <Sparkles className="size-2.5 mr-1" /> Zero Groq Limits
        </Badge>
      </div>

      {/* Input Textarea Container */}
      <div className="flex items-end gap-2 rounded-xl border border-border/40 bg-card/60 p-2 backdrop-blur-sm transition-colors focus-within:border-primary/40">
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask complex financial questions, footnote details, or ratio breakdowns..."
          className="min-h-[40px] max-h-[120px] resize-none border-0 bg-transparent p-1.5 text-xs shadow-none focus-visible:ring-0"
          disabled={disabled || isStreaming}
          rows={1}
        />
        <Button
          size="icon"
          className="size-8 shrink-0 rounded-lg active:scale-[0.98] transition-transform duration-75"
          onClick={handleSubmit}
          disabled={!input.trim() || isStreaming || disabled}
          aria-label="Send message"
        >
          {isStreaming ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
        </Button>
      </div>
    </div>
  );
}
