"use client";

import { useOwnedDocuments } from "@/hooks/useOwnedDocuments";
import { DocumentState } from "@/components/workspace/document-state";
import { useWorkspaceNavigation } from "@/hooks/useWorkspaceNavigation";
import { useFDISStore } from "@/store/useFDISStore";

export function OverviewScreen() {
  const { setActiveTab } = useWorkspaceNavigation();
  const { documents, state, retry } = useOwnedDocuments();
  const { setUploadOpen, setSelectedDocument } = useFDISStore();
  const ready = documents.filter((d) => d.status === "ready");
  return <main className="flex flex-1 flex-col gap-5 overflow-y-auto px-4 pb-6 pt-4 sm:px-8">
    <DocumentState state={state} retry={retry} />
    {(state === "ready" || state === "empty") && <>
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[ ["Your documents", documents.length], ["Ready documents", ready.length], ["Pages ready to query", ready.reduce((n, d) => n + (d.page_count || 0), 0)] ].map(([label, value]) => <div key={label} className="rounded-[22px] bg-white p-6"><p className="text-sm fam-sub">{label}</p><p className="mt-3 text-4xl font-medium fam-ink tabular-nums">{value}</p></div>)}
      </section>
      {documents.length > 0 && <section className="rounded-[22px] bg-white p-6"><h2 className="text-lg font-medium fam-ink">Recent documents</h2><div className="mt-4 space-y-3">{documents.slice(0, 5).map((doc) => <div key={doc.id} className="flex flex-wrap items-center justify-between gap-3 border-t py-3" style={{ borderColor: "var(--fam-line)" }}><p className="min-w-0 flex-1 break-all text-sm fam-ink">{doc.filename}</p><span className="text-xs fam-sub">{doc.status}</span>{doc.status === "ready" && <button className="rounded-full bg-[#DDF3E9] px-4 py-2 text-sm" onClick={() => { setSelectedDocument({ id: doc.id, filename: doc.filename }); setActiveTab("chat"); }}>Ask a question</button>}</div>)}</div></section>}
      {state === "ready" && <div className="flex flex-wrap gap-3"><button onClick={() => setUploadOpen(true)} className="rounded-full bg-[#0C3B2E] px-5 py-2.5 text-sm text-white">Upload PDF</button><button onClick={() => setActiveTab("documents")} className="rounded-full bg-white px-5 py-2.5 text-sm fam-ink">Open documents</button></div>}
    </>}
  </main>;
}
