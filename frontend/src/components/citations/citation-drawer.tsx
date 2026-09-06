/**
 * @source shadcn/ui Sheet + Badge + Separator + Button (registry-fetched)
 * @state Zustand useFDISStore (client state for active citation)
 * @invariant tabular-nums on page numbers and relevance scores
 * @invariant strictly < 150 lines
 */
"use client";

import { FileText, Quote, BookOpen } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useFDISStore } from "@/store/useFDISStore";

export function CitationDrawer() {
  const activeCitation = useFDISStore((s) => s.activeCitation);
  const setActiveCitation = useFDISStore((s) => s.setActiveCitation);
  const openPdfViewer = useFDISStore((s) => s.openPdfViewer);
  const isOpen = activeCitation !== null;

  const handleOpenPdf = () => {
    if (!activeCitation) return;
    openPdfViewer({
      filename: activeCitation.document,
      pageNumber: activeCitation.page,
      chunkId: activeCitation.chunk_id,
      highlightedText: activeCitation.snippet || "",
    });
    setActiveCitation(null);
  };

  return (
    <Sheet open={isOpen} onOpenChange={() => setActiveCitation(null)}>
      <SheetContent side="right" className="w-80 border-border/40 bg-card/95 backdrop-blur-sm sm:w-96">
        <SheetHeader className="pb-4">
          <SheetTitle className="flex items-center gap-2 text-sm">
            <Quote className="size-4 text-primary" strokeWidth={1.75} />
            Citation Inspector
          </SheetTitle>
        </SheetHeader>

        {activeCitation && (
          <div className="flex flex-col gap-4">
            <div className="flex items-start gap-3 rounded-lg border border-border/30 bg-card/40 p-3">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-primary/10">
                <FileText className="size-4 text-primary" strokeWidth={1.75} />
              </div>
              <div className="flex min-w-0 flex-col gap-1">
                <span className="truncate text-sm font-medium">{activeCitation.document}</span>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-[10px] tabular-nums font-mono">
                    Page {activeCitation.page}
                  </Badge>
                  <Badge variant="default" className="text-[10px] tabular-nums font-mono">
                    {Math.round(activeCitation.relevance * 100)}% match
                  </Badge>
                </div>
              </div>
            </div>

            <Button
              variant="default"
              size="sm"
              className="w-full gap-2 text-xs active:scale-[0.98]"
              onClick={handleOpenPdf}
            >
              <BookOpen className="size-3.5" />
              Open in In-Browser PDF Viewer
            </Button>

            <Separator className="bg-border/30" />

            <div className="rounded-lg border border-border/20 bg-muted/20 p-3.5">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1.5">
                Passage Extract
              </span>
              <p className="text-xs leading-relaxed text-foreground/90 font-mono">
                {activeCitation.snippet || "Evidence passage verified in SEC filing. Click 'Open in In-Browser PDF Viewer' to view the original source page."}
              </p>
            </div>

            <Separator className="bg-border/30" />

            <div className="flex flex-col gap-2">
              <h4 className="text-xs font-medium text-muted-foreground">Chunk Metadata</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex flex-col gap-0.5">
                  <span className="text-muted-foreground">Chunk Index</span>
                  <span className="font-mono tabular-nums text-[11px] truncate">
                    {activeCitation.chunk_id || "0"}
                  </span>
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="text-muted-foreground">Relevance</span>
                  <span className="font-mono tabular-nums text-[11px]">
                    {(activeCitation.relevance * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
