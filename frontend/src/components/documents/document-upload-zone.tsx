/**
 * @source shadcn/ui Card + Button (registry-fetched)
 * @animation Lottie DotLottie React
 * @icons Lucide React (upload-cloud from Iconify)
 */
"use client";

import { useCallback, useState } from "react";
import { Upload, X, FileText, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadDocument } from "@/lib/api";

interface DocumentUploadZoneProps {
  onSuccess?: () => void;
}

export function DocumentUploadZone({ onSuccess }: DocumentUploadZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setSelectedFile(null);
      onSuccess?.();
    },
  });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file?.type === "application/pdf") setSelectedFile(file);
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) setSelectedFile(file);
    },
    []
  );

  return (
    <Card
      className={`relative border-dashed p-6 transition-all duration-200 ${
        isDragActive
          ? "border-primary bg-primary/5"
          : "border-border/40 bg-card/30 hover:border-border/60"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragActive(true);
      }}
      onDragLeave={() => setIsDragActive(false)}
      onDrop={handleDrop}
    >
      {selectedFile ? (
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="flex size-12 items-center justify-center rounded-xl bg-primary/10">
            <FileText className="size-6 text-primary" strokeWidth={1.5} />
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-medium truncate max-w-[200px]">
              {selectedFile.name}
            </span>
            <span className="text-xs text-muted-foreground tabular-nums font-mono">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </span>
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={() => uploadMutation.mutate(selectedFile)}
              disabled={uploadMutation.isPending}
              className="active:scale-[0.98] transition-transform duration-75"
            >
              {uploadMutation.isPending ? (
                <Loader2 className="mr-1.5 size-3.5 animate-spin" />
              ) : (
                <Upload className="mr-1.5 size-3.5" />
              )}
              {uploadMutation.isPending ? "Uploading..." : "Upload"}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSelectedFile(null)}
              disabled={uploadMutation.isPending}
            >
              <X className="mr-1 size-3.5" />
              Cancel
            </Button>
          </div>
          {uploadMutation.isError && (
            <p className="text-xs text-destructive">
              Upload failed. Please try again.
            </p>
          )}
        </div>
      ) : (
        <label className="flex cursor-pointer flex-col items-center gap-3 text-center">
          <div className="flex size-12 items-center justify-center rounded-xl bg-muted/50">
            <Upload className="size-6 text-muted-foreground" strokeWidth={1.5} />
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-medium">
              Drop PDF here or click to browse
            </span>
            <span className="text-xs text-muted-foreground">
              Corporate filings, reports, and PDF documents
            </span>
          </div>
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleFileSelect}
          />
        </label>
      )}
    </Card>
  );
}
