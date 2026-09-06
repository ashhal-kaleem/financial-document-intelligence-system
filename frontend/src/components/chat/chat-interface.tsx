"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Sparkles,
  Bot,
  User,
  ShieldCheck,
  RefreshCw,
  Mail,
  Check,
  ExternalLink,
  Cpu,
  Layers,
  FileSearch,
  AlertTriangle,
} from "lucide-react";
import { CitationItem, streamQuestion, sendEmailAlert } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useFDISStore } from "@/store/useFDISStore";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: CitationItem[];
  isStreaming?: boolean;
  stage?: string;
  error?: string;
}

interface ChatInterfaceProps {
  documentCount: number;
}

const SAMPLE_QUERIES = [
  "What were Apple's total net sales and operating income in fiscal 2024?",
  "What is the breakdown of Services revenue vs Products revenue in 2024?",
  "What is the term debt liability and commercial paper financing activity?",
  "What was the effective tax rate in fiscal 2024 compared to 2023?",
];

export function ChatInterface({ documentCount }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [emailAddress, setEmailAddress] = useState("");
  const [emailSentSuccess, setEmailSentSuccess] = useState(false);

  // Zustand Store
  const selectedDocIds = useFDISStore((s) => s.selectedDocIds);
  const selectedModel = useFDISStore((s) => s.selectedModel);
  const setSelectedModel = useFDISStore((s) => s.setSelectedModel);
  const setActiveCitation = useFDISStore((s) => s.setActiveCitation);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStage]);

  const handleSubmit = async (queryText?: string) => {
    const textToSubmit = queryText || inputQuery;
    if (!textToSubmit.trim() || isStreaming) return;

    const userMessageId = "msg_" + Date.now();
    const assistantMessageId = "asst_" + (Date.now() + 1);

    const newMessages: Message[] = [
      ...messages,
      { id: userMessageId, role: "user", content: textToSubmit.trim() },
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        citations: [],
        isStreaming: true,
      },
    ];

    setMessages(newMessages);
    setInputQuery("");
    setIsStreaming(true);
    setCurrentStage("Connecting to inference engine...");

    let accumulatedContent = "";
    let accumulatedCitations: CitationItem[] = [];

    try {
      await streamQuestion(
        textToSubmit.trim(),
        selectedDocIds,
        selectedModel,
        (event) => {
          if (event.event === "stage") {
            setCurrentStage(event.detail || "Processing...");
          } else if (event.event === "citations" && event.citations) {
            accumulatedCitations = event.citations;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, citations: accumulatedCitations }
                  : msg
              )
            );
          } else if (event.event === "token" && event.token) {
            accumulatedContent += event.token;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: accumulatedContent }
                  : msg
              )
            );
          } else if (event.event === "error") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, error: event.detail, isStreaming: false }
                  : msg
              )
            );
          } else if (event.event === "done") {
            setCurrentStage(null);
            setIsStreaming(false);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, isStreaming: false }
                  : msg
              )
            );
          }
        }
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                error: err.message || "Failed to generate answer.",
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
      setCurrentStage(null);
    }
  };

  const handleSendAuditEmail = async () => {
    if (!emailAddress || messages.length === 0) return;
    const lastAssistantMessage = [...messages].reverse().find((m) => m.role === "assistant");
    if (!lastAssistantMessage) return;

    try {
      await sendEmailAlert(
        emailAddress,
        selectedDocIds.length > 0 ? "Filtered Financial Reports" : "Corporate Annual Reports",
        lastAssistantMessage.content
      );
      setEmailSentSuccess(true);
      setTimeout(() => {
        setEmailSentSuccess(false);
        setEmailModalOpen(false);
        setEmailAddress("");
      }, 2000);
    } catch (err) {
      alert("Failed to send email alert.");
    }
  };

  // Helper to render text with interactive citation badges
  const renderMessageContentWithCitations = (content: string, citations?: CitationItem[]) => {
    if (!citations || citations.length === 0) {
      return <div className="whitespace-pre-wrap leading-relaxed tabular-nums">{content}</div>;
    }

    // Split text by citation markers like [1], [2]
    const parts = content.split(/(\[\d+\])/g);
    return (
      <div className="whitespace-pre-wrap leading-relaxed tabular-nums">
        {parts.map((part, i) => {
          const match = part.match(/\[(\d+)\]/);
          if (match) {
            const citId = parseInt(match[1], 10);
            const cit = citations.find((c) => c.citation_id === citId);
            if (cit) {
              return (
                <Button
                  key={i}
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveCitation(cit)}
                  className="inline-flex items-center gap-1 mx-1 h-6 px-2 py-0 rounded-md bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-semibold text-xs border border-emerald-500/30 transition-all align-middle font-mono tabular-nums cursor-pointer"
                  title={`View citation #${citId} on Page ${cit.page}`}
                >
                  <span>[{citId}]</span>
                  <span className="text-[10px] opacity-75 tabular-nums">p.{cit.page}</span>
                </Button>
              );
            }
          }
          return <span key={i}>{part}</span>;
        })}
      </div>
    );
  };

  return (
    <div className="flex-1 h-full flex flex-col bg-background relative overflow-hidden">
      {/* Chat Navigation Header */}
      <header className="h-14 border-b border-border px-6 flex items-center justify-between bg-card/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-medium">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Scope:</span>
            <span className="text-foreground font-semibold tabular-nums font-mono">
              {selectedDocIds.length > 0
                ? `${selectedDocIds.length} Selected Filing${selectedDocIds.length > 1 ? "s" : ""}`
                : `All Indexed Filings (${documentCount})`}
            </span>
          </div>
        </div>

        {/* Model Selector & Email Share */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-muted/40 border border-border px-2.5 py-1 rounded-xl text-xs">
            <Cpu className="h-3.5 w-3.5 text-primary" />
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-transparent text-foreground text-xs focus:outline-none cursor-pointer font-mono"
            >
              <option value="groq/qwen3.8-27b">Groq LPU (qwen3.8-27b)</option>
              <option value="liquid/lfm-2.5-2.6b:free">OpenRouter (lfm-2.5 free)</option>
            </select>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setEmailModalOpen(true)}
            disabled={messages.length === 0}
            className="flex items-center gap-1.5 h-8 text-xs font-medium"
            title="Email last answer as audit brief"
          >
            <Mail className="h-3.5 w-3.5 text-primary" />
            <span>Email Brief</span>
          </Button>
        </div>
      </header>

      {/* Main Message History Area */}
      <div className="flex-1 overflow-y-auto px-6 py-8 space-y-6">
        {messages.length === 0 ? (
          // Empty State
          <div className="max-w-2xl mx-auto py-12 text-center space-y-6">
            <div className="h-16 w-16 rounded-2xl bg-primary/10 text-primary mx-auto flex items-center justify-center shadow-lg shadow-primary/10">
              <Sparkles className="h-8 w-8" />
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold text-foreground">
                Grounded Financial Intelligence
              </h2>
              <p className="text-sm text-muted-foreground max-w-lg mx-auto">
                Query 10-Ks, balance sheets, and footnotes with zero hallucination. All answers are strictly cited back to source pages and verified by pgvector.
              </p>
            </div>

            {/* Suggested Starter Queries */}
            <div className="pt-4 text-left">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-3 text-center">
                Suggested Financial Queries
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {SAMPLE_QUERIES.map((q, idx) => (
                  <Button
                    key={idx}
                    variant="outline"
                    onClick={() => handleSubmit(q)}
                    className="h-auto p-3.5 rounded-xl border border-border bg-card/60 hover:bg-primary/5 hover:border-primary/40 text-left text-xs text-foreground transition-all flex items-start justify-start gap-2.5 group whitespace-normal font-normal"
                  >
                    <FileSearch className="h-4 w-4 text-primary shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                    <span>{q}</span>
                  </Button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // Message Bubbles
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3.5 ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "assistant" && (
                  <div className="h-8 w-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 mt-1">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div
                  className={`relative max-w-[85%] rounded-2xl p-4 text-sm shadow-sm ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground font-medium rounded-tr-none"
                      : "bg-card border border-border text-foreground rounded-tl-none"
                  }`}
                >
                  {/* Assistant Header with Citations Count */}
                  {msg.role === "assistant" && msg.citations && msg.citations.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pb-3 mb-3 border-b border-border">
                      <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1">
                        <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" /> Citations:
                      </span>
                      {msg.citations.map((c) => (
                        <Button
                          key={c.citation_id}
                          variant="secondary"
                          size="sm"
                          onClick={() => setActiveCitation(c)}
                          className="h-6 px-2 py-0 rounded-md bg-muted hover:bg-muted/80 text-[11px] font-mono tabular-nums text-foreground border border-border flex items-center gap-1 transition-colors"
                        >
                          <span>#{c.citation_id}</span>
                          <span className="text-muted-foreground text-[10px] tabular-nums">p.{c.page}</span>
                        </Button>
                      ))}
                    </div>
                  )}

                  {/* Body Content */}
                  {msg.content ? (
                    renderMessageContentWithCitations(msg.content, msg.citations)
                  ) : msg.isStreaming ? (
                    // Skeleton loading mirror
                    <div className="space-y-2 py-2">
                      <Skeleton className="h-3 w-48" />
                      <Skeleton className="h-3 w-64" />
                      <Skeleton className="h-3 w-40" />
                    </div>
                  ) : null}

                  {/* Error State with Retry */}
                  {msg.error && (
                    <div className="mt-2 p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs space-y-2">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 shrink-0" />
                        <span className="font-semibold">Query Execution Error</span>
                      </div>
                      <p>{msg.error}</p>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleSubmit()}
                        className="px-3 py-1 text-xs font-medium flex items-center gap-1.5"
                      >
                        <RefreshCw className="h-3 w-3" /> Retry Query
                      </Button>
                    </div>
                  )}
                </div>

                {msg.role === "user" && (
                  <div className="h-8 w-8 rounded-xl bg-secondary text-secondary-foreground flex items-center justify-center shrink-0 mt-1">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {/* Real-time Streaming Stage Indicator */}
            {isStreaming && currentStage && (
              <div className="flex items-center gap-2.5 text-xs text-muted-foreground px-4 py-2 rounded-xl bg-muted/30 border border-border w-fit animate-pulse">
                <RefreshCw className="h-3.5 w-3.5 animate-spin text-primary" />
                <span>{currentStage}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Sticky Bottom Query Input */}
      <div className="p-4 border-t border-border bg-card/80 backdrop-blur-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="max-w-3xl mx-auto relative flex items-center gap-2"
        >
          <div className="relative flex-1">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder="Ask any question about balance sheets, debt covenants, or segment performance..."
              disabled={isStreaming}
              className="w-full resize-none py-3 px-4 rounded-xl border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary/40 text-sm text-foreground placeholder:text-muted-foreground disabled:opacity-60"
            />
          </div>

          <Button
            type="submit"
            disabled={!inputQuery.trim() || isStreaming}
            size="icon"
            className="h-11 w-11 rounded-xl bg-primary text-primary-foreground flex items-center justify-center hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-primary/20 shrink-0"
            title="Send Query (Enter)"
          >
            {isStreaming ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </div>

      {/* Email Share Modal */}
      {emailModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                  <Mail className="h-4 w-4" />
                </div>
                <h3 className="font-semibold text-sm text-foreground">Send Audit Summary</h3>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEmailModalOpen(false)}
                className="text-muted-foreground hover:text-foreground text-xs h-7 w-7 p-0"
              >
                ✕
              </Button>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">
              Email the last verified financial answer and citations directly to an auditor or analyst inbox via Resend.
            </p>

            <input
              type="email"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              placeholder="analyst@firm.com"
              className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setEmailModalOpen(false)}
                className="px-4 py-2 text-xs font-medium"
              >
                Cancel
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleSendAuditEmail}
                disabled={!emailAddress || emailSentSuccess}
                className="px-4 py-2 text-xs font-medium flex items-center gap-1.5"
              >
                {emailSentSuccess ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-300" /> Sent!
                  </>
                ) : (
                  "Send Email"
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
