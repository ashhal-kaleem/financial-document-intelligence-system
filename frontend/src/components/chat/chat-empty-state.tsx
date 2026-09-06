/**
 * @source shadcn/ui Card (registry-fetched)
 * @icons Lucide React
 * @avatar DiceBear API (bottts style for AI assistant)
 */
"use client";

import { Brain, FileText, TrendingUp, Shield } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const suggestions = [
  {
    icon: FileText,
    title: "Summarize Filings",
    description: "What are the key takeaways from Apple's 10-K?",
  },
  {
    icon: TrendingUp,
    title: "Revenue Analysis",
    description: "Compare revenue growth across uploaded filings",
  },
  {
    icon: Shield,
    title: "Risk Factors",
    description: "What are the top risk factors mentioned?",
  },
  {
    icon: Brain,
    title: "Footnote Deep Dive",
    description: "Explain the lease obligations in footnote 12",
  },
];

interface ChatEmptyStateProps {
  documentCount: number;
}

export function ChatEmptyState({ documentCount }: ChatEmptyStateProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 px-6 py-12">
      {/* AI Avatar — DiceBear bottts */}
      <div className="flex flex-col items-center gap-3 text-center">
        <img
          src="https://api.dicebear.com/7.x/bottts/svg?seed=fdis-ai&backgroundColor=b6e3f4&radius=50"
          alt="FDIS AI Assistant"
          className="size-16 rounded-full border-2 border-primary/20"
          loading="lazy"
        />
        <div className="flex flex-col gap-1">
          <h2 className="text-lg font-semibold tracking-tight">
            Financial Intelligence
          </h2>
          <p className="max-w-sm text-sm text-muted-foreground">
            {documentCount > 0
              ? `Ask questions about your ${documentCount} uploaded filing${documentCount > 1 ? "s" : ""}. Answers include verifiable citations.`
              : "Upload SEC filings to start asking questions with verifiable citations."}
          </p>
        </div>
      </div>

      {/* Suggestion grid */}
      <div className="grid w-full max-w-lg grid-cols-2 gap-2.5">
        {suggestions.map((s) => (
          <Card
            key={s.title}
            className="group cursor-pointer border-border/30 bg-card/40 transition-all duration-200 hover:border-primary/30 hover:bg-card/60"
          >
            <CardContent className="flex flex-col gap-1.5 p-3.5">
              <s.icon className="size-4 text-primary/70 transition-colors group-hover:text-primary" strokeWidth={1.75} />
              <span className="text-xs font-medium">{s.title}</span>
              <span className="text-[10px] leading-relaxed text-muted-foreground">
                {s.description}
              </span>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
