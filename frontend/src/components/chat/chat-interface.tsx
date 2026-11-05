"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ChatMessageItem } from "./chat-message-item";
import { ChatInputBox } from "./chat-input-box";
import { ChatSidebar } from "@/components/shell/app-chrome";
import { Orb } from "@/components/shell/orbs";
import { useFDISStore, Citation } from "@/store/useFDISStore";
import { streamQuestion, StreamEventPayload } from "@/lib/api";
import { loadChatHistory, saveChatHistory, ChatMessage } from "@/lib/chat-history";
import { Clock, GitCompareArrows, CheckCircle2, MoreHorizontal } from "lucide-react";

interface ChatInterfaceProps {
  documentCount: number;
  onDocumentUploaded?: () => void;
}

const QUICK_ACTIONS = [
  { icon: Clock, title: "Summarize a filing", sub: "Key points from any 10-K, with page citations", prompt: "Summarize the key points of the latest filing" },
  { icon: GitCompareArrows, title: "Compare two filings", sub: "Year-over-year changes, side by side", prompt: "Compare revenue and margins year over year" },
  { icon: CheckCircle2, title: "Check a figure", sub: "Trace any number to its source page", prompt: "Check the reported services revenue figure" },
];

export function ChatInterface({ documentCount, onDocumentUploaded }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const setActiveCitation = useFDISStore((s) => s.setActiveCitation);
  const selectedDocument = useFDISStore((s) => s.selectedDocument);
  const currentUser = useFDISStore((s) => s.currentUser);
  const setExportModalOpen = useFDISStore((s) => s.setExportModalOpen);

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

  const handleSend = useCallback(async (content: string) => {
    const userMsg: ChatMessage = { id: `user-${Date.now()}`, role: "user", content, timestamp: new Date().toISOString() };
    const assistantId = `assistant-${Date.now()}`;
    setMessages((prev) => [...prev, userMsg, { id: assistantId, role: "assistant", content: "", timestamp: new Date().toISOString() }]);
    setIsStreaming(true);

    try {
      const targetDocIds = selectedDocument ? [selectedDocument.id] : undefined;
      let fullContent = "";
      await streamQuestion(content, targetDocIds || [], undefined, (event: StreamEventPayload) => {
        if (event.event === "citations") {
          const citations: Citation[] = (event.citations || []).map((c) => ({
            documentId: c.document_id,
            document: c.filename,
            page: c.page,
            chunk_id: String(c.chunk_index),
            relevance: c.similarity,
            snippet: c.snippet,
          }));
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, citations } : m)));
        } else if (event.event === "token" && event.token) {
          fullContent += event.token;
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: fullContent } : m)));
        } else if (event.event === "error") {
          throw new Error(event.detail || "stream error");
        }
      });
      setMessages((current) => {
        saveChatHistory(current);
        return current;
      });
    } catch {
      setMessages((prev) => prev.map((m) =>
        m.id === assistantId
          ? { ...m, content: "The answer service is temporarily unavailable. Please check the connection and retry." }
          : m
      ));
    } finally {
      setIsStreaming(false);
    }
  }, [selectedDocument]);

  const history = messages.filter((m) => m.role === "user").map((m) => m.content).slice(-12).reverse();
  const empty = messages.length === 0;

  return (
    <div className="v8-lilac flex h-full overflow-hidden">
      <ChatSidebar
        history={history}
        onPick={(q) => {
          if (q) setDraft(q);
          else setMessages([]);
        }}
      />

      {/* main chat card */}
      <div className="flex flex-1 flex-col overflow-hidden bg-[#FDFDFD]">
        <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: "1px solid #F0EEF6" }}>
          <span className="text-[13px] font-semibold text-[#0A0A0A]">FDIS</span>
          <div className="flex items-center gap-2">
            <button className="flex size-8 items-center justify-center rounded-full hover:bg-[#F1EDF8]" aria-label="More">
              <MoreHorizontal className="size-4 text-[#6E6A78]" />
            </button>
            <button
              onClick={() => setExportModalOpen(true)}
              className="rounded-full bg-white px-3.5 py-1.5 text-[11px] font-medium text-[#0A0A0A] active:scale-[0.98]"
              style={{ border: "1px solid #E5E2EC" }}
            >
              Export chat
            </button>
            <button
              onClick={() => setExportModalOpen(true)}
              className="rounded-full bg-[#141414] px-3.5 py-1.5 text-[11px] font-medium text-white active:scale-[0.98]"
            >
              Export memo
            </button>
          </div>
        </div>

        {empty ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-5 overflow-y-auto px-8 py-8">
            <Orb kind="purple" className="size-36" />
            <div className="text-center">
              <p className="bg-gradient-to-r from-[#6D5BD0] to-[#A284EC] bg-clip-text text-[15px] font-semibold text-transparent">
                Hello, {(currentUser?.name || "Guest").split(" ")[0]}
              </p>
              <h2 className="mt-1 text-[30px] font-medium tracking-tight text-[#0A0A0A]">How can I help with your filings?</h2>
            </div>
            <ChatInputBox
              onSend={handleSend}
              isStreaming={isStreaming}
              
              onDocumentUploaded={onDocumentUploaded}
              draft={draft}
              setDraft={setDraft}
              hero
            />
            <div className="grid w-full max-w-3xl grid-cols-1 gap-3 sm:grid-cols-3">
              {QUICK_ACTIONS.map((a) => (
                <button
                  key={a.title}
                  onClick={() => handleSend(a.prompt)}
                  
                  className="rounded-2xl bg-[#FCFCFC] p-4 text-left transition-shadow hover:shadow-md active:scale-[0.99] disabled:opacity-50"
                  style={{ border: "1px solid #F0EEF6" }}
                >
                  <a.icon className="size-4 text-[#6E6A78]" strokeWidth={1.75} />
                  <p className="mt-2.5 text-[13px] font-semibold text-[#0A0A0A]">{a.title}</p>
                  <p className="mt-0.5 text-[11px] leading-snug text-[#A999C4]">{a.sub}</p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto" ref={scrollRef}>
              <div className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-6">
                {messages.map((msg) => (
                  <ChatMessageItem key={msg.id} message={msg} onCitationClick={(c) => setActiveCitation(c)} />
                ))}
                {isStreaming && (
                  <div className="flex items-center gap-2.5">
                    <Orb kind="warm" className="size-7 animate-pulse" />
                    <span className="text-xs text-[#A999C4]">Composing answer...</span>
                  </div>
                )}
              </div>
            </div>
            <div className="px-6 pb-5">
              <ChatInputBox
                onSend={handleSend}
                isStreaming={isStreaming}
                
                onDocumentUploaded={onDocumentUploaded}
                draft={draft}
                setDraft={setDraft}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
