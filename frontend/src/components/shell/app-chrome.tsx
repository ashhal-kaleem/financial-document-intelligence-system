"use client";

import { Bell, LayoutGrid, MessageSquare, FileText, Table2, GitCompareArrows, PieChart, Clock, Settings, LogOut, Search, Plus, PanelLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { useFDISStore, DashboardTab } from "@/store/useFDISStore";

export const NAV_ITEMS: { id: DashboardTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "chat", label: "Q&A" },
  { id: "documents", label: "Documents" },
  { id: "statements", label: "Statements" },
  { id: "comparison", label: "Comparison" },
  { id: "insights", label: "Insights" },
];

export function initialsOf(name?: string | null) {
  if (!name) return "G";
  const parts = name.trim().split(/\s+/);
  return (parts[0]?.[0] || "G") + (parts[1]?.[0] || "");
}

export function AvatarCircle({ name, className }: { name?: string | null; className?: string }) {
  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full bg-[var(--fam-tint)] fam-sub font-semibold uppercase",
        className
      )}
      style={{ border: "1px solid var(--fam-line)" }}
    >
      {initialsOf(name)}
    </div>
  );
}

export function ProfileChip({ family, expanded = true }: { family: string; expanded?: boolean }) {
  const { currentUser, setAuthModalOpen } = useFDISStore();
  const name = currentUser?.name || "Srkia Ash";
  return (
    <button
      onClick={() => setAuthModalOpen(true)}
      className={cn(
        "flex items-center gap-2.5 rounded-full bg-white pl-1.5 pr-3 py-1.5 transition-shadow hover:shadow-md active:scale-[0.98]",
        `v8-${family}`
      )}
      style={{ border: "1px solid var(--fam-line)" }}
    >
      <AvatarCircle name={name} className="size-7 text-[10px]" />
      {expanded && <span className="hidden sm:inline text-xs font-medium fam-ink truncate max-w-[110px]">{name}</span>}
      {expanded && !currentUser && <span className="hidden sm:inline rounded-full px-1.5 py-0.5 text-[9px] font-semibold fam-sub" style={{ background: "var(--fam-tint)" }}>Demo</span>}
    </button>
  );
}

export function BellButton({ family }: { family: string }) {
  return (
    <button
      className={cn("relative flex size-9 items-center justify-center rounded-full bg-white transition-shadow hover:shadow-md active:scale-[0.98]", `v8-${family}`)}
      style={{ border: "1px solid var(--fam-line)" }}
      aria-label="Notifications"
    >
      <Bell className="size-4 fam-sub" strokeWidth={1.75} />
      <span className="absolute -top-0.5 -right-0.5 flex size-3.5 items-center justify-center rounded-full bg-[#D64541] text-[8px] font-bold text-white">3</span>
    </button>
  );
}

export function LogoMark({ family, dark = false }: { family: string; dark?: boolean }) {
  return (
    <div className={cn("flex items-center gap-2.5", `v8-${family}`)}>
      <div
        className={cn("flex size-8 items-center justify-center rounded-lg text-[13px] font-bold", dark ? "bg-[var(--fam-deep)] text-white" : "bg-[var(--fam-accent-soft)] fam-ink")}
      >
        F
      </div>
      <span className="text-[15px] font-semibold tracking-tight fam-ink">FDIS</span>
    </div>
  );
}

/** Top navigation bar used by ref1 / ref5 / ref4 / ref3-family headers. */
export function TopNav({ family, greeting }: { family: string; greeting?: boolean }) {
  const { activeTab, setActiveTab, currentUser } = useFDISStore();
  return (
    <header className={cn("flex flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 sm:px-8 pt-6 pb-2", `v8-${family}`)}>
      <div className="flex items-center gap-3 min-w-0 md:min-w-[180px]">
        {greeting ? (
          <>
            <AvatarCircle name={currentUser?.name || "Srkia Ash"} className="size-9 text-xs" />
            <span className="text-lg font-medium fam-ink">Hello, {(currentUser?.name || "Srkia Ash").split(" ")[0]}</span>
          </>
        ) : (
          <LogoMark family={family} />
        )}
      </div>
      <nav className="order-3 flex w-full items-center gap-1 overflow-x-auto md:order-none md:w-auto md:overflow-visible">
        {NAV_ITEMS.map((item) => {
          const active = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={cn(
                "rounded-full px-4 py-2 text-[13px] transition-all active:scale-[0.98]",
                active ? "font-semibold fam-ink" : "fam-sub hover:fam-ink"
              )}
              style={active ? { backgroundColor: "var(--fam-accent)" } : undefined}
            >
              {item.label}
            </button>
          );
        })}
      </nav>
      <div className="flex items-center gap-2.5 min-w-0 md:min-w-[180px] justify-end">
        <BellButton family={family} />
        <ProfileChip family={family} />
      </div>
    </header>
  );
}

const RAIL_ICONS: Record<DashboardTab, typeof LayoutGrid> = {
  overview: LayoutGrid,
  chat: MessageSquare,
  documents: FileText,
  statements: Table2,
  comparison: GitCompareArrows,
  insights: PieChart,
};

/** Left icon rail with labels (ref3 Statements style). */
export function LabeledRail({ family }: { family: string }) {
  const { activeTab, setActiveTab } = useFDISStore();
  return (
    <aside className={cn("hidden md:flex w-[180px] shrink-0 flex-col gap-1 py-8 pl-6 pr-3", `v8-${family}`)}>
      <div className="mb-8 px-1"><LogoMark family={family} dark /></div>
      {NAV_ITEMS.filter((n) => n.id !== "insights").map((item) => {
        const Icon = RAIL_ICONS[item.id];
        const active = activeTab === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={cn(
              "flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] transition-all active:scale-[0.98]",
              active ? "font-semibold fam-ink" : "fam-sub hover:fam-ink"
            )}
            style={active ? { backgroundColor: "var(--fam-accent)" } : undefined}
          >
            <Icon className="size-4" strokeWidth={1.75} />
            {item.label}
          </button>
        );
      })}
      <div className="mt-auto flex flex-col gap-3">
        <div className="rounded-2xl bg-[#0E3B2E] p-4 text-white">
          <p className="text-[12px] font-semibold leading-snug">Ask anything about your filings</p>
          <button onClick={() => setActiveTab("chat")} className="mt-3 rounded-full bg-[#CDEFA6] px-3.5 py-1.5 text-[11px] font-semibold text-[#0E3B2E] transition-transform active:scale-[0.97]">Open Q&A</button>
        </div>
        <button className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] fam-sub hover:fam-ink transition-colors">
          <Settings className="size-4" strokeWidth={1.75} /> Settings
        </button>
      </div>
    </aside>
  );
}

/** Slim circular icon rail (ref4 Comparison / ref5 Documents style). */
export function CircleRail({ family }: { family: string }) {
  const { activeTab, setActiveTab } = useFDISStore();
  return (
    <aside className={cn("flex w-[68px] shrink-0 flex-col items-center gap-3 py-6", `v8-${family}`)}>
      {NAV_ITEMS.filter((n) => n.id !== "insights").map((item) => {
        const Icon = RAIL_ICONS[item.id];
        const active = activeTab === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            title={item.label}
            className={cn(
              "flex size-10 items-center justify-center rounded-full transition-all active:scale-[0.95]",
              active ? "fam-deep-bg text-white shadow-md" : "fam-sub hover:bg-[var(--fam-tint)]"
            )}
          >
            <Icon className="size-[18px]" strokeWidth={1.75} />
          </button>
        );
      })}
    </aside>
  );
}

/** ref6 chat sidebar: logo, new question, search, nav, history, profile. */
export function ChatSidebar({ history, onPick }: { history: string[]; onPick: (q: string) => void }) {
  const { activeTab, setActiveTab, currentUser, setAuthModalOpen } = useFDISStore();
  return (
    <aside className="v8-lilac hidden md:flex w-[270px] shrink-0 flex-col bg-[#F2F2F3] rounded-l-[28px]">
      <div className="flex items-center justify-between px-5 pt-5 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-[#C9B6F2]">
            <LayoutGrid className="size-4 text-white" strokeWidth={2} />
          </div>
          <span className="text-[15px] font-semibold tracking-tight text-[#0A0A0A]">FDIS</span>
        </div>
        <button className="fam-sub hover:fam-ink" aria-label="Collapse sidebar"><PanelLeft className="size-4" /></button>
      </div>
      <div className="px-4">
        <button
          onClick={() => onPick("")}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#141414] py-2.5 text-[13px] font-medium text-white transition-transform active:scale-[0.98]"
        >
          <Plus className="size-4" /> New question
        </button>
        <div className="mt-3 flex items-center gap-2 rounded-xl bg-[#F8F8F9] px-3 py-2 text-[12px] text-[#A999C4]" style={{ border: "1px solid #EEEDF2" }}>
          <Search className="size-3.5" /> Search
        </div>
      </div>
      <nav className="mt-4 flex flex-col gap-0.5 px-3">
        {NAV_ITEMS.filter((n) => !["chat", "overview", "insights"].includes(n.id)).map((item) => {
          const Icon = RAIL_ICONS[item.id];
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] text-[#45414F] transition-colors hover:bg-[#EAE7F0] active:scale-[0.99]"
            >
              <Icon className="size-4 text-[#6E6A78]" strokeWidth={1.75} />
              {item.label}
            </button>
          );
        })}
        <button className="flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] text-[#45414F] transition-colors hover:bg-[#EAE7F0]">
          <Clock className="size-4 text-[#6E6A78]" strokeWidth={1.75} /> History
        </button>
      </nav>
      <div className="mt-4 flex-1 overflow-y-auto px-3">
        {history.length > 0 && (
          <>
            <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-[#B4AFC2]">Recent</p>
            {history.slice(0, 8).map((q, i) => (
              <button
                key={i}
                onClick={() => onPick(q)}
                className="block w-full truncate rounded-lg px-3 py-1.5 text-left text-[12px] text-[#45414F] hover:bg-[#EAE7F0]"
              >
                {q}
              </button>
            ))}
          </>
        )}
      </div>
      <div className="p-3">
        <button
          onClick={() => setAuthModalOpen(true)}
          className="flex w-full items-center gap-2.5 rounded-xl bg-white p-2 transition-shadow hover:shadow-md"
        >
          <AvatarCircle name={currentUser?.name || "Srkia Ash"} className="size-7 text-[10px]" />
          <span className="flex-1 truncate text-left text-[12px] font-medium text-[#0A0A0A]">{currentUser?.name || "Srkia Ash"}</span>
          <LogOut className="size-3.5 text-[#A999C4]" />
        </button>
      </div>
    </aside>
  );
}

/** Small caption marking illustrative sample content (demo vs mixed with real uploads). */
export function SampleDataTag({ demo }: { demo: boolean }) {
  return (
    <span className="pointer-events-none absolute bottom-3 right-5 z-20 text-[10px] fam-mut">
      {demo ? "Sample data - illustrative" : "Some metrics illustrative"}
    </span>
  );
}
