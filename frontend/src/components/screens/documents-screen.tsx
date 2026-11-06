"use client";

import { useOwnedDocuments } from "@/hooks/useOwnedDocuments";
import { DocumentState } from "@/components/workspace/document-state";
import { useFDISStore } from "@/store/useFDISStore";

export function DocumentsScreen() {
  const { documents, state, retry } = useOwnedDocuments();
  const { setUploadOpen, setSelectedDocument, setActiveTab, openPdfViewer } = useFDISStore();
  return <main className="min-w-0 flex-1 overflow-y-auto px-4 pb-6 pt-4 sm:px-8">
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><h1 className="text-2xl font-medium fam-ink">Documents</h1>{state !== "signed-out" && state !== "loading" && <button onClick={() => setUploadOpen(true)} className="rounded-full bg-[#0C3B2E] px-5 py-2.5 text-sm text-white">Upload PDF</button>}</div>
    <DocumentState state={state} retry={retry} />
    {state === "ready" && <section className="space-y-3" aria-label="Your document library">{documents.map((doc) => <article key={doc.id} className="rounded-[22px] bg-white p-5">
      <h2 className="break-all text-base font-medium fam-ink">{doc.filename}</h2><p className="mt-2 text-sm fam-sub">{doc.status} · {doc.page_count || 0} pages · Uploaded {new Date(doc.created_at).toLocaleDateString()}</p>
      {doc.status === "error" && <p className="mt-2 text-sm text-red-700">Processing failed. This document is not ready for questions.</p>}
      {doc.status === "ready" && <div className="mt-4 flex flex-wrap gap-3"><button className="rounded-full bg-[#DDF3E9] px-4 py-2 text-sm" onClick={() => { setSelectedDocument({ id: doc.id, filename: doc.filename }); setActiveTab("chat"); }}>Ask a question</button><button className="rounded-full border px-4 py-2 text-sm" onClick={() => openPdfViewer({ documentId: doc.id, filename: doc.filename, pageNumber: 1 })}>Open PDF</button></div>}
    </article>)}</section>}
  </main>;
}
