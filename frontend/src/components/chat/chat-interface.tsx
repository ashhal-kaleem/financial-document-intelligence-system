/**
 * @source shadcn/ui ScrollArea (registry-fetched)
 * @engine Puter.js AI Chat (Claude 3.5 Sonnet / GPT-4o) + Puter KV Store
 * @fallback Backend SSE /ask/stream
 * @invariant strictly < 150 lines
 */
"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatEmptyState } from "./chat-empty-state";
import { ChatMessageItem } from "./chat-message-item";
import { ChatInputBox } from "./chat-input-box";
import { LoadingPulseAnimation } from "@/components/ui/lottie-player";
import { useFDISStore, Citation } from "@/store/useFDISStore";
import { fetchAskContext, streamQuestion, StreamEventPayload } from "@/lib/api";
import { streamPuterChat, loadChatHistory, saveChatHistory, PuterChatMessage } from "@/lib/puter";

interface ChatInterfaceProps {
  documentCount: number;
}

export function ChatInterface({ documentCount }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<PuterChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const setActiveCitation = useFDISStore((s) => s.setActiveCitation);

  // Restore persistent conversation from Puter.kv on mount
  useEffect(() => {
    loadChatHistory().then((history) => {
      if (history && history.length > 0) setMessages(history);
    });
  }, []);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = useCallback(async (content: string, model: string = "claude-3-5-sonnet") => {
    const userMsg: PuterChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    const assistantId = `assistant-${Date.now()}`;
    const initialAssistantMsg: PuterChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setIsStreaming(true);

    try {
      // 1. Retrieve RAG context & citations from backend pgvector
      const contextData = await fetchAskContext(content);
      const citations: Citation[] = (contextData.citations || []).map((c) => ({
        document: c.filename,
        page: c.page,
        chunk_id: String(c.chunk_index),
        relevance: c.similarity,
        snippet: c.snippet,
      }));

      // Update citations badge immediately
      setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, citations } : m)));

      // 2. Stream tokens via Puter.js AI (Claude 3.5 Sonnet / GPT-4o)
      let fullContent = "";
      try {
        await streamPuterChat(contextData.messages, model, (token) => {
          fullContent += token;
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: fullContent } : m)));
        });
      } catch (puterErr) {
        // Fallback to backend stream if Puter encounters client error
        await streamQuestion(content, [], undefined, (event: StreamEventPayload) => {
          if (event.event === "token" && event.token) {
            fullContent += event.token;
            setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: fullContent } : m)));
          }
        });
      }

      // 3. Persist conversation into Puter KV store
      setMessages((current) => {
        saveChatHistory(current);
        return current;
      });
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: "Inference engine temporarily unavailable. Please verify connection and retry.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  }, []);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {messages.length === 0 ? (
        <ChatEmptyState documentCount={documentCount} />
      ) : (
        <ScrollArea className="flex-1" ref={scrollRef}>
          <div className="flex flex-col">
            {messages.map((msg) => (
              <ChatMessageItem key={msg.id} message={msg} onCitationClick={(c) => setActiveCitation(c)} />
            ))}
            {isStreaming && (
              <div className="flex items-center gap-2 px-4 py-3">
                <LoadingPulseAnimation className="size-6" />
                <span className="text-xs text-muted-foreground animate-pulse">
                  Streaming Claude 3.5 Sonnet response...
                </span>
              </div>
            )}
          </div>
        </ScrollArea>
      )}

      <ChatInputBox onSend={handleSend} isStreaming={isStreaming} disabled={documentCount === 0} />
    </div>
  );
}
