/**
 * @source shadcn/ui Dialog + Button + Badge + ScrollArea (registry-fetched)
 * @state Zustand useFDISStore
 * @invariant tabular-nums font-mono for page counters
 * @invariant strictly < 150 lines
 */
"use client";

import { useState, useMemo } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useFDISStore } from "@/store/useFDISStore";
import { getDocumentPdfUrl } from "@/lib/api";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, ExternalLink, FileText, CheckCircle2 } from "lucide-react";

export function PdfViewerModal() {
  const { pdfViewer, closePdfViewer } = useFDISStore();
  const [currentPage, setCurrentPage] = useState<number>(pdfViewer.pageNumber || 1);
  const [zoom, setZoom] = useState<number>(100);

  const page = pdfViewer.pageNumber || currentPage;
  const pdfUrl = useMemo(() => {
    if (!pdfViewer.documentId) return "";
    return `${getDocumentPdfUrl(pdfViewer.documentId)}#page=${page}&zoom=${zoom}`;
  }, [pdfViewer.documentId, page, zoom]);

  if (!pdfViewer.isOpen) return null;

  return (
    <Dialog open={pdfViewer.isOpen} onOpenChange={(open) => !open && closePdfViewer()}>
      <DialogContent className="max-w-6xl w-[95vw] h-[90vh] p-0 flex flex-col bg-background/95 backdrop-blur-xl border-border/40 overflow-hidden shadow-2xl">
        <DialogHeader className="px-5 py-3 border-b border-border/30 flex flex-row items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <FileText className="size-4 text-primary" />
            <DialogTitle className="text-sm font-semibold truncate max-w-[280px] sm:max-w-md">
              {pdfViewer.filename || "Document Viewer"}
            </DialogTitle>
            <Badge variant="outline" className="text-xs font-mono tabular-nums bg-primary/10 text-primary border-primary/20">
              Page {page}
            </Badge>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-8 px-2.5 text-xs active:scale-[0.98]"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              <ChevronLeft className="size-3.5 mr-1" /> Prev
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-8 px-2.5 text-xs active:scale-[0.98]"
              onClick={() => setCurrentPage((p) => p + 1)}
            >
              Next <ChevronRight className="size-3.5 ml-1" />
            </Button>
            <div className="h-4 w-px bg-border/40 mx-1 hidden sm:block" />
            <Button
              variant="ghost"
              size="icon"
              className="size-8 active:scale-[0.98] hidden sm:inline-flex"
              onClick={() => setZoom((z) => Math.max(50, z - 20))}
            >
              <ZoomOut className="size-3.5" />
            </Button>
            <span className="text-xs font-mono tabular-nums text-muted-foreground hidden sm:inline-block w-9 text-center">
              {zoom}%
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="size-8 active:scale-[0.98] hidden sm:inline-flex"
              onClick={() => setZoom((z) => Math.min(200, z + 20))}
            >
              <ZoomIn className="size-3.5" />
            </Button>
            {pdfUrl && (
              <Button variant="ghost" size="icon" className="size-8 active:scale-[0.98]" asChild>
                <a href={pdfUrl} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="size-3.5" />
                </a>
              </Button>
            )}
          </div>
        </DialogHeader>

        <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
          <div className="flex-1 bg-muted/20 relative flex items-center justify-center border-r border-border/20 overflow-hidden">
            {pdfUrl ? (
              <iframe src={pdfUrl} className="w-full h-full border-0" title="PDF Document View" />
            ) : (
              <div className="text-center p-6 space-y-2">
                <FileText className="size-10 text-muted-foreground/40 mx-auto animate-pulse" />
                <p className="text-xs text-muted-foreground">Streaming document stream...</p>
              </div>
            )}
          </div>

          <div className="w-full md:w-80 lg:w-96 flex flex-col bg-card/10 shrink-0">
            <div className="px-4 py-3 border-b border-border/20 bg-card/20 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Cited Evidentiary Chunk
              </span>
              <Badge variant="secondary" className="text-[10px] font-mono tabular-nums">
                Verified Ground Truth
              </Badge>
            </div>
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {pdfViewer.highlightedText ? (
                  <div className="p-3.5 rounded-lg border border-primary/20 bg-primary/5 text-xs text-foreground/90 font-mono leading-relaxed selection:bg-primary/30">
                    <div className="flex items-center gap-1.5 text-primary text-[11px] font-medium mb-2">
                      <CheckCircle2 className="size-3.5" /> Extracted Text Passage
                    </div>
                    {pdfViewer.highlightedText}
                  </div>
                ) : (
                  <div className="p-3.5 rounded-lg border border-border/30 bg-muted/10 text-xs text-muted-foreground font-mono leading-relaxed">
                    Source citation passage from Page {page} of {pdfViewer.filename}.
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
