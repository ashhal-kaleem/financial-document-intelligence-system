"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, TrendingDown, Search, SlidersHorizontal, ArrowLeftRight } from "lucide-react";
import { fetchDocuments } from "@/lib/api";
import { useHydrated } from "@/hooks/useHydrated";

interface MetricRow { name: string; docA: number; docB: number; src: string }
const METRICS: MetricRow[] = [
  { name: "Revenue", docA: 383285, docB: 391035, src: "p.31" },
  { name: "Gross profit", docA: 169148, docB: 180683, src: "p.31" },
  { name: "Operating income", docA: 114301, docB: 123216, src: "p.31" },
  { name: "Net income", docA: 96995, docB: 93736, src: "p.33" },
  { name: "Cash & securities", docA: 61555, docB: 65162, src: "p.35" },
  { name: "Total debt", docA: 111088, docB: 105362, src: "p.37" },
];

const fmt = (v: number) => `$${(v / 1000).toFixed(1)}B`;
const pct = (a: number, b: number) => `${b >= a ? "+" : ""}${(((b - a) / a) * 100).toFixed(1)}%`;

const QUARTERS = [["Q1", 62, 55], ["Q2", 88, 76], ["Q3", 58, 68], ["Q4", 95, 84]];

export function ComparisonScreen() {
  const isHydrated = useHydrated();
  const { data: docs = [] } = useQuery({ queryKey: ["documents"], queryFn: fetchDocuments, enabled: isHydrated });
  const [swapped, setSwapped] = useState(false);

  const filingA = docs[0]?.filename.replace(/\.pdf$/i, "") || "Filing A · FY2024";
  const filingB = docs[1]?.filename.replace(/\.pdf$/i, "") || "Filing B · FY2023";

  const delta = (i: number) => {
    const m = METRICS[i];
    const [a, b] = swapped ? [m.docB, m.docA] : [m.docA, m.docB];
    return { diff: fmt(Math.abs(b - a)), p: pct(a, b), up: b >= a };
  };

  return (
    <div className="v8-orange flex flex-1 flex-col gap-4 overflow-y-auto px-6 pb-6 pt-2" style={{ background: "#F7F7F6" }}>
      <div>
        <h2 className="text-[26px] font-medium tracking-tight fam-ink">Compare filings</h2>
        <p className="text-[12px] fam-sub">Two filings side by side - every difference calculated for you.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.05fr_1.5fr_1.2fr]">
        {/* left column */}
        <div className="flex flex-col gap-4">
          <section className="rounded-[20px] bg-white p-5">
            <p className="text-[11px] fam-mut">{swapped ? filingB : filingA}</p>
            <p className="mt-1 text-[28px] font-medium fam-ink tabular-nums">{fmt(METRICS[0].docB)}</p>
            <p className="mt-0.5 flex items-center gap-1 text-[11px] font-semibold text-[#2E9E4F]">
              <TrendingUp className="size-3" /> 2.0% <span className="font-normal fam-mut">revenue vs FY2023</span>
            </p>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => setSwapped((s) => !s)}
                className="flex items-center gap-1.5 rounded-full bg-[#2C2C25] px-4 py-2 text-[12px] font-medium text-white active:scale-[0.98]"
              >
                <ArrowLeftRight className="size-3.5" /> Swap
              </button>
              <button className="rounded-full bg-white px-4 py-2 text-[12px] font-medium fam-ink active:scale-[0.98]" style={{ border: "1px solid var(--fam-line)" }}>Details</button>
            </div>
          </section>

          <section className="rounded-[20px] bg-white p-5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="fam-sub">Also compare</span>
              <span className="fam-mut">3 filings</span>
            </div>
            <div className="mt-2.5 flex gap-2">
              {["MSFT", "TSLA", "GOOG"].map((t, i) => (
                <span key={t} className={`rounded-full px-3.5 py-1.5 text-[11px] font-semibold ${i < 2 ? "bg-[#FDEBE1] text-[#F06423]" : "bg-[#F7F7F6] fam-mut"}`} style={i < 2 ? {} : { border: "1px solid var(--fam-line)" }}>{t}</span>
              ))}
            </div>
            <p className="mt-3 text-[10px] fam-mut">{swapped ? filingA : filingB} · baseline for all deltas</p>
          </section>

          <section className="rounded-[20px] bg-white p-5">
            <p className="text-[12px] font-medium fam-ink">Comparison coverage</p>
            <div className="mt-2.5 h-[9px] overflow-hidden rounded-full bg-[#F7F7F6]" style={{ border: "1px solid var(--fam-line)" }}>
              <div className="h-full w-[86%] rounded-full bg-[#F06423]" />
            </div>
            <p className="mt-2 text-[11px] fam-sub">12 of 14 metrics matched</p>
          </section>

          <div className="grid grid-cols-2 gap-4">
            <section className="rounded-[20px] bg-[#2C2C25] p-5 text-white">
              <p className="text-[11px] text-white/70">Gross margin</p>
              <p className="mt-2 text-[26px] font-medium tabular-nums">46.2%</p>
              <p className="mt-4 text-[10px] text-white/60">FY2024</p>
              <p className="text-[11px] font-semibold text-[#8CCB6E]">+2.0 pts</p>
            </section>
            <section className="rounded-[20px] p-5 text-white" style={{ background: "linear-gradient(170deg,#F89066,#EC7148)" }}>
              <p className="text-[11px] text-white/80">R&D spend</p>
              <p className="mt-2 text-[26px] font-medium tabular-nums">$31.4B</p>
              <p className="mt-4 text-[10px] text-white/70">FY2024</p>
              <p className="text-[11px] font-semibold">+8.1%</p>
            </section>
          </div>
        </div>

        {/* middle: delta cards + metric table */}
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            {[{ label: "Revenue Δ", i: 0, hero: true }, { label: "Net income Δ", i: 3 }, { label: "Gross profit Δ", i: 1 }, { label: "Op. income Δ", i: 2 }].map(({ label, i, hero }) => {
              const d = delta(i);
              return (
                <section
                  key={label}
                  className="rounded-[20px] p-5"
                  style={hero ? { background: "linear-gradient(170deg,#F89066,#EC7148)" } : { background: "#fff" }}
                >
                  <p className={`text-[11px] ${hero ? "text-white/85" : "fam-sub"}`}>{label}</p>
                  <p className={`mt-1 text-[24px] font-medium tabular-nums ${hero ? "text-white" : "fam-ink"}`}>{d.up ? "+" : "-"}{d.diff.replace("$", "$")}</p>
                  <p className={`mt-1 flex items-center gap-1 text-[11px] font-semibold ${hero ? "text-white/90" : d.up ? "text-[#2E9E4F]" : "text-[#D64541]"}`}>
                    {d.up ? <TrendingUp className="size-3" /> : <TrendingDown className="size-3" />} {d.p.replace("+", "")}
                    <span className={`font-normal ${hero ? "text-white/70" : "fam-mut"}`}>vs FY2023</span>
                  </p>
                </section>
              );
            })}
          </div>

          <section className="flex-1 rounded-[20px] bg-white p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-[13px] font-semibold fam-ink">Metric comparison</h3>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1.5 rounded-full bg-[#F7F7F6] px-3 py-1.5 text-[11px] fam-mut"><Search className="size-3" /> Search</span>
                <span className="flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-[11px] fam-sub" style={{ border: "1px solid var(--fam-line)" }}><SlidersHorizontal className="size-3" /> Filter</span>
              </div>
            </div>
            <table className="mt-3 w-full text-[11.5px]">
              <thead>
                <tr className="text-left text-[10px] fam-mut">
                  <th className="pb-2 font-medium">Metric</th>
                  <th className="pb-2 font-medium text-right">Filing B · FY2023</th>
                  <th className="pb-2 font-medium text-right">Filing A · FY2024</th>
                  <th className="pb-2 font-medium text-right">Change</th>
                  <th className="pb-2 font-medium text-right">Source</th>
                </tr>
              </thead>
              <tbody>
                {METRICS.map((m) => {
                  const up = m.docB >= m.docA;
                  return (
                    <tr key={m.name} className="border-t" style={{ borderColor: "var(--fam-line)" }}>
                      <td className="py-2.5 font-medium fam-ink">{m.name}</td>
                      <td className="py-2.5 text-right fam-sub tabular-nums">{fmt(m.docA)}</td>
                      <td className="py-2.5 text-right fam-ink tabular-nums">{fmt(m.docB)}</td>
                      <td className={`py-2.5 text-right font-semibold tabular-nums ${up ? "text-[#2E9E4F]" : "text-[#D64541]"}`}>{pct(m.docA, m.docB)}</td>
                      <td className="py-2.5 text-right text-[10px] fam-mut tabular-nums">{m.src}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </section>
        </div>

        {/* right: quarterly bars */}
        <section className="rounded-[20px] bg-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-[13px] font-semibold fam-ink">Revenue by Quarter</h3>
              <p className="text-[10px] fam-mut">FY2024 vs FY2023</p>
            </div>
            <div className="flex items-center gap-2.5 text-[10px] fam-sub">
              <span className="flex items-center gap-1"><span className="size-2 rounded-full bg-[#F06423]" /> FY24</span>
              <span className="flex items-center gap-1"><span className="size-2 rounded-full bg-[#2C2C25]" /> FY23</span>
            </div>
          </div>
          <div className="mt-6 flex h-64 items-end justify-around">
            {QUARTERS.map(([q, a, b]) => (
              <div key={q as string} className="flex h-full flex-col items-center justify-end gap-1.5">
                <div className="flex h-full items-end gap-1.5">
                  <div className="w-[22px] rounded-full bg-[#F06423]" style={{ height: `${(a as number) * 2.2}px` }} />
                  <div className="w-[22px] rounded-full bg-[#2C2C25]" style={{ height: `${(b as number) * 2.2}px` }} />
                </div>
                <span className="text-[10px] fam-mut">{q}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
