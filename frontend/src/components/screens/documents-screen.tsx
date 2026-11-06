"use client";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { useOwnedDocuments } from "@/hooks/useOwnedDocuments";
import { DocumentState } from "@/components/workspace/document-state";
import { useWorkspaceNavigation } from "@/hooks/useWorkspaceNavigation";
import { useFDISStore } from "@/store/useFDISStore";
import { deleteDocument, type DocumentItem } from "@/lib/api";
export function DocumentsScreen() {
  const { documents, state, retry } = useOwnedDocuments();
  const { setActiveTab } = useWorkspaceNavigation();
  const { setUploadOpen, setSelectedDocument, openPdfViewer, currentUser } =
    useFDISStore();
  const client = useQueryClient();
  const [target, setTarget] = useState<DocumentItem | null>(null);
  const [note, setNote] = useState("");
  const deletion = useMutation({
    mutationFn: async (doc: DocumentItem) => {
      const owner = currentUser?.id;
      await deleteDocument(doc.id);
      if (useFDISStore.getState().currentUser?.id !== owner)
        throw Error("Account changed. Check your documents again.");
      return doc;
    },
    onSuccess: (doc) => {
      if (useFDISStore.getState().selectedDocument?.id === doc.id)
        setSelectedDocument(null);
      useFDISStore.getState().closePdfViewer();
      setNote("Document deletion confirmed by the server.");
      setTarget(null);
      client.invalidateQueries({ queryKey: ["documents"] });
    },
  });
  return (
    <main className="min-w-0 flex-1 overflow-y-auto px-4 pb-6 pt-4 sm:px-8">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-medium fam-ink">Documents</h1>
        {(state === "ready" || state === "error") && (
          <button
            onClick={() => setUploadOpen(true)}
            className="min-h-11 rounded-full bg-[#0C3B2E] px-5 py-2.5 text-sm text-white"
          >
            Upload PDF
          </button>
        )}
      </div>
      <DocumentState state={state} retry={retry} />
      {note && (
        <p role="status" className="mb-4 text-sm">
          {note}
        </p>
      )}
      {state === "ready" && (
        <section className="space-y-3" aria-label="Your document library">
          {documents.map((doc) => (
            <article key={doc.id} className="rounded-[22px] bg-white p-5">
              <h2 className="break-all text-base font-medium fam-ink">
                {doc.filename}
              </h2>
              <p className="mt-2 text-sm fam-sub">
                {doc.status} · {doc.page_count || 0} pages · Uploaded{" "}
                {new Date(doc.created_at).toLocaleDateString()}
              </p>
              {["queued", "processing", "uploaded"].includes(doc.status) && (
                <p className="mt-2 text-sm text-[#53634F]">
                  Waiting for indexing. Status refreshes automatically. Free
                  server sleep can delay processing; this PDF is not ready for
                  questions.
                </p>
              )}
              {doc.status === "error" && (
                <p className="mt-2 text-sm text-red-700">
                  Processing failed. Not ready for questions. Delete and upload
                  again to retry.
                </p>
              )}
              {doc.status === "deleting" && (
                <p className="mt-2 text-sm text-amber-800">
                  Deletion was not fully confirmed. Retry deletion to finish
                  cleanup.
                </p>
              )}
              <div className="mt-4 flex flex-wrap gap-3">
                {doc.status === "ready" && (
                  <>
                    <button
                      className="min-h-11 rounded-full bg-[#DDF3E9] px-4 py-2 text-sm"
                      onClick={() => {
                        setSelectedDocument({
                          id: doc.id,
                          filename: doc.filename,
                        });
                        setActiveTab("chat");
                      }}
                    >
                      Ask a question
                    </button>
                    <button
                      className="min-h-11 rounded-full border px-4 py-2 text-sm"
                      onClick={() =>
                        openPdfViewer({
                          documentId: doc.id,
                          filename: doc.filename,
                          pageNumber: 1,
                        })
                      }
                    >
                      Open PDF
                    </button>
                  </>
                )}
                <button
                  disabled={
                    deletion.isPending ||
                    ["uploaded", "processing"].includes(doc.status)
                  }
                  onClick={() => {
                    deletion.reset();
                    setNote("");
                    setTarget(doc);
                  }}
                  className="min-h-11 rounded-full border border-red-200 px-4 py-2 text-sm text-red-800 disabled:opacity-40"
                >
                  {doc.status === "deleting" ? "Retry delete" : "Delete"}
                </button>
              </div>
            </article>
          ))}
        </section>
      )}
      <Dialog
        open={Boolean(target)}
        onOpenChange={(open) => {
          if (!open && !deletion.isPending) setTarget(null);
        }}
      >
        <DialogContent className="w-[92vw] max-w-md bg-white">
          <DialogHeader>
            <DialogTitle>Delete this PDF?</DialogTitle>
            <DialogDescription className="break-all">
              {target?.filename}. This removes the PDF and its indexed data. It
              cannot be undone. Browser chat history is separate.
            </DialogDescription>
          </DialogHeader>
          {deletion.isError && (
            <p role="alert" className="text-sm text-red-800">
              {deletion.error.message}
            </p>
          )}
          <div className="flex flex-wrap gap-3">
            <button
              disabled={deletion.isPending}
              onClick={() => setTarget(null)}
              className="min-h-11 rounded-full border px-4"
            >
              Cancel
            </button>
            <button
              disabled={deletion.isPending}
              onClick={() => target && deletion.mutate(target)}
              className="min-h-11 rounded-full bg-red-800 px-4 text-white disabled:opacity-50"
            >
              {deletion.isPending ? "Deleting..." : "Confirm delete"}
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </main>
  );
}
