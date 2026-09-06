/**
 * @source shadcn/ui ScrollArea + Sheet + Button + Skeleton (registry-fetched)
 * @animation Lottie empty-docs.json (LottieFiles)
 * @icons Lucide React
 * @invariant 5 mandatory UI states: Ideal, Loading, Empty, Error, Degraded
 */
"use client";

import { useState, useMemo } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { SidebarHeader } from "./sidebar-header";
import { DocumentListItem, DocumentListItemSkeleton } from "./document-list-item";
import { DocumentUploadZone } from "./document-upload-zone";
import { EmptyDocsAnimation } from "@/components/ui/lottie-player";
import { RefreshCw, AlertTriangle } from "lucide-react";
import type { DocumentItem } from "@/lib/api";

interface DocumentSidebarProps {
  documents: DocumentItem[];
  isLoading: boolean;
  isError: boolean;
  onRetryFetch: () => void;
  onDeleteDocument: (id: string) => void;
  onDocumentUploaded: () => void;
  deletingId?: string;
}

export function DocumentSidebar({
  documents,
  isLoading,
  isError,
  onRetryFetch,
  onDeleteDocument,
  onDocumentUploaded,
  deletingId,
}: DocumentSidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showUpload, setShowUpload] = useState(false);

  const filtered = useMemo(() => {
    if (!searchQuery.trim()) return documents;
    const q = searchQuery.toLowerCase();
    return documents.filter((d) =>
      d.filename.toLowerCase().includes(q)
    );
  }, [documents, searchQuery]);

  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-border/40 bg-sidebar lg:w-80">
      <SidebarHeader
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onUploadClick={() => setShowUpload(!showUpload)}
      />

      {showUpload && (
        <div className="border-b border-border/40 p-3">
          <DocumentUploadZone
            onSuccess={() => {
              setShowUpload(false);
              onDocumentUploaded();
            }}
          />
        </div>
      )}

      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-0.5 p-2">
          {/* State 2: Loading — Skeleton mirror */}
          {isLoading && (
            <>
              {Array.from({ length: 5 }).map((_, i) => (
                <DocumentListItemSkeleton key={i} />
              ))}
            </>
          )}

          {/* State 4: Error — explanation + retry */}
          {!isLoading && isError && (
            <div className="flex flex-col items-center gap-3 px-4 py-8 text-center">
              <AlertTriangle className="size-8 text-destructive/70" strokeWidth={1.5} />
              <p className="text-sm text-muted-foreground">
                Failed to load filings
              </p>
              <Button
                variant="secondary"
                size="sm"
                onClick={onRetryFetch}
                className="active:scale-[0.98] transition-transform duration-75"
              >
                <RefreshCw className="mr-1.5 size-3.5" />
                Retry
              </Button>
            </div>
          )}

          {/* State 3: Empty — Lottie animation + CTA */}
          {!isLoading && !isError && filtered.length === 0 && (
            <div className="flex flex-col items-center gap-3 px-4 py-8 text-center">
              <EmptyDocsAnimation className="size-24 opacity-60" />
              <div className="flex flex-col gap-0.5">
                <p className="text-sm font-medium">No filings yet</p>
                <p className="text-xs text-muted-foreground">
                  Upload your first SEC filing to get started
                </p>
              </div>
              <Button
                size="sm"
                onClick={() => setShowUpload(true)}
                className="active:scale-[0.98] transition-transform duration-75"
              >
                Upload Filing
              </Button>
            </div>
          )}

          {/* State 1: Ideal — document list */}
          {!isLoading &&
            !isError &&
            filtered.map((doc) => (
              <DocumentListItem
                key={doc.id}
                document={doc}
                isDeleting={deletingId === doc.id}
                onDelete={onDeleteDocument}
              />
            ))}
        </div>
      </ScrollArea>
    </aside>
  );
}
