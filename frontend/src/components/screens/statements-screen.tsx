"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchDocuments } from "@/lib/api";
import { useHydrated } from "@/hooks/useHydrated";
import { useFDISStore } from "@/store/useFDISStore";

const KPIS = [
  { label: "Revenue", value: "$391.0B", delta: "+2.0%", sub: "+$7.7B vs FY2023", pos: true },
  { label: "Gross profit", value: "$180.7B", delta: "+6.8%", sub: "+$11.6B vs FY2023", pos: true },
  { label: "Op. income", value: "$123.2B", delta: "+7.8%", sub: "+$8.9B vs FY2023", pos: true },
  { label: "Net income", value: "$93.7B", delta: "-3.4%", sub: "-$3.3B vs FY2023", pos: false },
];

const TABLE: [string, string, string, string, string, boolean][] = [
  ["Revenue", "$383.3B", "$391.0B", "+2.0%", "p.31", true],
  ["Cost of sales", "$214.1B", "$210.4B", "-1.8%", "p.31", true],
  ["Gross profit", "$169.1B", "$180.7B", "+6.8%", "p.31", true],
  ["R&D", "$29.9B", "$31.4B", "+8.1%", "p.33", false],
  ["SG&A", "$24.9B", "$26.1B", "+4.6%", "p.33", false],
  ["Operating income", "$114.5B", "$123.2B", "+7.8%", "p.33", true],
  ["Net income", "$97.0B", "$93.7B", "-3.4%", "p.35", false],
];

const SEGMENTS = [
  ["iPhone", "$201.2B", 88], ["Services", "$96.2B", 42], ["Mac", "$30.0B", 13],
  ["iPad", "$26.7B", 12], ["Wearables", "$37.0B", 16],
] as const;

export function StatementsScreen() {
  const isHydrated = useHydrated();
  const { setActiveTab } = useFDISStore();
  const { data: documents = [] } = useQuery({ queryKey: ["documents"], queryFn: fetchDocuments, enabled: isHydrated });
  const filingA = documents[0];

  return (
    <div className="flex flex-1 gap-0 overflow-hidden v8-green" style={{ background: "#EAF1E4" }}>
      {/* dense grid */}
      <div className="grid flex-1 grid-cols-1 gap-3 overflow-y-auto p-4 xl:grid-cols-[1.5fr_1fr_0.9fr]">
        {/* col 1 */}
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-3">
            {KPIS.map((k) => (
              <div key={k.label} className="rounded-2xl bg-white p-4">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] fam-sub">{k.label}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${k.pos ? "bg-[#E7F5DA] text-[#4C8A2E]" : "bg-[#FBEAEA] text-[#C4504F]"}`}>{k.delta}</span>
                </div>
                <p className="mt-1.5 text-[24px] font-medium fam-ink tabular-nums">{k.value}</p>
                <p className="text-[10px] fam-mut tabular-nums">{k.sub}</p>
              </div>
            ))}
          </div>
          <div className="rounded-2xl bg-white p-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-[13px] font-semibold fam-ink">Revenue trend</h3>
                <p className="text-[10px] fam-mut">quarterly, $B</p>
              </div>
              <div className="flex items-center gap-3 text-[10px] fam-sub">
                <span className="flex items-center gap-1"><span className="size-2 rounded-full bg-[#CDEFA6]" /> Revenue</span>
                <span className="flex items-center gap-1"><span className="size-2 rounded-full bg-[#0E3B2E]" /> Net income</span>
                <span className="rounded-full bg-[#F2F2F0] px-2 py-0.5">FY22-FY24</span>
              </div>
            </div>
            <svg viewBox="0 0 560 160" className="mt-4 w-full">
              <polyline points="20,120 190,95 370,70 540,40" fill="none" stroke="#8CCB6E" strokeWidth="2.5" strokeLinecap="round" />
              <polyline points="20,130 190,118 370,105 540,96" fill="none" stroke="#0E3B2E" strokeWidth="2.5" strokeLinecap="round" />
              {["FY22", "FY23", "FY24"].map((t, i) => (
                <text key={t} x={20 + i * 185} y={152} fontSize="10" fill="#A6AF9E">{t}</text>
              ))}
            </svg>
          </div>
          <div className="rounded-2xl bg-white p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-[13px] font-semibold fam-ink">Income statement</h3>
              <span className="rounded-full bg-[#F2F2F0] px-2.5 py-1 text-[10px] fam-sub">FY2024</span>
            </div>
            <table className="mt-3 w-full text-[11.5px]">
              <thead>
                <tr className="text-left text-[10px] fam-mut">
                  <th className="pb-2 font-medium">Line item</th>
                  <th className="pb-2 font-medium text-right">FY2023</th>
                  <th className="pb-2 font-medium text-right">FY2024</th>
                  <th className="pb-2 font-medium text-right">Change</th>
                  <th className="pb-2 font-medium text-right">Src</th>
                </tr>
              </thead>
              <tbody>
                {TABLE.map(([name, a, b, c, src, pos]) => (
                  <tr key={name} className="border-t" style={{ borderColor: "#EFF3EA" }}>
                    <td className="py-2 font-medium fam-ink">{name}</td>
                    <td className="py-2 text-right fam-sub tabular-nums">{a}</td>
                    <td className="py-2 text-right fam-ink tabular-nums">{b}</td>
                    <td className="py-2 text-right">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${pos ? "bg-[#E7F5DA] text-[#4C8A2E]" : "bg-[#FBEAEA] text-[#C4504F]"}`}>{c}</span>
                    </td>
                    <td className="py-2 text-right text-[10px] fam-mut tabular-nums">{src}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* col 2 */}
        <div className="flex flex-col gap-3">
          <div className="rounded-2xl bg-white p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-[13px] font-semibold fam-ink">Cost structure</h3>
              <span className="rounded-full bg-[#F2F2F0] px-2 py-0.5 text-[10px] fam-sub">FY2024</span>
            </div>
            <div className="mt-4 flex items-center justify-center">
              <div className="relative flex size-36 items-center justify-center rounded-full" style={{ background: "conic-gradient(#0E3B2E 0 54%, #8CCB6E 54% 66%, #CDEFA6 66% 78%, #EDF3E6 78% 100%)" }}>
                <div className="flex size-[88px] flex-col items-center justify-center rounded-full bg-white">
                  <span className="text-[9px] fam-mut">COGS</span>
                  <span className="text-[22px] font-medium fam-ink tabular-nums">54%</span>
                </div>
              </div>
            </div>
            <div className="mt-4 flex flex-col gap-1.5 text-[11px]">
              {[["#0E3B2E", "Cost of sales", "54%"], ["#8CCB6E", "R&D", "8%"], ["#CDEFA6", "SG&A", "6%"]].map(([c, l, v]) => (
                <div key={l} className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 fam-sub"><span className="size-2 rounded-full" style={{ background: c }} />{l}</span>
                  <span className="fam-ink tabular-nums">{v}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl bg-white p-5">
            <h3 className="text-[13px] font-semibold fam-ink">Segments</h3>
            <p className="text-[10px] fam-mut">revenue share, FY2024</p>
            <div className="mt-3 flex flex-col gap-3">
              {SEGMENTS.map(([name, val, pct]) => (
                <div key={name}>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-medium fam-ink">{name}</span>
                    <span className="fam-sub tabular-nums">{val}</span>
                  </div>
                  <div className="mt-1 h-[7px] overflow-hidden rounded-full bg-[#F2F2F0]">
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, background: "linear-gradient(90deg,#0E3B2E,#8CCB6E)" }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl bg-[#0E3B2E] p-5 text-white">
            <p className="text-[13px] font-semibold">Ask anything about your filings</p>
            <button onClick={() => setActiveTab("chat")} className="mt-3 rounded-full bg-[#CDEFA6] px-4 py-2 text-[12px] font-semibold text-[#0E3B2E] active:scale-[0.98]">
              Open Q&A
            </button>
          </div>
        </div>

        {/* col 3 */}
        <div className="flex flex-col gap-3">
          <div className="rounded-2xl bg-white p-5">
            <h3 className="text-[13px] font-semibold fam-ink">Filing A</h3>
            <p className="text-[10px] fam-mut">Form 10-K · FY2024</p>
            <div className="mt-3 h-[7px] overflow-hidden rounded-full bg-[#F2F2F0]">
              <div className="h-full w-[86%] rounded-full" style={{ background: "linear-gradient(90deg,#0E3B2E,#8CCB6E)" }} />
            </div>
            <p className="mt-2 text-[10px] fam-sub tabular-nums">{filingA ? `${filingA.page_count} pages · ${filingA.status}` : "184 pages · period ended Sep 28, 2024"}</p>
          </div>
          <div className="rounded-2xl bg-white p-5">
            <h3 className="text-[13px] font-semibold fam-ink">Documents</h3>
            <p className="text-[10px] fam-mut">in this workspace</p>
            <div className="mt-3 flex flex-col gap-2.5">
              {(documents.length ? documents.slice(0, 2) : [{ id: "s1", filename: "FORM 10-K · FY2024", page_count: 184 }, { id: "s2", filename: "FORM 10-K · FY2023", page_count: 171 }]).map((d: any, i: number) => (
                <div key={d.id} className={`rounded-xl p-3.5 ${i === 0 ? "bg-[#0E3B2E] text-white" : "bg-[#E9F6E4]"}`}>
                  <p className={`text-[10px] ${i === 0 ? "text-white/70" : "fam-sub"}`}>FORM 10-K</p>
                  <p className={`text-[15px] font-semibold ${i === 0 ? "" : "fam-ink"}`}>{i === 0 ? "FY2024" : "FY2023"}</p>
                  <p className={`text-[10px] ${i === 0 ? "text-white/70" : "fam-mut"} tabular-nums`}>{d.page_count} pages · PDF</p>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl bg-white p-5">
            <h3 className="text-[13px] font-semibold fam-ink">Recent queries</h3>
            <div className="mt-3 flex flex-col gap-3">
              {[
                ["What drove the gross margin expansion?", "2h ago"],
                ["Compare R&D spend FY23 vs FY24", "5h ago"],
                ["Summarize risk factors", "Yesterday"],
                ["Net income walk FY23 to FY24", "Yesterday"],
              ].map(([q, t]) => (
                <button key={q} onClick={() => setActiveTab("chat")} className="flex items-start gap-2 text-left">
                  <span className="mt-1 size-1.5 shrink-0 rounded-full bg-[#CDEFA6]" />
                  <span>
                    <span className="block text-[11px] font-medium fam-ink">{q}</span>
                    <span className="block text-[9px] fam-mut">{t}</span>
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
