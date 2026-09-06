"use client";

import React, { useRef, useState } from "react";
import {
  FileText,
  Upload,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Database,
  Layers,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { DocumentItem, uploadDocument } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useFDISStore } from "@/store/useFDISStore";

interface DocumentSidebarProps {
  documents: DocumentItem[];
  isLoading: boolean;
  onDeleteDocument: (id: string) => void;
  onDocumentUploaded: () => void;
  onRetryFetch?: () => void;
  isError?: boolean;
}

export function DocumentSidebar({
  documents,
  isLoading,
  onDeleteDocument,
  onDocumentUploaded,
  onRetryFetch,
  isError,
}: DocumentSidebarProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const selectedDocIds = useFDISStore((s) => s.selectedDocIds);
  const toggleSelectDoc = useFDISStore((s) => s.toggleSelectDoc);
  const selectAllDocs = useFDISStore((s) => s.selectAllDocs);
  const clearSelectedDocs = useFDISStore((s) => s.clearSelectedDocs);

  const totalPages = documents.reduce((acc, d) => acc + (d.page_count || 0), 0);
  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Only PDF files are supported.");
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      await uploadDocument(file);
      onDocumentUploaded();
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err: any) {
      setUploadError(err.message || "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <aside className="w-80 h-full border-r border-border/60 bg-card/60 backdrop-blur-md flex flex-col select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-border/60 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-primary flex items-center justify-center text-primary-foreground shadow-md shadow-primary/20">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="font-bold text-sm text-foreground tracking-tight flex items-center gap-1.5">
              FDIS <span className="text-[10px] uppercase font-semibold tracking-wider text-emerald-500 bg-emerald-500/10 px-1.5 py-0.5 rounded-full border border-emerald-500/20 tabular-nums font-mono">v1.0</span>
            </h1>
            <p className="text-[11px] text-muted-foreground">Financial Document Intelligence</p>
          </div>
        </div>
      </div>

      {/* Upload Action Card */}
      <div className="p-4 border-b border-border/60">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileChange}
        />
        <Button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          variant="outline"
          className="w-full flex items-center justify-center gap-2 py-5 border-dashed border-primary/40 hover:border-primary/80 bg-primary/5 hover:bg-primary/10 text-foreground transition-all group"
        >
          <Upload className="h-4 w-4 text-primary group-hover:-translate-y-0.5 transition-transform" />
          <span className="text-xs font-semibold">
            {isUploading ? "Ingesting PDF Filing..." : "Upload 10-K / Annual Report"}
          </span>
        </Button>

        {uploadError && (
          <div className="mt-2.5 p-2.5 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-start gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span className="leading-tight">{uploadError}</span>
          </div>
        )}
      </div>

      {/* Knowledge Base Statistics */}
      <div className="px-4 py-3 border-b border-border/60 bg-muted/20 flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <Database className="h-3.5 w-3.5 text-primary" />
          <span>Documents: <strong className="text-foreground tabular-nums font-mono">{documents.length}</strong></span>
        </div>
        <div className="flex items-center gap-3">
          <span className="tabular-nums font-mono">{totalPages} pgs</span>
          <span className="tabular-nums font-mono">{totalChunks} chunks</span>
        </div>
      </div>

      {/* Bulk Selection Controls */}
      {documents.length > 0 && (
        <div className="px-4 py-2 border-b border-border/60 flex items-center justify-between bg-muted/10">
          <span className="text-[11px] font-medium text-muted-foreground">
            Active Filings: <strong className="text-primary tabular-nums font-mono">{selectedDocIds.length}</strong>/{documents.length}
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => selectAllDocs(documents.map((d) => d.id))}
              className="text-[11px] text-muted-foreground hover:text-foreground h-6 px-2"
            >
              Select All
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearSelectedDocs}
              className="text-[11px] text-muted-foreground hover:text-foreground h-6 px-2"
            >
              Clear
            </Button>
          </div>
        </div>
      )}

      {/* Document List Container — Handles 5 UI States */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {isLoading ? (
          /* Loading State: 3-Card Skeleton Mirror (NOT generic spinner) */
          <div className="space-y-2.5 p-1">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-3 rounded-xl border border-border/40 bg-card/40 space-y-2">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3.5 w-12" />
                </div>
                <div className="flex items-center gap-2 pt-1">
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-3 w-20" />
                </div>
              </div>
            ))}
          </div>
        ) : isError ? (
          /* Error State: Clear explanation + Retry Action */
          <div className="h-48 flex flex-col items-center justify-center text-center p-4">
            <AlertCircle className="h-8 w-8 text-destructive/80 mb-2" />
            <p className="text-xs font-semibold text-foreground">Failed to Load Filings</p>
            <p className="text-[11px] text-muted-foreground mt-1 mb-3">Database connection could not be established.</p>
            {onRetryFetch && (
              <Button size="sm" variant="outline" onClick={onRetryFetch} className="gap-1.5 text-xs">
                <RefreshCw className="h-3.5 w-3.5" /> Try Again
              </Button>
            )}
          </div>
        ) : documents.length === 0 ? (
          /* Empty State: Centered icon, friendly title, actionable description */
          <div className="h-64 flex flex-col items-center justify-center text-center p-4">
            <div className="h-12 w-12 rounded-2xl bg-muted flex items-center justify-center text-muted-foreground mb-3">
              <FileText className="h-6 w-6" />
            </div>
            <p className="text-xs font-semibold text-foreground">No Filings Ingested</p>
            <p className="text-[11px] text-muted-foreground mt-1 max-w-[200px] leading-relaxed">
              Upload an Apple, Microsoft, or Tesla 10-K report to begin grounded financial Q&A.
            </p>
          </div>
        ) : (
          /* Ideal State: Rich document cards */
          documents.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            return (
              <div
                key={doc.id}
                onClick={() => toggleSelectDoc(doc.id)}
                className={`group p-3 rounded-xl border transition-all cursor-pointer relative ${
                  isSelected
                    ? "bg-primary/10 border-primary/40 shadow-sm"
                    : "bg-card/40 border-border/60 hover:bg-card hover:border-border hover:-translate-y-0.5"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2.5 overflow-hidden">
                    <div className="mt-0.5">
                      {isSelected ? (
                        <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border border-muted-foreground/40 shrink-0" />
                      )}
                    </div>
                    <div className="overflow-hidden">
                      <h4 className="text-xs font-medium text-foreground truncate group-hover:text-primary transition-colors" title={doc.filename}>
                        {doc.filename}
                      </h4>
                      <div className="flex items-center gap-2 mt-1 text-[10px] text-muted-foreground">
                        <span className="tabular-nums font-mono">{doc.page_count} pgs</span>
                        <span>•</span>
                        <span className="tabular-nums font-mono">{doc.chunk_count} chunks</span>
                        {doc.is_sample && (
                          <Badge variant="secondary" className="text-[9px] px-1 py-0 h-4">
                            Sample
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteDocument(doc.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 h-6 w-6 text-muted-foreground hover:text-destructive transition-all"
                    title="Delete Document"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Storage Footer */}
      <div className="p-3 border-t border-border/60 bg-muted/10 text-[11px] text-muted-foreground flex items-center justify-between">
        <span className="flex items-center gap-1">
          <Layers className="h-3 w-3 text-emerald-500" /> pgvector 0.8.2 Active
        </span>
        <span className="text-[10px] tabular-nums font-mono text-muted-foreground/80">384-dim All-MiniLM</span>
      </div>
    </aside>
  );
}
