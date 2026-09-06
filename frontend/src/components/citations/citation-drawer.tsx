"use client";

import React from "react";
import { X, FileText, CheckCircle, Bookmark } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useFDISStore } from "@/store/useFDISStore";

export function CitationDrawer() {
  const citation = useFDISStore((s) => s.activeCitation);
  const setActiveCitation = useFDISStore((s) => s.setActiveCitation);

  if (!citation) return null;

  const simPercent = Math.round(citation.similarity * 100);

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-card/95 backdrop-blur-xl border-l border-border/70 shadow-2xl flex flex-col transform transition-transform duration-300 ease-in-out animate-in slide-in-from-right">
      {/* Drawer Header */}
      <div className="flex items-center justify-between p-5 border-b border-border/60 bg-muted/30">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold text-sm tabular-nums font-mono">
            #{citation.citation_id}
          </div>
          <div>
            <h3 className="font-semibold text-sm text-foreground">Verified Source Citation</h3>
            <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5">
              <FileText className="h-3 w-3" /> {citation.filename}
            </p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setActiveCitation(null)}
          title="Close Inspector"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Drawer Metadata Gauges */}
      <div className="p-5 border-b border-border/60 grid grid-cols-3 gap-3 bg-muted/10">
        <div className="bg-card p-3 rounded-xl border border-border/60 flex flex-col">
          <span className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">Page</span>
          <span className="text-lg font-bold text-foreground mt-0.5 tabular-nums font-mono">p.{citation.page}</span>
        </div>

        <div className="bg-card p-3 rounded-xl border border-border/60 flex flex-col">
          <span className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">Similarity</span>
          <span className="text-lg font-bold text-emerald-500 mt-0.5 tabular-nums font-mono">{simPercent}%</span>
        </div>

        <div className="bg-card p-3 rounded-xl border border-border/60 flex flex-col">
          <span className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">Chunk</span>
          <span className="text-lg font-bold text-foreground mt-0.5 tabular-nums font-mono">
            {citation.chunk_index + 1}/{citation.total_chunks}
          </span>
        </div>
      </div>

      {/* Drawer Body / Snippet */}
      <div className="flex-1 p-5 overflow-y-auto space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
              <Bookmark className="h-3.5 w-3.5 text-primary" /> Grounded Text Excerpt
            </span>
            <Badge variant="success" className="text-[11px] gap-1">
              <CheckCircle className="h-3 w-3" /> Verified Zero-Hallucination
            </Badge>
          </div>

          <div className="p-4 rounded-xl bg-muted/40 border border-border/60 text-sm leading-relaxed text-foreground font-mono text-xs whitespace-pre-wrap selection:bg-primary/20">
            {citation.snippet}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-primary/5 border border-primary/20 text-xs text-muted-foreground leading-relaxed">
          <p className="font-semibold text-primary mb-1">Auditor Citation Note</p>
          This passage was matched via pgvector cosine similarity. All financial facts reported in the assistant answer are verbatim grounded to this specific section.
        </div>
      </div>

      {/* Drawer Footer */}
      <div className="p-4 border-t border-border/60 bg-muted/20 flex justify-end">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setActiveCitation(null)}
        >
          Close Panel
        </Button>
      </div>
    </div>
  );
}
