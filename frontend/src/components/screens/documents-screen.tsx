"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Plus } from "lucide-react";
import { fetchDocuments } from "@/lib/api";
import { useHydrated } from "@/hooks/useHydrated";
import { useFDISStore } from "@/store/useFDISStore";

const BARS = [38, 46, 34, 58, 41, 47];

export function DocumentsScreen() {
  const isHydrated = useHydrated();
  const { setActiveTab, setUploadOpen } = useFDISStore();
  const { data: documents = [] } = useQuery({ queryKey: ["documents"], queryFn: fetchDocuments, enabled: isHydrated });
  const latest = documents[0];
  const totalPages = documents.reduce((n, d) => n + (d.page_count || 0), 0);

  return (
    <div className="v8-green flex flex-1 flex-col gap-4 overflow-y-auto px-8 pb-6 pt-2">
      <div className="flex items-end justify-between">
        <h2 className="text-[30px] font-medium tracking-tight fam-ink">Documents Library</h2>
        <div className="flex items-center gap-2.5">
          <span className="rounded-full bg-white px-4 py-2 text-[12px] font-medium fam-ink" style={{ border: "1px solid var(--fam-line)" }}>FY2024 filings</span>
          <button
            onClick={() => setUploadOpen(true)}
            className="flex items-center gap-1.5 rounded-full bg-[#141414] px-4 py-2.5 text-[12px] font-medium text-white transition-transform active:scale-[0.98]"
          >
            <Plus className="size-3.5" /> Upload filing
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Latest filing */}
        <section className="rounded-[22px] bg-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-[14px] font-semibold fam-ink">Latest Filing</h3>
              <p className="text-[11px] fam-mut">Recently uploaded</p>
            </div>
            <ArrowUpRight className="size-4 fam-mut" />
          </div>
          <div className="mt-4 rounded-2xl p-5 text-white" style={{ background: "linear-gradient(150deg, #1C8B5A 0%, #117F4E 100%)" }}>
            <span className="rounded-md bg-white/15 px-2 py-0.5 text-[10px] font-bold tracking-wider">PDF</span>
            <p className="mt-4 text-[12px] text-white/85">{latest ? latest.filename.replace(/\.pdf$/i, "") : "Apple Inc. - Form 10-K"}</p>
            <p className="mt-1 text-[26px] font-medium tabular-nums">{latest ? `${latest.page_count} pages` : "184 pages"}</p>
            <div className="mt-4 flex gap-2 text-[10px] text-white/80">
              <span className="rounded-full bg-white/10 px-2.5 py-1">FORM 10-K</span>
              <span className="rounded-full bg-white/10 px-2.5 py-1">FY2024</span>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between">
            <div>
              <p className="text-[11px] fam-mut">Questions This Week</p>
              <p className="text-[18px] font-medium fam-ink tabular-nums">+26</p>
            </div>
            <span className="rounded-full bg-[#DDF3E9] px-2.5 py-1 text-[10px] font-semibold text-[#117F4E]">+18%</span>
          </div>
        </section>

        {/* Questions by month */}
        <section className="rounded-[22px] bg-white p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-[14px] font-semibold fam-ink">Questions by Month</h3>
            <div className="flex items-center gap-1.5 text-[10px]">
              <span className="rounded-full bg-[#F2F2F0] px-2.5 py-1 fam-sub">Monthly</span>
              <span className="rounded-full bg-[#117F4E] px-2.5 py-1 font-semibold text-white">FY2024</span>
            </div>
          </div>
          <div className="mt-6 flex h-36 items-end justify-between gap-3 px-2">
            {BARS.map((v, i) => (
              <div key={i} className="flex flex-1 flex-col items-center gap-2">
                <div className="relative w-full max-w-[42px] rounded-full" style={{ height: `${v * 2}px`, background: i === 3 ? "#117F4E" : "#C7E3D4" }}>
                  {i === 3 && <span className="absolute -top-7 left-1/2 -translate-x-1/2 rounded-full bg-[#141414] px-2 py-0.5 text-[10px] font-semibold text-white">32</span>}
                </div>
                <span className="text-[9px] fam-mut">{["JAN", "FEB", "MAR", "APR", "MAY", "JUN"][i]}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Pages across filings */}
        <section className="rounded-[22px] bg-white p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-[14px] font-semibold fam-ink">Pages Across Filings</h3>
            <ArrowUpRight className="size-4 fam-mut" />
          </div>
          <p className="mt-2 text-[34px] font-medium fam-ink tabular-nums">{totalPages || 563}</p>
          <div className="mt-3 flex items-center gap-2.5">
            <button onClick={() => setActiveTab("chat")} className="rounded-full bg-[#117F4E] px-4 py-2 text-[12px] font-medium text-white active:scale-[0.98]">Ask</button>
            <button onClick={() => setUploadOpen(true)} className="rounded-full bg-white px-4 py-2 text-[12px] font-medium fam-ink active:scale-[0.98]" style={{ border: "1px solid var(--fam-line)" }}>Upload</button>
          </div>
        </section>
      </div>

      <div className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-[1.9fr_1fr]">
        {/* Document library table */}
        <section className="rounded-[22px] bg-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-[14px] font-semibold fam-ink">Document Library</h3>
              <p className="text-[11px] fam-mut">All uploaded filings</p>
            </div>
            <ArrowUpRight className="size-4 fam-mut" />
          </div>
          <table className="mt-4 w-full text-left text-[12px]">
            <thead>
              <tr className="text-[10px] uppercase tracking-wide fam-mut">
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">Uploaded</th>
                <th className="pb-2 font-medium">Pages</th>
                <th className="pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((d) => (
                <tr key={d.id} className="border-t" style={{ borderColor: "var(--fam-line)" }}>
                  <td className="py-3">
                    <div className="flex items-center gap-2.5">
                      <span className="flex size-7 items-center justify-center rounded-full bg-[#DDF3E9] text-[10px] font-bold text-[#117F4E]">
                        {d.filename[0]?.toUpperCase()}
                      </span>
                      <div>
                        <p className="font-medium fam-ink">{d.filename.replace(/\.pdf$/i, "")}</p>
                        <p className="text-[10px] fam-mut">{d.page_count} pgs</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 fam-sub tabular-nums">{new Date(d.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</td>
                  <td className="py-3 fam-sub tabular-nums">{d.page_count}</td>
                  <td className="py-3">
                    <span className={`flex w-fit items-center gap-1.5 text-[11px] font-medium ${d.status === "ready" ? "text-[#117F4E]" : d.status === "error" ? "text-[#D64541]" : "text-[#B4620E]"}`}>
                      <span className={`size-1.5 rounded-full ${d.status === "ready" ? "bg-[#117F4E]" : d.status === "error" ? "bg-[#D64541]" : "bg-[#B4620E]"}`} />
                      {d.status === "ready" ? "Ready" : d.status === "error" ? "Error" : "Processing"}
                    </span>
                  </td>
                </tr>
              ))}
              {documents.length === 0 && [["A", "AAPL_10K_FY2024", "184 pgs", "16 Jun 2026", "184", "ready"], ["M", "MSFT_10K_FY2024", "212 pgs", "15 Jun 2026", "212", "ready"], ["T", "TSLA_10K_FY2024", "167 pgs", "14 Jun 2026", "167", "processing"]].map(([i, name, pgs, date, pages, st]) => (
                <tr key={name} className="border-t" style={{ borderColor: "var(--fam-line)" }}>
                  <td className="py-3">
                    <div className="flex items-center gap-2.5">
                      <span className="flex size-7 items-center justify-center rounded-full bg-[#DDF3E9] text-[10px] font-bold text-[#117F4E]">{i}</span>
                      <div>
                        <p className="font-medium fam-ink">{name}</p>
                        <p className="text-[10px] fam-mut">{pgs}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 fam-sub tabular-nums">{date}</td>
                  <td className="py-3 fam-sub tabular-nums">{pages}</td>
                  <td className="py-3">
                    <span className={`flex w-fit items-center gap-1.5 text-[11px] font-medium ${st === "ready" ? "text-[#117F4E]" : "text-[#B4620E]"}`}>
                      <span className={`size-1.5 rounded-full ${st === "ready" ? "bg-[#117F4E]" : "bg-[#B4620E]"}`} />
                      {st === "ready" ? "Ready" : "Processing"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Citations */}
        <section className="rounded-[22px] bg-white p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-[14px] font-semibold fam-ink">Citations Opened</h3>
            <span className="rounded-full bg-[#DDF3E9] px-2 py-0.5 text-[10px] font-semibold text-[#117F4E]">+9</span>
          </div>
          <p className="mt-2 text-[34px] font-medium fam-ink tabular-nums">86</p>
          <p className="mt-6 text-[12px] font-medium fam-ink">Shared With</p>
          <p className="text-[10px] fam-mut">Recent collaborators</p>
          <div className="mt-2 flex -space-x-1.5">
            {["AR", "RS", "MP", "+2"].map((t, i) => (
              <span key={i} className={`flex size-7 items-center justify-center rounded-full border-2 border-white text-[9px] font-bold ${["bg-[#F5D0A9]", "bg-[#C9E4CA]", "bg-[#E5CBF6]", "bg-[#117F4E] text-white"][i]}`}>{t}</span>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
