"use client";

import { useFDISStore } from "@/store/useFDISStore";

export function AnalysisUnavailable({ title, detail }: { title: string; detail: string }) {
  const setActiveTab = useFDISStore((s) => s.setActiveTab);
  return <main className="min-w-0 flex-1 overflow-y-auto p-5 sm:p-8"><section className="rounded-[22px] bg-white p-6 sm:p-8"><h1 className="text-2xl font-medium fam-ink">{title}</h1><p className="mt-4 max-w-xl text-sm leading-6 fam-sub">{detail}</p><p className="mt-3 text-sm fam-sub">No figures or activity are shown without verified data from your account.</p><button onClick={() => setActiveTab("documents")} className="mt-6 rounded-full bg-[#0C3B2E] px-5 py-2.5 text-sm text-white">Open your documents</button></section></main>;
}
