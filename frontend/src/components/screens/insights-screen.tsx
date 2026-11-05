"use client";

import { Search } from "lucide-react";
import { useFDISStore } from "@/store/useFDISStore";
import { NAV_ITEMS, AvatarCircle } from "@/components/shell/app-chrome";

const KPIS = [
  { label: "Questions asked", value: "396", delta: "+22%", bg: "linear-gradient(140deg,#5ED6D1,#3FB8B2)" },
  { label: "Answers with sources", value: "128", delta: "+36%", bg: "linear-gradient(140deg,#8FBDF3,#6FA8EF)" },
  { label: "Pages indexed", value: "563", delta: "+11%", bg: "linear-gradient(140deg,#F4A9CB,#EF9BC2)" },
  { label: "Citations opened", value: "86", delta: "+15%", bg: "linear-gradient(140deg,#C6AFEF,#B99FEC)" },
];

const RECENT = [
  ["Revenue drivers FY24", "AAPL 10-K", "15 Jul 2026", "4", "#5ED6D1"],
  ["Debt covenants summary", "TSLA 10-K", "14 Jul 2026", "3", "#8FBDF3"],
  ["R&D spend vs peers", "MSFT 10-K", "10 Jul 2026", "5", "#C6AFEF"],
];

export function InsightsScreen() {
  const { activeTab, setActiveTab, currentUser } = useFDISStore();

  return (
    <div className="v8-pastel flex flex-1 overflow-hidden" style={{ background: "#EBEAF5" }}>
      {/* ref2 sidebar */}
      <aside className="flex w-[210px] shrink-0 flex-col px-5 py-6">
        <div className="flex items-center gap-2.5">
          <div className="flex size-8 items-center justify-center rounded-full" style={{ border: "2px solid #B99FEC" }}>
            <span className="size-3.5 rounded-full bg-[#4FC8C4]" />
          </div>
          <span className="text-[15px] font-semibold tracking-tight fam-ink">FDIS</span>
        </div>
        <nav className="mt-8 flex flex-col gap-1">
          {NAV_ITEMS.map((item) => {
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`rounded-xl px-3 py-2 text-left text-[13px] transition-all active:scale-[0.99] ${active ? "bg-[#F1EDF8] font-semibold fam-ink" : "fam-sub hover:fam-ink"}`}
              >
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="flex flex-1 flex-col gap-4 overflow-y-auto rounded-tl-[26px] bg-[#FDFDFE] p-6" style={{ boxShadow: "-8px 0 30px #6C6A8C14" }}>
        {/* header */}
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-[22px] font-semibold tracking-tight fam-ink">Hi {(currentUser?.name || "Srkia Ash").split(" ")[0]},</h2>
            <p className="text-[12px] fam-sub">Welcome back!</p>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="rounded-full bg-white px-3.5 py-2 text-[11px] fam-sub" style={{ border: "1px solid var(--fam-line)" }}>Nov 3, 2026</span>
            <span className="flex items-center gap-2 rounded-full bg-white px-3.5 py-2 text-[11px] fam-mut" style={{ border: "1px solid var(--fam-line)" }}>
              <Search className="size-3.5" /> Search filings
            </span>
            <AvatarCircle name={currentUser?.name || "Srkia Ash"} className="size-8 text-[10px]" />
            <span className="text-[12px] font-medium fam-ink">{currentUser?.name || "Srkia Ash"}</span>
            {!currentUser && <span className="rounded-full bg-white px-1.5 py-0.5 text-[9px] font-semibold fam-sub" style={{ border: "1px solid var(--fam-line)" }}>Demo</span>}
          </div>
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
          {KPIS.map((k) => (
            <section key={k.label} className="rounded-[18px] p-4 text-white" style={{ background: k.bg }}>
              <span className="block size-6 rounded-full bg-white/30" />
              <p className="mt-3 text-[11px] text-white/90">{k.label}</p>
              <p className="text-[26px] font-semibold tabular-nums">{k.value}</p>
              <div className="mt-1.5 flex items-center gap-1.5">
                <span className="rounded-full bg-white/30 px-2 py-0.5 text-[10px] font-bold">{k.delta}</span>
                <span className="text-[10px] text-white/85">than last month</span>
              </div>
            </section>
          ))}
        </div>

        {/* charts row */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.15fr_1fr]">
          <section className="rounded-[18px] bg-white p-5" style={{ border: "1px solid var(--fam-line)" }}>
            <div className="flex items-center justify-between">
              <h3 className="text-[13px] font-semibold fam-ink">Questions by month</h3>
              <span className="rounded-full bg-[#F5F6FA] px-2.5 py-1 text-[10px] fam-sub">Last 6 mo</span>
            </div>
            <svg viewBox="0 0 480 170" className="mt-3 w-full">
              <defs>
                <linearGradient id="qFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0" stopColor="#6FA8EF" stopOpacity="0.22" />
                  <stop offset="1" stopColor="#6FA8EF" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path d="M20,120 110,100 200,88 290,96 380,70 460,62 L460,150 L20,150 Z" fill="url(#qFill)" stroke="none" />
              <polyline points="20,120 110,100 200,88 290,96 380,70 460,62" fill="none" stroke="#6FA8EF" strokeWidth="2.5" strokeLinecap="round" />
              {["May", "Jun", "Jul", "Aug", "Sep", "Oct"].map((m, i) => (
                <text key={m} x={20 + i * 88} y={162} fontSize="10" fill="#B4B9C8">{m}</text>
              ))}
              <circle cx={290} cy={96} r={4} fill="#22242E" />
              <rect x={272} y={66} width={36} height={18} rx={6} fill="#22242E" />
              <text x={290} y={79} fontSize="10" fill="#fff" textAnchor="middle">46</text>
            </svg>
          </section>

          <section className="rounded-[18px] bg-white p-5" style={{ border: "1px solid var(--fam-line)" }}>
            <div className="flex items-center justify-between">
              <h3 className="text-[13px] font-semibold fam-ink">Answers by filing</h3>
              <span className="rounded-full bg-[#F5F6FA] px-2.5 py-1 text-[10px] fam-sub">This month</span>
            </div>
            <div className="mt-3 flex items-center gap-6">
              <div className="relative flex size-32 shrink-0 items-center justify-center rounded-full" style={{ background: "conic-gradient(#4FC8C4 0 32%, #6FA8EF 32% 57%, #EF9BC2 57% 74%, #B99FEC 74% 90%, #E4E7F0 90% 100%)" }}>
                <div className="flex size-[74px] flex-col items-center justify-center rounded-full bg-white">
                  <span className="text-[20px] font-semibold fam-ink tabular-nums">128</span>
                  <span className="text-[8px] fam-mut">answers</span>
                </div>
              </div>
              <div className="flex flex-1 flex-col gap-2 text-[11px]">
                {[["#4FC8C4", "AAPL 10-K", "32%"], ["#6FA8EF", "TSLA 10-K", "25%"], ["#EF9BC2", "MSFT 10-K", "17%"], ["#B99FEC", "FY27 guidance", "16%"], ["#B4B9C8", "Others", "10%"]].map(([c, l, v]) => (
                  <div key={l} className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 fam-sub"><span className="size-2 rounded-full" style={{ background: c }} />{l}</span>
                    <span className="fam-ink tabular-nums">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>

        {/* bottom row */}
        <div className="grid flex-1 grid-cols-1 gap-4 xl:grid-cols-[1.15fr_1fr]">
          <section className="rounded-[18px] bg-white p-5" style={{ border: "1px solid var(--fam-line)" }}>
            <div className="flex items-center justify-between">
              <h3 className="text-[13px] font-semibold fam-ink">Recent answers</h3>
              <div className="flex gap-3 text-[10px]">
                <span className="font-semibold text-[#3FB8B2]">Recently</span>
                <span className="fam-mut">Oldest</span>
                <span className="fam-mut">More</span>
              </div>
            </div>
            <table className="mt-3 w-full text-[11.5px]">
              <thead>
                <tr className="text-left text-[10px] fam-mut">
                  <th className="pb-2 font-medium">Question</th>
                  <th className="pb-2 font-medium">Filing</th>
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium text-right">Sources</th>
                </tr>
              </thead>
              <tbody>
                {RECENT.map(([q, f, d, s, c]) => (
                  <tr key={q} className="border-t" style={{ borderColor: "var(--fam-line)" }}>
                    <td className="py-2.5">
                      <span className="flex items-center gap-2">
                        <span className="size-3 rounded-full" style={{ background: c }} />
                        <span className="font-medium fam-ink">{q}</span>
                      </span>
                    </td>
                    <td className="py-2.5 fam-sub">{f}</td>
                    <td className="py-2.5 fam-sub tabular-nums">{d}</td>
                    <td className="py-2.5 text-right fam-ink tabular-nums">{s}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="rounded-[18px] bg-white p-5" style={{ border: "1px solid var(--fam-line)" }}>
            <div className="flex items-center justify-between">
              <h3 className="text-[13px] font-semibold fam-ink">Reading progress</h3>
              <span className="rounded-full bg-[#EDF3FE] px-2.5 py-1 text-[10px] font-medium text-[#6FA8EF]">Add filing</span>
            </div>
            <div className="mt-4 flex flex-col gap-5">
              {[
                ["AAPL 10-K FY2024", "96 / 184 pages", 52, "#4FC8C4"],
                ["TSLA 10-K FY2024", "45 / 212 pages", 21, "#6FA8EF"],
              ].map(([name, sub, pct, c]) => (
                <div key={name as string}>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-medium fam-ink">{name}</span>
                    <span className="fam-sub tabular-nums">{pct}%</span>
                  </div>
                  <p className="text-[9px] fam-mut tabular-nums">{sub}</p>
                  <div className="mt-1.5 flex gap-1">
                    {Array.from({ length: 16 }).map((_, i) => (
                      <span
                        key={i}
                        className="h-[7px] flex-1 rounded-full"
                        style={{ background: i < Math.round(((pct as number) / 100) * 16) ? (c as string) : "#E4E7F0" }}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
