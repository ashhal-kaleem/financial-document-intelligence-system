"use client";

import { useCallback, useState } from "react";
import { UploadCloud, X, FileText, Loader2, CheckCircle2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadDocument } from "@/lib/api";
import { useFDISStore } from "@/store/useFDISStore";
import { Orb } from "@/components/shell/orbs";

export function UploadModal({ onUploaded }: { onUploaded?: () => void }) {
  const { isUploadOpen, setUploadOpen } = useFDISStore();
  const [isDragActive, setIsDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const ownerId = useFDISStore.getState().currentUser?.id;
      if (!ownerId) { useFDISStore.getState().setAuthModalOpen(true); throw Error("Sign in to upload."); }
      const doc = await uploadDocument(file);
      if (useFDISStore.getState().currentUser?.id !== ownerId) throw Error("Account changed. Check uploads after signing back in.");
      return doc;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setSelectedFile(null);
      onUploaded?.();
      setTimeout(() => setUploadOpen(false), 900);
    },
  });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file?.type === "application/pdf") setSelectedFile(file);
  }, []);

  if (!isUploadOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1C1F2E]/30 backdrop-blur-sm" onClick={() => setUploadOpen(false)}>
      <div
        className="v8-lilac w-[92vw] max-w-md rounded-[24px] bg-white p-7 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <Orb kind="purple" className="size-10" />
          <button onClick={() => setUploadOpen(false)} className="fam-mut hover:fam-ink" aria-label="Close upload">
            <X className="size-4" />
          </button>
        </div>
        <h2 className="mt-4 text-center text-[18px] font-semibold fam-ink">Upload a filing</h2>
        <p className="mt-1 text-center text-[12px] fam-sub">PDF only. Processing may take time; wait for Ready before asking questions.</p>

        <label
          onDragOver={(e) => { e.preventDefault(); setIsDragActive(true); }}
          onDragLeave={() => setIsDragActive(false)}
          onDrop={handleDrop}
          className={`mt-5 flex cursor-pointer flex-col items-center gap-2.5 rounded-2xl border-2 border-dashed p-8 transition-colors ${isDragActive ? "border-[#A284EC] bg-[#F1EDF8]" : "border-[#ECE8F6] bg-[#FCFCFE]"}`}
        >
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f?.type === "application/pdf") setSelectedFile(f);
            }}
          />
          <UploadCloud className="size-8 text-[#A999C4]" strokeWidth={1.5} />
          <p className="text-[13px] font-medium fam-ink">{selectedFile ? selectedFile.name : "Drop your PDF here, or browse"}</p>
          <p className="text-[10px] fam-mut">10-K, 10-Q, annual reports, earnings releases</p>
        </label>

        {uploadMutation.isSuccess && (
          <p className="mt-3 flex items-center justify-center gap-1.5 text-[12px] font-medium text-[#1F8A4C]">
            <CheckCircle2 className="size-4" /> {uploadMutation.data?.status === "ready" ? "Filing indexed" : "Uploaded; processing is pending"}
          </p>
        )}
        {uploadMutation.isError && (
          <p className="mt-3 text-center text-[12px] text-[#D64541]">Upload failed. Check the backend connection and retry.</p>
        )}

        <button
          onClick={() => selectedFile && uploadMutation.mutate(selectedFile)}
          disabled={!selectedFile || uploadMutation.isPending}
          className="mt-5 flex w-full items-center justify-center gap-2 rounded-full bg-[#141414] py-3 text-[13px] font-medium text-white transition-transform active:scale-[0.98] disabled:opacity-40"
        >
          {uploadMutation.isPending ? <Loader2 className="size-4 animate-spin" /> : <FileText className="size-4" />}
          {uploadMutation.isPending ? "Indexing filing..." : "Upload & index"}
        </button>
      </div>
    </div>
  );
}
