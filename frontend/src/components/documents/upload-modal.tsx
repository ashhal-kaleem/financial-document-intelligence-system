"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { uploadDocument } from "@/lib/api";
import { useFDISStore } from "@/store/useFDISStore";
export function UploadModal({ onUploaded }: { onUploaded?: () => void }) {
  const { isUploadOpen, setUploadOpen } = useFDISStore();
  const [file, setFile] = useState<File | null>(null);
  const [validation, setValidation] = useState("");
  const router = useRouter();
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: async (file: File) => {
      const owner = useFDISStore.getState().currentUser?.id;
      if (!owner) {
        useFDISStore.getState().setAuthModalOpen(true);
        throw Error("Sign in before uploading.");
      }
      const doc = await uploadDocument(file);
      if (useFDISStore.getState().currentUser?.id !== owner)
        throw Error("Account changed. Check uploads after signing back in.");
      return doc;
    },
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["documents"] });
      setFile(null);
      onUploaded?.();
    },
  });
  const select = (f?: File) => {
    mutation.reset();
    setValidation("");
    if (!f) return;
    if (
      f.type !== "application/pdf" ||
      !f.name.toLowerCase().endsWith(".pdf")
    ) {
      setFile(null);
      setValidation("Choose a PDF file.");
      return;
    }
    if (f.size > 25 * 1024 * 1024) {
      setFile(null);
      setValidation("Choose a PDF no larger than 25 MB.");
      return;
    }
    if (!f.size) {
      setFile(null);
      setValidation("This file is empty.");
      return;
    }
    setFile(f);
  };
  return (
    <Dialog
      open={isUploadOpen}
      onOpenChange={(open) => {
        if (!mutation.isPending) {
          setUploadOpen(open);
          if (!open) {
            setFile(null);
            setValidation("");
            mutation.reset();
          }
        }
      }}
    >
      <DialogContent className="w-[92vw] max-w-md max-h-[90dvh] overflow-y-auto rounded-3xl bg-white">
        <DialogHeader>
          <DialogTitle>Upload a PDF</DialogTitle>
          <DialogDescription>
            Your private library stores the original PDF and indexed text.
            Questions and retrieved excerpts go to AI only after you connect and
            consent. Free hosting may delay processing.
          </DialogDescription>
        </DialogHeader>
        <label
          className="block rounded-xl border-2 border-dashed p-5"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (!mutation.isPending) select(e.dataTransfer.files[0]);
          }}
        >
          <span className="mb-3 block text-sm">
            PDF up to 25 MB. Drop here, or choose a file
          </span>
          <input
            aria-label="PDF file"
            type="file"
            accept=".pdf,application/pdf"
            disabled={mutation.isPending}
            onChange={(e) => select(e.target.files?.[0])}
            className="w-full text-xs"
          />
          {file && (
            <span className="mt-3 block break-all text-xs">
              {file.name} · {(file.size / 1024 / 1024).toFixed(2)} MB
            </span>
          )}
        </label>
        {validation && (
          <p role="alert" className="text-sm text-red-800">
            {validation}
          </p>
        )}
        {mutation.isError && (
          <p role="alert" className="text-sm text-red-800">
            {mutation.error.message}
          </p>
        )}
        {mutation.isSuccess ? (
          <>
            <p role="status" className="text-sm">
              {mutation.data.status === "ready"
                ? "Ready for questions."
                : "Upload received. Processing is pending; this is not ready for questions yet."}
            </p>
            <button
              onClick={() => {
                setUploadOpen(false);
                mutation.reset();
                router.push("/documents");
              }}
              className="min-h-11 rounded-full bg-[#123D2B] px-5 text-white"
            >
              View document status
            </button>
          </>
        ) : (
          <button
            disabled={!file || mutation.isPending}
            onClick={() => file && mutation.mutate(file)}
            className="min-h-11 rounded-full bg-[#123D2B] px-5 text-white disabled:opacity-40"
          >
            {mutation.isPending
              ? "Uploading PDF. Keep this page open..."
              : "Upload PDF"}
          </button>
        )}
      </DialogContent>
    </Dialog>
  );
}
