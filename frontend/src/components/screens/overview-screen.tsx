"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Eye, TrendingUp, ArrowUpRight, MoreHorizontal } from "lucide-react";
import { fetchDocuments } from "@/lib/api";
import { useHydrated } from "@/hooks/useHydrated";
import { useFDISStore } from "@/store/useFDISStore";

function shortTicker(filename: string) {
  const m = filename.match(/[A-Z]{2,5}/);
  return m ? m[0] : filename.replace(/\.pdf$/i, "").slice(0, 5).toUpperCase();
}

export function OverviewScreen() {
  const isHydrated = useHydrated();
  const { setActiveTab, setUploadOpen } = useFDISStore();
  const { data: documents = [] } = useQuery({
    queryKey: ["documents"],
    queryFn: fetchDocuments,
    enabled: isHydrated,
  });

  const readyDocs = documents.filter((d) => d.status === "ready");
  const pagesReady = documents.length ? readyDocs.reduce((n, d) => n + (d.page_count || 0), 0) : 396;
  const tickers = useMemo(() => { const t = documents.slice(0, 3).map((d) => shortTicker(d.filename)); return t.length ? t : ["AAPL", "MSFT", "TSLA"]; }, [documents]);
  const latest = documents[0];

  return (
    <div className="v8-green flex flex-1 flex-col gap-4 overflow-y-auto px-8 pb-6 pt-2">
      {/* Row 1 */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.35fr_1fr]">
        {/* Pages ready card */}
        <section className="relative overflow-hidden rounded-[22px] bg-white p-7">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {tickers.map((t, i) => (
                <span key={i} className={`rounded-full px-3 py-1 text-[11px] font-medium ${i === 0 ? "bg-[#F2F2F0] fam-ink" : "fam-mut"}`} style={i ? { border: "1px solid var(--fam-line)" } : { border: "1px solid var(--fam-line)" }}>
                  {t}
                </span>
              ))}
                          </div>
            <div className="text-right">
              <p className="text-[10px] fam-mut">Document</p>
              <p className="max-w-[96px] sm:max-w-[220px] truncate text-[12px] font-medium fam-ink">{latest?.filename || "AAPL_10K_FY2024.pdf"}</p>
            </div>
          </div>
          <p className="mt-8 text-[12px] fam-sub">Pages Ready to Query</p>
          <div className="mt-1 flex items-end gap-4">
            <span className="text-[64px] leading-none font-medium tracking-tight fam-ink tabular-nums">{pagesReady}</span>
            <Eye className="mb-2 size-4 fam-mut" />
          </div>
          <div className="mt-8 flex items-center gap-2.5 pr-16">
            <button
              onClick={() => setActiveTab("chat")}
              className="rounded-full bg-[#0C3B2E] px-5 py-2.5 text-[13px] font-medium text-white transition-transform active:scale-[0.98]"
            >
              Ask a Question
            </button>
            <button
              onClick={() => setUploadOpen(true)}
              className="rounded-full bg-white px-5 py-2.5 text-[13px] font-medium fam-ink transition-transform active:scale-[0.98]"
              style={{ border: "1px solid var(--fam-line)" }}
            >
              Upload Filing
            </button>
            <button
              aria-label="More actions"
              className="hidden sm:flex size-10 items-center justify-center rounded-full bg-white fam-sub transition-colors hover:fam-ink"
              style={{ border: "1px solid var(--fam-line)" }}
            >
              <MoreHorizontal className="size-4" />
            </button>
          </div>
          <button
            onClick={() => setActiveTab("chat")}
            aria-label="Go to Q&A"
            className="absolute bottom-7 right-7 flex size-14 items-center justify-center rounded-full bg-[#AEF359] shadow-md transition-transform active:scale-95"
          >
            <ArrowUpRight className="size-6 text-[#0C3B2E]" strokeWidth={2.25} />
          </button>
        </section>

        {/* Coverage card */}
        <section className="rounded-[22px] p-7" style={{ background: "linear-gradient(160deg, #C9F78D 0%, #AEF359 60%, #9DEB52 100%)" }}>
          <div className="flex items-center justify-between">
            <span className="rounded-full bg-[#0C3B2E] px-3.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-white">Coverage +</span>
            <span className="text-[18px] fam-ink">···</span>
          </div>
          <p className="mt-6 text-[12px] font-medium text-[#33411F]">Answers with Sources</p>
          <div className="mt-1 flex items-center gap-3">
            <span className="text-[48px] leading-none font-medium tracking-tight text-[#111714] tabular-nums">128</span>
            <span className="rounded-full bg-white/80 px-2.5 py-1 text-[10px] font-semibold text-[#1F8A4C]">+12 this week</span>
          </div>
          <div className="mt-6 grid grid-cols-2 gap-3">
            <div className="rounded-2xl bg-[#DDFBC0]/90 p-4">
              <div className="flex items-center justify-between text-[11px] text-[#33411F]">Citations Opened <Eye className="size-3" /></div>
              <p className="mt-2 text-[26px] font-medium fam-ink tabular-nums">86</p>
            </div>
            <div className="rounded-2xl bg-[#DDFBC0]/90 p-4">
              <div className="flex items-center justify-between text-[11px] text-[#33411F]">Saved Memos <Eye className="size-3" /></div>
              <p className="mt-2 text-[26px] font-medium fam-ink tabular-nums">12</p>
            </div>
          </div>
        </section>
      </div>

      {/* Row 2 */}
      <div className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Questions by filing donut */}
        <section className="rounded-[22px] bg-white p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-[14px] font-semibold fam-ink">Questions by Filing</h3>
            <span className="flex items-center gap-1 rounded-full bg-[#F2F2F0] px-2.5 py-1 text-[10px] fam-sub"><TrendingUp className="size-3 text-[#1F8A4C]" /> April</span>
          </div>
          <div className="mt-6 flex items-center justify-center">
            <div className="relative flex size-40 items-center justify-center rounded-full" style={{ background: "conic-gradient(#AEF359 0 62%, #E9F6E4 62% 100%)" }}>
              <div className="flex size-[104px] flex-col items-center justify-center rounded-full bg-white">
                <span className="text-[30px] font-medium fam-ink tabular-nums">64</span>
                <span className="text-[11px] font-semibold text-[#1F8A4C]">+12%</span>
              </div>
            </div>
          </div>
          <p className="mt-4 text-center text-[11px] fam-sub">AAPL questions up 8.4%</p>
          <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-[12px]">
            {[["AAPL", "28"], ["MSFT", "21"], ["TSLA", "15"]].map(([k, v]) => (
              <div key={k} className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 fam-sub"><span className="size-2 rounded-sm bg-[#AEF359]" />{k}</span>
                <span className="fam-mut tabular-nums">{v}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Pages indexed */}
        <section className="rounded-[22px] bg-white p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-[14px] font-semibold fam-ink">Pages Indexed</h3>
            <span className="text-[10px] fam-mut">···</span>
          </div>
          <div className="mt-4 flex items-end gap-3">
            <span className="text-[38px] leading-none font-medium fam-ink tabular-nums">{pagesReady || 0}</span>
            <span className="mb-1 text-[11px] font-semibold text-[#1F8A4C]">+18% vs last month</span>
          </div>
          <div className="mt-5 flex flex-col gap-4">
            {(documents.length ? documents.slice(0, 4) : []).map((d) => (
              <div key={d.id}>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="font-medium fam-ink truncate max-w-[220px]">{d.filename.replace(/\.pdf$/i, "")}</span>
                  <span className="fam-sub tabular-nums">{d.status === "ready" ? `${d.page_count} pages` : d.status}</span>
                </div>
                <div className="mt-1.5 h-[7px] overflow-hidden rounded-full bg-[#F2F2F0]">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: d.status === "ready" ? `${Math.min(100, Math.round(((d.page_count || 0) / Math.max(1, pagesReady)) * 100 * 2))}%` : "12%",
                      background: d.status === "ready" ? "#1E5C45" : "#DDFBC0",
                    }}
                  />
                </div>
              </div>
            ))}
            {documents.length === 0 && [["AAPL 10-K", "184 pages", "46%", "#1E5C45"], ["MSFT 10-K", "212 pages", "55%", "#1E5C45"], ["TSLA 10-K", "processing", "12%", "#DDFBC0"], ["Others", "-", "8%", "#1E5C45"]].map(([name, meta, w, color]) => (
              <div key={name}>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="font-medium fam-ink">{name}</span>
                  <span className="fam-sub tabular-nums">{meta}</span>
                </div>
                <div className="mt-1.5 h-[7px] overflow-hidden rounded-full bg-[#F2F2F0]">
                  <div className="h-full rounded-full" style={{ width: w, background: color }} />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Recent questions */}
        <section className="rounded-[22px] bg-white p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-[14px] font-semibold fam-ink">Recent Questions</h3>
            <span className="text-[10px] fam-mut">···</span>
          </div>
          <div className="mt-4 flex flex-col gap-3">
            {(documents.find((d) => d.status === "processing") || documents.length === 0) && (
              <div className="rounded-xl p-3" style={{ border: "1px solid var(--fam-line)" }}>
                <p className="truncate text-[12px] font-medium fam-ink">{documents.find((d) => d.status === "processing")?.filename || "TSLA_10K_FY2024.pdf"}</p>
                <p className="text-[11px] text-[#D64541]">Still processing - answers pending</p>
              </div>
            )}
            {[
              ["Services revenue drivers?", "AAPL 10-K · Today, 09:00", "Answered"],
              ["Debt covenants summary", "MSFT 10-K · Yesterday, 14:30", "Answered"],
              ["FY27 revenue guidance", "AAPL 10-K · Yesterday, 11:02", "No source"],
              ["R&D spend vs peers", "All filings · Apr 1, 2026", "Answered"],
            ].map(([q, meta, status]) => (
              <button key={q} onClick={() => setActiveTab("chat")} className="flex items-center justify-between gap-3 text-left">
                <div className="min-w-0">
                  <p className="truncate text-[12px] font-medium fam-ink">{q}</p>
                  <p className="text-[10px] fam-mut">{meta}</p>
                </div>
                <span className={`shrink-0 text-[10px] font-semibold ${status === "Answered" ? "text-[#1F8A4C]" : "text-[#D64541]"}`}>{status}</span>
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
