/**
 * @source shadcn/ui Card + Badge + Button + Skeleton (registry-fetched)
 * @icons Lucide React
 * @invariant tabular-nums on page counts and timestamps
 * @invariant strictly < 150 lines
 */
"use client";

import { FileText, Trash2, Loader2, CheckCircle, AlertCircle, Clock, Target } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { DocumentItem } from "@/lib/api";

interface DocumentListItemProps {
  document: DocumentItem;
  isDeleting: boolean;
  isSelected?: boolean;
  onDelete: (id: string) => void;
  onSelect?: (doc: DocumentItem) => void;
}

const statusConfig: Record<string, { icon: typeof CheckCircle; label: string; variant: "default" | "secondary" | "destructive" }> = {
  ready: { icon: CheckCircle, label: "Ready", variant: "default" as const },
  processing: { icon: Loader2, label: "Processing", variant: "secondary" as const },
  uploaded: { icon: Clock, label: "Uploaded", variant: "secondary" as const },
  error: { icon: AlertCircle, label: "Error", variant: "destructive" as const },
};

export function DocumentListItem({
  document,
  isDeleting,
  isSelected = false,
  onDelete,
  onSelect,
}: DocumentListItemProps) {
  const status = statusConfig[document.status as keyof typeof statusConfig] ??
    statusConfig.uploaded;
  const StatusIcon = status.icon;

  return (
    <div
      onClick={() => onSelect?.(document)}
      className={`group flex items-start gap-3 rounded-lg border p-3 transition-all duration-200 cursor-pointer ${
        isSelected
          ? "border-primary/50 bg-primary/10 shadow-sm"
          : "border-transparent hover:border-border/40 hover:bg-card/60"
      }`}
    >
      <div className={`flex size-9 shrink-0 items-center justify-center rounded-md ${
        isSelected ? "bg-primary text-primary-foreground" : "bg-primary/8 text-primary"
      }`}>
        <FileText className="size-4" strokeWidth={1.75} />
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <div className="flex items-center gap-1.5">
          <span className="truncate text-sm font-medium leading-tight">
            {document.filename}
          </span>
          {isSelected && (
            <Badge variant="default" className="h-4 px-1 text-[9px] bg-primary gap-0.5 shrink-0">
              <Target className="size-2.5" /> Target
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={status.variant} className="h-5 gap-1 text-[10px] tabular-nums">
            <StatusIcon
              className={`size-3 ${document.status === "processing" ? "animate-spin" : ""}`}
              strokeWidth={2}
            />
            {status.label}
          </Badge>
          {document.page_count && (
            <span className="text-[10px] text-muted-foreground tabular-nums font-mono">
              {document.page_count} pages
            </span>
          )}
        </div>
      </div>

      <Button
        variant="ghost"
        size="icon"
        className="size-7 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 hover:text-destructive active:scale-[0.98]"
        onClick={(e) => {
          e.stopPropagation();
          onDelete(document.id);
        }}
        disabled={isDeleting}
        aria-label={`Delete ${document.filename}`}
      >
        {isDeleting ? (
          <Loader2 className="size-3.5 animate-spin" />
        ) : (
          <Trash2 className="size-3.5" strokeWidth={1.75} />
        )}
      </Button>
    </div>
  );
}

export function DocumentListItemSkeleton() {
  return (
    <div className="flex items-start gap-3 p-3">
      <Skeleton className="size-9 rounded-md" />
      <div className="flex flex-1 flex-col gap-1.5">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/3" />
      </div>
    </div>
  );
}
